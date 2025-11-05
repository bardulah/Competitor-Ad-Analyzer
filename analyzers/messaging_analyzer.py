"""Messaging and text analysis for advertisements."""

import logging
from typing import Dict, Any, List, Optional
from collections import Counter
import re
from anthropic import Anthropic

from config import ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)


class MessagingAnalyzer:
    """Analyzes messaging, copy, and text elements of ads."""

    def __init__(self):
        """Initialize the messaging analyzer."""
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)

        # Common power words in advertising
        self.power_words = [
            'free', 'new', 'guaranteed', 'proven', 'save', 'easy', 'limited',
            'exclusive', 'you', 'now', 'today', 'instant', 'discover', 'unlock',
            'secret', 'best', 'amazing', 'incredible', 'breakthrough', 'revolutionary'
        ]

        # Common CTA patterns
        self.cta_patterns = [
            'buy', 'shop', 'get', 'learn', 'discover', 'try', 'start',
            'sign up', 'subscribe', 'download', 'claim', 'join', 'order'
        ]

    def analyze_ad_copy(self, ad_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the copy/messaging of a single ad.

        Args:
            ad_data: Dictionary containing ad information

        Returns:
            Dictionary containing messaging analysis
        """
        logger.info(f"Analyzing messaging for ad: {ad_data.get('id', 'unknown')}")

        headline = ad_data.get('headline', '')
        body_text = ad_data.get('body_text', '')
        cta = ad_data.get('cta', '')

        combined_text = f"{headline}\n{body_text}\n{cta}"

        if not combined_text.strip():
            return {
                'error': 'No text content to analyze',
                'ad_id': ad_data.get('id')
            }

        # Basic text metrics
        basic_metrics = self._calculate_text_metrics(combined_text)

        # Identify power words
        power_words_used = self._find_power_words(combined_text)

        # Analyze CTA
        cta_analysis = self._analyze_cta(cta)

        # AI-powered deep analysis
        deep_analysis = self._deep_messaging_analysis(headline, body_text, cta)

        return {
            'ad_id': ad_data.get('id'),
            'basic_metrics': basic_metrics,
            'power_words_used': power_words_used,
            'cta_analysis': cta_analysis,
            'deep_analysis': deep_analysis
        }

    def analyze_multiple_ads(self, ads_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze messaging across multiple ads to find patterns.

        Args:
            ads_data: List of ad data dictionaries

        Returns:
            Dictionary containing pattern analysis
        """
        logger.info(f"Analyzing messaging patterns across {len(ads_data)} ads")

        all_headlines = []
        all_body_texts = []
        all_ctas = []
        all_power_words = []

        for ad in ads_data:
            headline = ad.get('headline', '')
            body_text = ad.get('body_text', '')
            cta = ad.get('cta', '')

            if headline:
                all_headlines.append(headline)
            if body_text:
                all_body_texts.append(body_text)
            if cta:
                all_ctas.append(cta)

            combined = f"{headline} {body_text} {cta}".lower()
            all_power_words.extend(self._find_power_words(combined))

        # Pattern analysis
        patterns = {
            'total_ads_analyzed': len(ads_data),
            'most_common_power_words': Counter(all_power_words).most_common(10),
            'cta_patterns': self._analyze_cta_patterns(all_ctas),
            'headline_patterns': self._analyze_text_patterns(all_headlines, 'headlines'),
            'messaging_themes': self._identify_themes(all_body_texts)
        }

        return patterns

    def _calculate_text_metrics(self, text: str) -> Dict[str, Any]:
        """Calculate basic text metrics.

        Args:
            text: Text to analyze

        Returns:
            Dictionary of metrics
        """
        words = text.split()
        sentences = re.split(r'[.!?]+', text)

        return {
            'character_count': len(text),
            'word_count': len(words),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'avg_word_length': sum(len(w) for w in words) / len(words) if words else 0,
            'readability_score': self._calculate_readability(text)
        }

    def _calculate_readability(self, text: str) -> str:
        """Simple readability assessment.

        Args:
            text: Text to assess

        Returns:
            Readability level string
        """
        words = text.split()
        if not words:
            return "N/A"

        avg_word_length = sum(len(w) for w in words) / len(words)

        if avg_word_length < 4:
            return "Very Easy"
        elif avg_word_length < 5:
            return "Easy"
        elif avg_word_length < 6:
            return "Moderate"
        else:
            return "Complex"

    def _find_power_words(self, text: str) -> List[str]:
        """Find power words in text.

        Args:
            text: Text to search

        Returns:
            List of power words found
        """
        text_lower = text.lower()
        found_words = []

        for word in self.power_words:
            if word in text_lower:
                found_words.append(word)

        return found_words

    def _analyze_cta(self, cta: str) -> Dict[str, Any]:
        """Analyze call-to-action.

        Args:
            cta: CTA text

        Returns:
            CTA analysis dictionary
        """
        if not cta:
            return {
                'present': False,
                'type': None,
                'urgency': False
            }

        cta_lower = cta.lower()

        # Identify CTA type
        cta_type = 'custom'
        for pattern in self.cta_patterns:
            if pattern in cta_lower:
                cta_type = pattern
                break

        # Check for urgency indicators
        urgency_words = ['now', 'today', 'limited', 'hurry', 'last chance', 'ending soon']
        has_urgency = any(word in cta_lower for word in urgency_words)

        return {
            'present': True,
            'text': cta,
            'type': cta_type,
            'urgency': has_urgency,
            'length': len(cta.split())
        }

    def _analyze_cta_patterns(self, ctas: List[str]) -> Dict[str, Any]:
        """Analyze patterns in CTAs.

        Args:
            ctas: List of CTA texts

        Returns:
            Pattern analysis
        """
        if not ctas:
            return {}

        cta_types = []
        urgency_count = 0

        for cta in ctas:
            analysis = self._analyze_cta(cta)
            if analysis['present']:
                cta_types.append(analysis['type'])
                if analysis['urgency']:
                    urgency_count += 1

        return {
            'total_ctas': len(ctas),
            'most_common_types': Counter(cta_types).most_common(5),
            'urgency_percentage': (urgency_count / len(ctas)) * 100 if ctas else 0
        }

    def _analyze_text_patterns(self, texts: List[str], label: str) -> Dict[str, Any]:
        """Analyze patterns in a collection of texts.

        Args:
            texts: List of texts to analyze
            label: Label for the text type

        Returns:
            Pattern analysis
        """
        if not texts:
            return {}

        avg_length = sum(len(t.split()) for t in texts) / len(texts)

        # Find common phrases (simple implementation)
        all_words = ' '.join(texts).lower().split()
        common_words = Counter(all_words).most_common(10)

        return {
            'total_count': len(texts),
            'avg_word_count': avg_length,
            'common_words': common_words
        }

    def _identify_themes(self, texts: List[str]) -> List[str]:
        """Identify common themes in text collection.

        Args:
            texts: List of texts to analyze

        Returns:
            List of identified themes
        """
        if not texts:
            return []

        combined_text = ' '.join(texts)

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": f"""Analyze these advertisement texts and identify the top 5-7 recurring themes or messaging strategies:

{combined_text[:5000]}  # Limit text length

List only the theme names, one per line."""
                }]
            )

            themes = response.content[0].text.strip().split('\n')
            return [theme.strip('- ').strip() for theme in themes if theme.strip()]

        except Exception as e:
            logger.error(f"Error identifying themes: {e}")
            return []

    def _deep_messaging_analysis(self, headline: str, body_text: str, cta: str) -> str:
        """Perform AI-powered deep analysis of messaging.

        Args:
            headline: Ad headline
            body_text: Ad body text
            cta: Call to action

        Returns:
            Analysis text
        """
        try:
            prompt = f"""Analyze this advertisement copy:

HEADLINE: {headline}
BODY: {body_text}
CTA: {cta}

Provide a concise analysis covering:
1. Emotional appeal and tone
2. Value proposition clarity
3. Target audience signals
4. Persuasion techniques used
5. Strengths and weaknesses
6. Recommendations for improvement

Keep the analysis focused and actionable."""

            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Error in deep messaging analysis: {e}")
            return f"Error performing analysis: {str(e)}"
