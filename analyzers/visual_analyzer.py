"""AI-powered visual analysis of advertisement images."""

import logging
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional
from anthropic import Anthropic

from config import ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)


class VisualAnalyzer:
    """Analyzes visual elements of ads using Claude's vision capabilities."""

    def __init__(self):
        """Initialize the visual analyzer."""
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)

    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Analyze a single ad image.

        Args:
            image_path: Path to the ad screenshot

        Returns:
            Dictionary containing visual analysis
        """
        logger.info(f"Analyzing image: {image_path}")

        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = base64.standard_b64encode(f.read()).decode('utf-8')

            # Determine media type
            media_type = self._get_media_type(image_path)

            # Analyze with Claude
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
                            "text": self._get_analysis_prompt()
                        }
                    ]
                }]
            )

            # Parse response
            analysis_text = response.content[0].text

            # Structure the analysis
            analysis = self._parse_analysis(analysis_text)
            analysis['raw_analysis'] = analysis_text

            logger.info("Image analysis completed successfully")
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return {
                'error': str(e),
                'image_path': image_path
            }

    def analyze_multiple(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """Analyze multiple ad images.

        Args:
            image_paths: List of paths to ad screenshots

        Returns:
            List of analysis dictionaries
        """
        analyses = []

        for image_path in image_paths:
            analysis = self.analyze_image(image_path)
            analyses.append(analysis)

        return analyses

    def compare_ads(self, image_paths: List[str]) -> Dict[str, Any]:
        """Compare multiple ads to identify common patterns.

        Args:
            image_paths: List of paths to ad screenshots (max 5)

        Returns:
            Dictionary containing comparative analysis
        """
        if len(image_paths) > 5:
            logger.warning("Too many images for comparison. Using first 5.")
            image_paths = image_paths[:5]

        logger.info(f"Comparing {len(image_paths)} ads")

        try:
            # Prepare image content for multi-image analysis
            content = []

            for image_path in image_paths:
                with open(image_path, 'rb') as f:
                    image_data = base64.standard_b64encode(f.read()).decode('utf-8')

                media_type = self._get_media_type(image_path)

                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_data
                    }
                })

            # Add comparison prompt
            content.append({
                "type": "text",
                "text": self._get_comparison_prompt()
            })

            # Analyze with Claude
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=3000,
                messages=[{
                    "role": "user",
                    "content": content
                }]
            )

            comparison_text = response.content[0].text

            logger.info("Comparison analysis completed")

            return {
                'num_ads_compared': len(image_paths),
                'analysis': comparison_text,
                'image_paths': image_paths
            }

        except Exception as e:
            logger.error(f"Error comparing ads: {e}")
            return {
                'error': str(e),
                'image_paths': image_paths
            }

    def _get_media_type(self, image_path: str) -> str:
        """Determine media type from file extension.

        Args:
            image_path: Path to image file

        Returns:
            Media type string
        """
        extension = Path(image_path).suffix.lower()
        media_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        return media_types.get(extension, 'image/png')

    def _get_analysis_prompt(self) -> str:
        """Get the prompt for single ad analysis.

        Returns:
            Analysis prompt string
        """
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

    def _get_comparison_prompt(self) -> str:
        """Get the prompt for comparing multiple ads.

        Returns:
            Comparison prompt string
        """
        return """Compare these advertisements and identify patterns across them:

1. COMMON VISUAL PATTERNS
   - Shared design elements
   - Similar color schemes or palettes
   - Typography patterns
   - Layout similarities

2. MESSAGING PATTERNS
   - Common themes or value propositions
   - Similar call-to-action approaches
   - Emotional appeals used

3. SUCCESS INDICATORS
   - What elements appear in multiple ads (suggesting they work)?
   - Professional production quality patterns
   - Target audience alignment

4. DIFFERENTIATION OPPORTUNITIES
   - Gaps in the current approaches
   - Oversaturated elements to avoid
   - Unique angles not being exploited

5. ACTIONABLE RECOMMENDATIONS
   - Top 5 elements to adopt from these ads
   - Top 3 things to do differently
   - Suggested creative direction for competing ads

Provide specific, actionable insights for creating competitive advertisements."""

    def _parse_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """Parse the analysis text into structured data.

        Args:
            analysis_text: Raw analysis text from Claude

        Returns:
            Structured analysis dictionary
        """
        # This is a simple parser - could be enhanced with more sophisticated parsing
        analysis = {
            'visual_composition': '',
            'imagery': '',
            'messaging': '',
            'design_patterns': '',
            'effectiveness': '',
            'insights': ''
        }

        # Try to extract sections
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

        return analysis
