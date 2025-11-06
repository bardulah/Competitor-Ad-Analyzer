"""Trend analysis for tracking creative evolution over time."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from sqlalchemy import func

from database import AdRepository, AnalysisRepository, get_session
from database.models import Advertisement, VisualAnalysis, MessagingAnalysis

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """Analyzes trends in competitor advertising over time."""

    def __init__(self):
        """Initialize trend analyzer."""
        pass

    def analyze_advertiser_trends(self, advertiser: str, months: int = 6) -> Dict[str, Any]:
        """Analyze creative trends for a specific advertiser over time.

        Args:
            advertiser: Advertiser name
            months: Number of months to analyze

        Returns:
            Trend analysis dictionary
        """
        logger.info(f"Analyzing trends for {advertiser} over {months} months")

        with AdRepository() as ad_repo:
            # Get ads from the time period
            cutoff_date = datetime.utcnow() - timedelta(days=months * 30)

            session = ad_repo.session
            ads = session.query(Advertisement)\
                .filter(Advertisement.advertiser == advertiser)\
                .filter(Advertisement.scraped_at >= cutoff_date)\
                .order_by(Advertisement.scraped_at)\
                .all()

            if not ads:
                return {'error': f'No ads found for {advertiser} in the last {months} months'}

            logger.info(f"Found {len(ads)} ads for analysis")

            # Group ads by month
            ads_by_month = self._group_ads_by_month(ads)

            # Analyze different dimensions
            trends = {
                'advertiser': advertiser,
                'period_months': months,
                'total_ads': len(ads),
                'ads_by_month': self._count_by_month(ads_by_month),
                'messaging_trends': self._analyze_messaging_trends(ads_by_month),
                'visual_trends': self._analyze_visual_trends(ads_by_month),
                'cta_trends': self._analyze_cta_trends(ads_by_month),
                'seasonal_patterns': self._detect_seasonal_patterns(ads_by_month),
                'strategy_shifts': self._detect_strategy_shifts(ads_by_month),
                'insights': []
            }

            # Generate insights
            trends['insights'] = self._generate_trend_insights(trends)

            return trends

    def compare_competitor_trends(self, competitors: List[str], months: int = 6) -> Dict[str, Any]:
        """Compare trends across multiple competitors.

        Args:
            competitors: List of competitor names
            months: Number of months to analyze

        Returns:
            Comparative trend analysis
        """
        logger.info(f"Comparing trends for {len(competitors)} competitors")

        competitor_trends = {}

        for competitor in competitors:
            trends = self.analyze_advertiser_trends(competitor, months)
            competitor_trends[competitor] = trends

        # Perform cross-competitor analysis
        comparison = {
            'competitors': competitors,
            'period_months': months,
            'individual_trends': competitor_trends,
            'market_insights': self._analyze_market_trends(competitor_trends),
            'competitive_positioning': self._analyze_competitive_positioning(competitor_trends),
            'opportunities': self._identify_market_opportunities(competitor_trends)
        }

        return comparison

    def _group_ads_by_month(self, ads: List[Advertisement]) -> Dict[str, List[Advertisement]]:
        """Group ads by month.

        Args:
            ads: List of advertisements

        Returns:
            Dictionary mapping month strings to ad lists
        """
        grouped = defaultdict(list)

        for ad in ads:
            if ad.scraped_at:
                month_key = ad.scraped_at.strftime('%Y-%m')
                grouped[month_key].append(ad)

        return dict(grouped)

    def _count_by_month(self, ads_by_month: Dict[str, List]) -> Dict[str, int]:
        """Count ads by month.

        Args:
            ads_by_month: Grouped ads

        Returns:
            Count dictionary
        """
        return {month: len(ads) for month, ads in sorted(ads_by_month.items())}

    def _analyze_messaging_trends(self, ads_by_month: Dict[str, List[Advertisement]]) -> Dict[str, Any]:
        """Analyze how messaging has evolved over time.

        Args:
            ads_by_month: Ads grouped by month

        Returns:
            Messaging trend analysis
        """
        trends = {
            'power_words_by_month': {},
            'cta_types_by_month': {},
            'average_length_by_month': {},
            'evolution': []
        }

        for month, ads in sorted(ads_by_month.items()):
            # Analyze power words
            all_text = ' '.join([
                f"{ad.headline or ''} {ad.body_text or ''}".lower()
                for ad in ads
            ])

            power_words = self._extract_power_words(all_text)
            trends['power_words_by_month'][month] = power_words

            # Analyze CTAs
            ctas = [ad.cta for ad in ads if ad.cta]
            cta_types = Counter([self._categorize_cta(cta) for cta in ctas])
            trends['cta_types_by_month'][month] = dict(cta_types)

            # Average text length
            text_lengths = [
                len((ad.headline or '') + (ad.body_text or ''))
                for ad in ads
            ]
            avg_length = sum(text_lengths) / len(text_lengths) if text_lengths else 0
            trends['average_length_by_month'][month] = int(avg_length)

        # Detect evolution patterns
        months = sorted(ads_by_month.keys())
        if len(months) >= 2:
            first_month = months[0]
            last_month = months[-1]

            first_words = set(trends['power_words_by_month'][first_month])
            last_words = set(trends['power_words_by_month'][last_month])

            new_words = last_words - first_words
            dropped_words = first_words - last_words

            trends['evolution'].append({
                'dimension': 'power_words',
                'new_elements': list(new_words)[:5],
                'dropped_elements': list(dropped_words)[:5]
            })

        return trends

    def _analyze_visual_trends(self, ads_by_month: Dict[str, List[Advertisement]]) -> Dict[str, Any]:
        """Analyze visual design trends over time.

        Args:
            ads_by_month: Ads grouped by month

        Returns:
            Visual trend analysis
        """
        trends = {
            'colors_by_month': {},
            'styles_by_month': {},
            'image_vs_video_by_month': {},
            'evolution': []
        }

        session = get_session()

        try:
            for month, ads in sorted(ads_by_month.items()):
                ad_ids = [ad.id for ad in ads]

                # Get visual analyses for these ads
                analyses = session.query(VisualAnalysis)\
                    .filter(VisualAnalysis.ad_id.in_(ad_ids))\
                    .all()

                # Extract color trends (simplified)
                colors = []
                for analysis in analyses:
                    if analysis.colors:
                        colors.extend(analysis.colors)

                trends['colors_by_month'][month] = Counter(colors).most_common(5)

                # Media type analysis
                image_count = sum(1 for ad in ads if ad.image_url and not ad.video_url)
                video_count = sum(1 for ad in ads if ad.video_url)

                trends['image_vs_video_by_month'][month] = {
                    'images': image_count,
                    'videos': video_count,
                    'video_percentage': (video_count / len(ads) * 100) if ads else 0
                }

        finally:
            session.close()

        return trends

    def _analyze_cta_trends(self, ads_by_month: Dict[str, List[Advertisement]]) -> Dict[str, Any]:
        """Analyze call-to-action trends.

        Args:
            ads_by_month: Ads grouped by month

        Returns:
            CTA trend analysis
        """
        trends = {
            'cta_evolution': {},
            'urgency_by_month': {}
        }

        for month, ads in sorted(ads_by_month.items()):
            ctas = [ad.cta.lower() for ad in ads if ad.cta]

            # Analyze urgency
            urgency_words = ['now', 'today', 'limited', 'hurry', 'last chance']
            urgent_ctas = sum(1 for cta in ctas if any(word in cta for word in urgency_words))

            trends['urgency_by_month'][month] = {
                'total_ctas': len(ctas),
                'urgent_ctas': urgent_ctas,
                'urgency_percentage': (urgent_ctas / len(ctas) * 100) if ctas else 0
            }

            # Most common CTA types
            cta_types = Counter([self._categorize_cta(cta) for cta in ctas])
            trends['cta_evolution'][month] = dict(cta_types.most_common(5))

        return trends

    def _detect_seasonal_patterns(self, ads_by_month: Dict[str, List[Advertisement]]) -> Dict[str, Any]:
        """Detect seasonal advertising patterns.

        Args:
            ads_by_month: Ads grouped by month

        Returns:
            Seasonal pattern analysis
        """
        patterns = {
            'volume_by_season': defaultdict(int),
            'messaging_by_season': defaultdict(list),
            'insights': []
        }

        seasons = {
            '12': 'Winter', '01': 'Winter', '02': 'Winter',
            '03': 'Spring', '04': 'Spring', '05': 'Spring',
            '06': 'Summer', '07': 'Summer', '08': 'Summer',
            '09': 'Fall', '10': 'Fall', '11': 'Fall'
        }

        for month, ads in ads_by_month.items():
            month_num = month.split('-')[1]
            season = seasons.get(month_num, 'Unknown')

            patterns['volume_by_season'][season] += len(ads)

            # Collect messaging themes
            themes = [ad.body_text[:100] for ad in ads if ad.body_text]
            patterns['messaging_by_season'][season].extend(themes)

        # Identify peak seasons
        if patterns['volume_by_season']:
            max_season = max(patterns['volume_by_season'].items(), key=lambda x: x[1])
            patterns['peak_season'] = max_season[0]
            patterns['insights'].append(f"Peak advertising season: {max_season[0]} ({max_season[1]} ads)")

        return patterns

    def _detect_strategy_shifts(self, ads_by_month: Dict[str, List[Advertisement]]) -> List[Dict[str, Any]]:
        """Detect significant strategy shifts.

        Args:
            ads_by_month: Ads grouped by month

        Returns:
            List of detected shifts
        """
        shifts = []

        months = sorted(ads_by_month.keys())

        for i in range(1, len(months)):
            prev_month = months[i-1]
            curr_month = months[i]

            prev_ads = ads_by_month[prev_month]
            curr_ads = ads_by_month[curr_month]

            # Check for volume changes
            volume_change = len(curr_ads) - len(prev_ads)
            if abs(volume_change) >= 10:  # Significant change
                shifts.append({
                    'month': curr_month,
                    'type': 'volume_change',
                    'description': f"Ad volume {'increased' if volume_change > 0 else 'decreased'} by {abs(volume_change)} ads",
                    'magnitude': abs(volume_change)
                })

            # Check for messaging changes (simplified)
            prev_words = set(self._extract_keywords(prev_ads))
            curr_words = set(self._extract_keywords(curr_ads))

            new_words = curr_words - prev_words
            if len(new_words) >= 5:
                shifts.append({
                    'month': curr_month,
                    'type': 'messaging_shift',
                    'description': f"New messaging themes emerged: {', '.join(list(new_words)[:3])}",
                    'new_themes': list(new_words)[:5]
                })

        return shifts

    def _extract_power_words(self, text: str) -> List[str]:
        """Extract power words from text."""
        power_words = [
            'free', 'new', 'guaranteed', 'proven', 'save', 'easy', 'limited',
            'exclusive', 'now', 'today', 'instant', 'discover', 'unlock'
        ]

        found_words = [word for word in power_words if word in text.lower()]
        return found_words

    def _extract_keywords(self, ads: List[Advertisement]) -> List[str]:
        """Extract keywords from ads."""
        all_text = ' '.join([
            f"{ad.headline or ''} {ad.body_text or ''}".lower()
            for ad in ads
        ])

        # Simple keyword extraction (could be enhanced with NLP)
        words = all_text.split()
        # Filter out common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
        keywords = [w for w in words if len(w) > 4 and w not in stop_words]

        return list(Counter(keywords).most_common(10))

    def _categorize_cta(self, cta: str) -> str:
        """Categorize a CTA into types."""
        cta_lower = cta.lower()

        if any(word in cta_lower for word in ['buy', 'shop', 'order', 'purchase']):
            return 'transactional'
        elif any(word in cta_lower for word in ['learn', 'discover', 'explore', 'see']):
            return 'informational'
        elif any(word in cta_lower for word in ['sign up', 'subscribe', 'join', 'register']):
            return 'registration'
        elif any(word in cta_lower for word in ['download', 'get', 'claim']):
            return 'acquisition'
        else:
            return 'other'

    def _generate_trend_insights(self, trends: Dict[str, Any]) -> List[str]:
        """Generate human-readable insights from trend data.

        Args:
            trends: Trend analysis data

        Returns:
            List of insight strings
        """
        insights = []

        # Volume insights
        if 'ads_by_month' in trends:
            monthly_counts = list(trends['ads_by_month'].values())
            if len(monthly_counts) >= 2:
                if monthly_counts[-1] > monthly_counts[0] * 1.5:
                    insights.append("Advertising volume has increased significantly over the period")
                elif monthly_counts[-1] < monthly_counts[0] * 0.5:
                    insights.append("Advertising volume has decreased noticeably over the period")

        # Messaging insights
        if 'messaging_trends' in trends and 'evolution' in trends['messaging_trends']:
            for evolution in trends['messaging_trends']['evolution']:
                if evolution.get('new_elements'):
                    insights.append(f"New messaging focus on: {', '.join(evolution['new_elements'][:3])}")

        # Video trend
        if 'visual_trends' in trends and 'image_vs_video_by_month' in trends['visual_trends']:
            video_data = trends['visual_trends']['image_vs_video_by_month']
            if video_data:
                months = sorted(video_data.keys())
                if len(months) >= 2:
                    first_video_pct = video_data[months[0]]['video_percentage']
                    last_video_pct = video_data[months[-1]]['video_percentage']

                    if last_video_pct > first_video_pct + 20:
                        insights.append("Significant shift towards video content")

        # Strategy shifts
        if 'strategy_shifts' in trends and trends['strategy_shifts']:
            major_shifts = [s for s in trends['strategy_shifts'] if s.get('magnitude', 0) > 15]
            if major_shifts:
                insights.append(f"Detected {len(major_shifts)} major strategy shifts during the period")

        return insights

    def _analyze_market_trends(self, competitor_trends: Dict[str, Dict]) -> Dict[str, Any]:
        """Analyze overall market trends from competitor data."""
        market_insights = {
            'common_patterns': [],
            'divergent_strategies': [],
            'market_maturity': 'unknown'
        }

        # Find common patterns across competitors
        all_power_words = []
        all_cta_types = []

        for competitor, trends in competitor_trends.items():
            if 'messaging_trends' in trends:
                power_words_data = trends['messaging_trends'].get('power_words_by_month', {})
                for words in power_words_data.values():
                    all_power_words.extend(words)

        # Most common across all competitors
        if all_power_words:
            common_words = Counter(all_power_words).most_common(5)
            market_insights['common_patterns'].append(f"Industry-wide power words: {', '.join([w[0] for w in common_words])}")

        return market_insights

    def _analyze_competitive_positioning(self, competitor_trends: Dict[str, Dict]) -> Dict[str, Any]:
        """Analyze how competitors are positioned relative to each other."""
        positioning = {
            'leaders': [],
            'followers': [],
            'innovators': []
        }

        # Rank by volume
        volume_ranking = []
        for competitor, trends in competitor_trends.items():
            total_ads = trends.get('total_ads', 0)
            volume_ranking.append((competitor, total_ads))

        volume_ranking.sort(key=lambda x: x[1], reverse=True)

        if volume_ranking:
            positioning['leaders'] = [volume_ranking[0][0]]  # Top advertiser
            positioning['followers'] = [v[0] for v in volume_ranking[1:]]

        return positioning

    def _identify_market_opportunities(self, competitor_trends: Dict[str, Dict]) -> List[str]:
        """Identify market opportunities based on competitor analysis."""
        opportunities = []

        # Look for underutilized channels or messaging
        all_messaging = []
        for competitor, trends in competitor_trends.items():
            if 'messaging_trends' in trends:
                all_messaging.append(trends['messaging_trends'])

        # Simplified opportunity detection
        opportunities.append("Analyze gaps in competitor messaging for differentiation")
        opportunities.append("Consider seasonal patterns for campaign timing")

        return opportunities
