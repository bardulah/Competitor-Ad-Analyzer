"""Pattern detection across advertisement campaigns."""

import logging
from typing import Dict, Any, List, Optional
from collections import Counter, defaultdict
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class PatternDetector:
    """Detects patterns and trends across multiple advertisements."""

    def __init__(self):
        """Initialize the pattern detector."""
        pass

    def detect_patterns(self, ads_data: List[Dict[str, Any]],
                       visual_analyses: Optional[List[Dict[str, Any]]] = None,
                       messaging_analyses: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Detect patterns across ads using all available data.

        Args:
            ads_data: List of ad data dictionaries
            visual_analyses: Optional list of visual analysis results
            messaging_analyses: Optional list of messaging analysis results

        Returns:
            Dictionary containing detected patterns
        """
        logger.info(f"Detecting patterns across {len(ads_data)} ads")

        patterns = {
            'metadata_patterns': self._analyze_metadata_patterns(ads_data),
            'temporal_patterns': self._analyze_temporal_patterns(ads_data),
            'engagement_patterns': self._analyze_engagement_patterns(ads_data),
            'summary': {}
        }

        if visual_analyses:
            patterns['visual_patterns'] = self._extract_visual_patterns(visual_analyses)

        if messaging_analyses:
            patterns['messaging_patterns'] = self._extract_messaging_patterns(messaging_analyses)

        # Generate summary insights
        patterns['summary'] = self._generate_pattern_summary(patterns)

        return patterns

    def _analyze_metadata_patterns(self, ads_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in ad metadata.

        Args:
            ads_data: List of ad data

        Returns:
            Metadata patterns
        """
        platforms = []
        advertisers = []
        has_video = 0
        has_image = 0

        for ad in ads_data:
            if ad.get('platform'):
                platforms.append(ad['platform'])
            if ad.get('advertiser'):
                advertisers.append(ad['advertiser'])
            if ad.get('video_url'):
                has_video += 1
            if ad.get('image_url'):
                has_image += 1

        return {
            'platform_distribution': dict(Counter(platforms)),
            'top_advertisers': Counter(advertisers).most_common(10),
            'media_types': {
                'video_ads': has_video,
                'image_ads': has_image,
                'video_percentage': (has_video / len(ads_data)) * 100 if ads_data else 0
            }
        }

    def _analyze_temporal_patterns(self, ads_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze temporal patterns in ads.

        Args:
            ads_data: List of ad data

        Returns:
            Temporal patterns
        """
        start_dates = []
        durations = []

        for ad in ads_data:
            start_date = ad.get('start_date')
            end_date = ad.get('end_date')

            if start_date:
                start_dates.append(start_date)

            # Calculate duration if both dates exist
            if start_date and end_date:
                try:
                    # Simple duration estimation (would need proper date parsing)
                    durations.append(1)  # Placeholder
                except:
                    pass

        return {
            'total_ads_with_dates': len(start_dates),
            'date_range': {
                'earliest': min(start_dates) if start_dates else None,
                'latest': max(start_dates) if start_dates else None
            },
            'avg_duration_days': sum(durations) / len(durations) if durations else None
        }

    def _analyze_engagement_patterns(self, ads_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze engagement-related patterns.

        Args:
            ads_data: List of ad data

        Returns:
            Engagement patterns
        """
        ads_with_impressions = []
        ads_with_spend = []

        for ad in ads_data:
            if ad.get('impressions'):
                ads_with_impressions.append(ad)
            if ad.get('spend_estimate'):
                ads_with_spend.append(ad)

        patterns = {
            'ads_with_engagement_data': len(ads_with_impressions),
            'ads_with_spend_data': len(ads_with_spend)
        }

        # Top performing ads (if data available)
        if ads_with_impressions:
            sorted_ads = sorted(
                ads_with_impressions,
                key=lambda x: x.get('impressions', 0),
                reverse=True
            )
            patterns['top_performing_ads'] = [
                {
                    'id': ad.get('id'),
                    'advertiser': ad.get('advertiser'),
                    'impressions': ad.get('impressions')
                }
                for ad in sorted_ads[:5]
            ]

        return patterns

    def _extract_visual_patterns(self, visual_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract patterns from visual analyses.

        Args:
            visual_analyses: List of visual analysis results

        Returns:
            Visual patterns
        """
        patterns = {
            'total_analyzed': len(visual_analyses),
            'common_themes': [],
            'design_trends': []
        }

        # Extract keywords from analyses
        all_text = ' '.join([
            str(analysis.get('raw_analysis', ''))
            for analysis in visual_analyses
        ])

        # Simple keyword extraction (could be enhanced)
        color_keywords = ['blue', 'red', 'green', 'yellow', 'white', 'black', 'orange', 'purple']
        style_keywords = ['minimalist', 'modern', 'bold', 'clean', 'vibrant', 'professional']

        found_colors = [color for color in color_keywords if color in all_text.lower()]
        found_styles = [style for style in style_keywords if style in all_text.lower()]

        patterns['common_colors'] = Counter(found_colors).most_common(5)
        patterns['common_styles'] = Counter(found_styles).most_common(5)

        return patterns

    def _extract_messaging_patterns(self, messaging_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract patterns from messaging analyses.

        Args:
            messaging_analyses: List of messaging analysis results

        Returns:
            Messaging patterns
        """
        all_power_words = []
        all_cta_types = []
        urgency_count = 0

        for analysis in messaging_analyses:
            # Extract power words
            power_words = analysis.get('power_words_used', [])
            all_power_words.extend(power_words)

            # Extract CTA info
            cta_analysis = analysis.get('cta_analysis', {})
            if cta_analysis.get('type'):
                all_cta_types.append(cta_analysis['type'])
            if cta_analysis.get('urgency'):
                urgency_count += 1

        return {
            'total_analyzed': len(messaging_analyses),
            'most_common_power_words': Counter(all_power_words).most_common(10),
            'most_common_cta_types': Counter(all_cta_types).most_common(5),
            'urgency_usage_rate': (urgency_count / len(messaging_analyses)) * 100 if messaging_analyses else 0
        }

    def _generate_pattern_summary(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of all detected patterns.

        Args:
            patterns: All detected patterns

        Returns:
            Summary dictionary
        """
        summary = {
            'analysis_date': datetime.now().isoformat(),
            'key_findings': []
        }

        # Extract key findings from various patterns
        metadata = patterns.get('metadata_patterns', {})
        if metadata:
            summary['key_findings'].append(
                f"Analyzed ads across {len(metadata.get('platform_distribution', {}))} platforms"
            )

        visual = patterns.get('visual_patterns', {})
        if visual and visual.get('common_colors'):
            top_color = visual['common_colors'][0][0] if visual['common_colors'] else None
            if top_color:
                summary['key_findings'].append(
                    f"Most common color scheme: {top_color}"
                )

        messaging = patterns.get('messaging_patterns', {})
        if messaging and messaging.get('most_common_power_words'):
            top_word = messaging['most_common_power_words'][0][0] if messaging['most_common_power_words'] else None
            if top_word:
                summary['key_findings'].append(
                    f"Most used power word: '{top_word}'"
                )

        engagement = patterns.get('engagement_patterns', {})
        if engagement.get('top_performing_ads'):
            summary['key_findings'].append(
                f"Identified {len(engagement['top_performing_ads'])} top-performing ads"
            )

        return summary

    def export_patterns(self, patterns: Dict[str, Any], output_path: str):
        """Export patterns to JSON file.

        Args:
            patterns: Patterns dictionary
            output_path: Path to output file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(patterns, f, indent=2, ensure_ascii=False)

        logger.info(f"Patterns exported to {output_path}")
