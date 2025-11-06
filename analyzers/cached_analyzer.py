"""Cached analyzer with multi-tier model usage."""

import logging
import hashlib
import base64
from typing import Dict, Any, Optional
from anthropic import Anthropic

from config import ANTHROPIC_API_KEY
from database import CacheRepository, CostRepository
import uuid

logger = logging.getLogger(__name__)


# Model pricing per 1M tokens (input / output)
MODEL_PRICING = {
    'claude-3-haiku-20240307': (0.25, 1.25),
    'claude-3-5-sonnet-20241022': (3.00, 15.00),
    'claude-opus-3-20240229': (15.00, 75.00),
}


class CachedVisualAnalyzer:
    """Visual analyzer with caching and multi-tier model usage."""

    def __init__(self, session_id: Optional[str] = None):
        """Initialize the cached visual analyzer."""
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.session_id = session_id or str(uuid.uuid4())

    def analyze_image(self, image_path: str, use_cache: bool = True,
                     quick_filter: bool = True) -> Dict[str, Any]:
        """Analyze a single ad image with caching and smart model selection.

        Args:
            image_path: Path to the ad screenshot
            use_cache: Whether to use cached results
            quick_filter: If True, use Haiku first to filter low-quality ads

        Returns:
            Dictionary containing visual analysis
        """
        logger.info(f"Analyzing image: {image_path}")

        # Calculate content hash for caching
        content_hash = self._calculate_file_hash(image_path)

        # Check cache
        if use_cache:
            with CacheRepository() as cache_repo:
                cached_result = cache_repo.get_cached_analysis(content_hash, 'visual')
                if cached_result:
                    logger.info(f"Using cached analysis for {image_path}")
                    return cached_result

        # Read and encode image
        with open(image_path, 'rb') as f:
            image_data = base64.standard_b64encode(f.read()).decode('utf-8')

        media_type = self._get_media_type(image_path)

        # Step 1: Quick filter with Haiku (if enabled)
        if quick_filter:
            quality_score = self._quick_quality_check(image_data, media_type)

            if quality_score < 5.0:
                logger.info(f"Low quality ad detected (score: {quality_score}), skipping deep analysis")
                result = {
                    'quality_score': quality_score,
                    'analysis_type': 'quick_filter',
                    'model_used': 'claude-3-haiku-20240307',
                    'skip_reason': 'low_quality',
                    'image_path': image_path
                }

                # Cache the result
                if use_cache:
                    self._cache_result(content_hash, result, 'visual', 'image',
                                      'claude-3-haiku-20240307')

                return result

        # Step 2: Deep analysis with Sonnet
        result = self._deep_analysis(image_data, media_type, image_path)

        # Cache the result
        if use_cache:
            self._cache_result(content_hash, result, 'visual', 'image',
                              result.get('model_used', 'claude-3-5-sonnet-20241022'))

        return result

    def _quick_quality_check(self, image_data: str, media_type: str) -> float:
        """Quick quality check using Haiku model.

        Args:
            image_data: Base64 encoded image
            media_type: Image media type

        Returns:
            Quality score (0-10)
        """
        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=256,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": """Rate this advertisement's visual quality on a scale of 0-10, considering:
- Professional production value
- Visual clarity and appeal
- Effective use of design elements
- Brand presence

Respond with ONLY a number between 0-10. No explanation."""
                        }
                    ]
                }]
            )

            # Track cost
            self._track_cost(
                'quick_quality_check',
                'claude-3-haiku-20240307',
                response.usage.input_tokens,
                response.usage.output_tokens
            )

            # Parse score
            score_text = response.content[0].text.strip()
            try:
                score = float(score_text)
                return max(0.0, min(10.0, score))
            except ValueError:
                logger.warning(f"Could not parse quality score: {score_text}")
                return 5.0  # Default to medium quality

        except Exception as e:
            logger.error(f"Error in quick quality check: {e}")
            return 5.0  # Default to medium quality on error

    def _deep_analysis(self, image_data: str, media_type: str, image_path: str) -> Dict[str, Any]:
        """Perform deep analysis using Sonnet model.

        Args:
            image_data: Base64 encoded image
            media_type: Image media type
            image_path: Path to image file

        Returns:
            Comprehensive analysis dictionary
        """
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": self._get_deep_analysis_prompt()
                        }
                    ]
                }]
            )

            # Track cost
            self._track_cost(
                'deep_visual_analysis',
                'claude-3-5-sonnet-20241022',
                response.usage.input_tokens,
                response.usage.output_tokens
            )

            analysis_text = response.content[0].text

            # Parse and structure the analysis
            analysis = self._parse_analysis(analysis_text)
            analysis['raw_analysis'] = analysis_text
            analysis['model_used'] = 'claude-3-5-sonnet-20241022'
            analysis['analysis_type'] = 'deep'
            analysis['image_path'] = image_path

            logger.info("Deep image analysis completed successfully")
            return analysis

        except Exception as e:
            logger.error(f"Error in deep analysis: {e}")
            return {
                'error': str(e),
                'image_path': image_path,
                'model_used': 'claude-3-5-sonnet-20241022'
            }

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file for caching.

        Args:
            file_path: Path to file

        Returns:
            MD5 hash string
        """
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            # Read in chunks for large files
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _cache_result(self, content_hash: str, result: Dict[str, Any],
                     analysis_type: str, content_type: str, model_used: str):
        """Save result to cache.

        Args:
            content_hash: Hash of content
            result: Analysis result
            analysis_type: Type of analysis
            content_type: Type of content
            model_used: Model used for analysis
        """
        try:
            # Estimate cost (simplified)
            cost = result.get('cost', 0.01)  # Default small cost

            with CacheRepository() as cache_repo:
                cache_repo.save_to_cache(
                    content_hash=content_hash,
                    analysis_type=analysis_type,
                    result=result,
                    content_type=content_type,
                    model_used=model_used,
                    cost=cost
                )
        except Exception as e:
            logger.warning(f"Failed to cache result: {e}")

    def _track_cost(self, operation_type: str, model_used: str,
                   input_tokens: int, output_tokens: int):
        """Track API cost for the operation.

        Args:
            operation_type: Type of operation
            model_used: Model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        """
        try:
            # Calculate cost
            if model_used in MODEL_PRICING:
                input_cost_per_m, output_cost_per_m = MODEL_PRICING[model_used]
                cost = (input_tokens / 1_000_000 * input_cost_per_m +
                       output_tokens / 1_000_000 * output_cost_per_m)

                with CostRepository() as cost_repo:
                    cost_repo.track_cost(
                        operation_type=operation_type,
                        model_used=model_used,
                        cost_usd=cost,
                        session_id=self.session_id,
                        tokens_used=input_tokens + output_tokens
                    )

                logger.debug(f"Tracked cost: ${cost:.4f} for {operation_type}")
        except Exception as e:
            logger.warning(f"Failed to track cost: {e}")

    def _get_media_type(self, image_path: str) -> str:
        """Determine media type from file extension."""
        from pathlib import Path
        extension = Path(image_path).suffix.lower()
        media_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        return media_types.get(extension, 'image/png')

    def _get_deep_analysis_prompt(self) -> str:
        """Get the prompt for deep analysis."""
        return """Analyze this advertisement image in detail. Provide a comprehensive breakdown including:

1. VISUAL COMPOSITION
   - Layout and design structure
   - Color palette and color psychology
   - Typography choices and hierarchy
   - Use of whitespace
   - Visual balance and focal points

2. IMAGERY & GRAPHICS
   - Type of imagery (photography, illustration, 3D, etc.)
   - Subject matter and mood
   - Image quality and production value
   - Brand elements and logo placement

3. MESSAGING
   - Headline and key copy visible
   - Call-to-action (CTA) placement and wording
   - Value proposition clarity
   - Emotional appeal

4. DESIGN PATTERNS
   - Common design patterns or templates used
   - Industry trends evident in the design
   - Target audience signals

5. EFFECTIVENESS FACTORS
   - What makes this ad stand out?
   - Potential strengths for engagement
   - Areas that could be improved
   - Overall professional assessment (1-10 rating)

6. COMPETITIVE INSIGHTS
   - What elements could be adapted for similar campaigns?
   - Unique selling points in the visual presentation
   - Recommendations for competing ads

Please be specific and actionable in your analysis."""

    def _parse_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """Parse the analysis text into structured data."""
        analysis = {
            'visual_composition': '',
            'imagery': '',
            'messaging': '',
            'design_patterns': '',
            'effectiveness': '',
            'insights': '',
            'quality_score': 7.0  # Default score
        }

        sections = {
            'VISUAL COMPOSITION': 'visual_composition',
            'IMAGERY & GRAPHICS': 'imagery',
            'MESSAGING': 'messaging',
            'DESIGN PATTERNS': 'design_patterns',
            'EFFECTIVENESS FACTORS': 'effectiveness',
            'COMPETITIVE INSIGHTS': 'insights'
        }

        current_section = None
        current_text = []

        for line in analysis_text.split('\n'):
            # Check if line is a section header
            is_header = False
            for header, key in sections.items():
                if header in line.upper():
                    # Save previous section
                    if current_section:
                        analysis[current_section] = '\n'.join(current_text).strip()

                    # Start new section
                    current_section = key
                    current_text = []
                    is_header = True
                    break

            if not is_header and current_section:
                current_text.append(line)

        # Save last section
        if current_section:
            analysis[current_section] = '\n'.join(current_text).strip()

        # Try to extract quality score
        import re
        score_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:/\s*10|out of 10)', analysis_text, re.IGNORECASE)
        if score_match:
            try:
                analysis['quality_score'] = float(score_match.group(1))
            except:
                pass

        return analysis


class CachedMessagingAnalyzer:
    """Messaging analyzer with caching and smart model selection."""

    def __init__(self, session_id: Optional[str] = None):
        """Initialize the cached messaging analyzer."""
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.session_id = session_id or str(uuid.uuid4())

    def analyze_text(self, text: str, use_cache: bool = True) -> Dict[str, Any]:
        """Analyze ad copy with caching.

        Args:
            text: Text to analyze
            use_cache: Whether to use cached results

        Returns:
            Analysis dictionary
        """
        if not text or not text.strip():
            return {'error': 'No text to analyze'}

        # Calculate content hash
        content_hash = hashlib.md5(text.encode('utf-8')).hexdigest()

        # Check cache
        if use_cache:
            with CacheRepository() as cache_repo:
                cached_result = cache_repo.get_cached_analysis(content_hash, 'messaging')
                if cached_result:
                    logger.info("Using cached messaging analysis")
                    return cached_result

        # Perform analysis
        result = self._analyze_with_sonnet(text)

        # Cache result
        if use_cache:
            try:
                with CacheRepository() as cache_repo:
                    cache_repo.save_to_cache(
                        content_hash=content_hash,
                        analysis_type='messaging',
                        result=result,
                        content_type='text',
                        model_used='claude-3-5-sonnet-20241022',
                        cost=result.get('cost', 0.005)
                    )
            except Exception as e:
                logger.warning(f"Failed to cache result: {e}")

        return result

    def _analyze_with_sonnet(self, text: str) -> Dict[str, Any]:
        """Analyze text using Sonnet model."""
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": f"""Analyze this advertisement copy:

{text}

Provide a concise analysis covering:
1. Emotional appeal and tone
2. Value proposition clarity
3. Target audience signals
4. Persuasion techniques used
5. Strengths and weaknesses
6. Quality score (0-10)

Keep the analysis focused and actionable."""
                }]
            )

            # Track cost
            self._track_cost(
                'messaging_analysis',
                'claude-3-5-sonnet-20241022',
                response.usage.input_tokens,
                response.usage.output_tokens
            )

            analysis_text = response.content[0].text

            return {
                'analysis': analysis_text,
                'model_used': 'claude-3-5-sonnet-20241022',
                'text_analyzed': text[:200]  # Store snippet
            }

        except Exception as e:
            logger.error(f"Error in messaging analysis: {e}")
            return {'error': str(e)}

    def _track_cost(self, operation_type: str, model_used: str,
                   input_tokens: int, output_tokens: int):
        """Track API cost."""
        try:
            if model_used in MODEL_PRICING:
                input_cost_per_m, output_cost_per_m = MODEL_PRICING[model_used]
                cost = (input_tokens / 1_000_000 * input_cost_per_m +
                       output_tokens / 1_000_000 * output_cost_per_m)

                with CostRepository() as cost_repo:
                    cost_repo.track_cost(
                        operation_type=operation_type,
                        model_used=model_used,
                        cost_usd=cost,
                        session_id=self.session_id,
                        tokens_used=input_tokens + output_tokens
                    )
        except Exception as e:
            logger.warning(f"Failed to track cost: {e}")
