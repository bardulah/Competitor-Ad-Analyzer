"""Competitive benchmarking and comparison module."""

import logging
from typing import Dict, Any, List, Optional
from collections import Counter, defaultdict

from database import AdRepository, AnalysisRepository
from analyzers.trend_analyzer import TrendAnalyzer

logger = logging.getLogger(__name__)


class CompetitiveBenchmarking:
    """Performs competitive benchmarking across advertisers."""

    def __init__(self):
        """Initialize competitive benchmarking."""
        self.trend_analyzer = TrendAnalyzer()

    def benchmark_competitors(self, competitors: List[str], months: int = 3) -> Dict[str, Any]:
        """Benchmark multiple competitors against each other.

        Args:
            competitors: List of competitor names
            months: Months of data to analyze

        Returns:
            Comprehensive benchmarking report
        """
        logger.info(f"Benchmarking {len(competitors)} competitors")

        benchmark = {
            'competitors': competitors,
            'period_months': months,
            'market_share': self._calculate_market_share(competitors, months),
            'creative_quality': self._benchmark_creative_quality(competitors),
            'messaging_strategies': self._benchmark_messaging(competitors),
            'media_mix': self._benchmark_media_mix(competitors),
            'engagement_indicators': self._benchmark_engagement(competitors),
            'competitive_landscape': self._analyze_competitive_landscape(competitors),
            'market_positioning': self._determine_market_positioning(competitors),
            'white_space_opportunities': self._find_white_space(competitors),
            'recommendations': []
        }

        # Generate strategic recommendations
        benchmark['recommendations'] = self._generate_benchmark_recommendations(benchmark)

        return benchmark

    def _calculate_market_share(self, competitors: List[str], months: int) -> Dict[str, Any]:
        """Calculate advertising volume share of voice.

        Args:
            competitors: List of competitors
            months: Months to analyze

        Returns:
            Market share data
        """
        ad_counts = {}
        total_ads = 0

        with AdRepository() as ad_repo:
            for competitor in competitors:
                ads = ad_repo.get_ads_by_advertiser(competitor, limit=10000)
                count = len(ads)
                ad_counts[competitor] = count
                total_ads += count

        # Calculate share percentages
        share = {}
        for competitor, count in ad_counts.items():
            percentage = (count / total_ads * 100) if total_ads > 0 else 0
            share[competitor] = {
                'ad_count': count,
                'share_percentage': round(percentage, 2)
            }

        # Rank competitors
        ranked = sorted(share.items(), key=lambda x: x[1]['ad_count'], reverse=True)

        return {
            'total_market_ads': total_ads,
            'competitor_share': share,
            'market_leader': ranked[0][0] if ranked else None,
            'ranking': [c[0] for c in ranked]
        }

    def _benchmark_creative_quality(self, competitors: List[str]) -> Dict[str, Any]:
        """Benchmark creative quality across competitors.

        Args:
            competitors: List of competitors

        Returns:
            Quality benchmarking data
        """
        quality_scores = {}

        with AnalysisRepository() as analysis_repo:
            for competitor in competitors:
                # Get top performing ads
                with AdRepository() as ad_repo:
                    ads = ad_repo.get_ads_by_advertiser(competitor, limit=100)

                if not ads:
                    quality_scores[competitor] = {'avg_score': 0, 'sample_size': 0}
                    continue

                # Get their analyses
                session = analysis_repo.session
                from database.models import VisualAnalysis
                ad_ids = [ad.id for ad in ads]

                analyses = session.query(VisualAnalysis)\
                    .filter(VisualAnalysis.ad_id.in_(ad_ids))\
                    .filter(VisualAnalysis.quality_score != None)\
                    .all()

                scores = [a.quality_score for a in analyses if a.quality_score]

                avg_score = sum(scores) / len(scores) if scores else 0

                quality_scores[competitor] = {
                    'avg_score': round(avg_score, 2),
                    'sample_size': len(scores),
                    'top_score': max(scores) if scores else 0,
                    'consistency': round(self._calculate_consistency(scores), 2) if len(scores) > 1 else 0
                }

        # Rank by quality
        ranked = sorted(quality_scores.items(),
                       key=lambda x: x[1]['avg_score'],
                       reverse=True)

        return {
            'scores_by_competitor': quality_scores,
            'quality_leader': ranked[0][0] if ranked else None,
            'ranking': [c[0] for c in ranked]
        }

    def _benchmark_messaging(self, competitors: List[str]) -> Dict[str, Any]:
        """Benchmark messaging strategies.

        Args:
            competitors: List of competitors

        Returns:
            Messaging benchmarking data
        """
        messaging_analysis = {}

        with AdRepository() as ad_repo:
            for competitor in competitors:
                ads = ad_repo.get_ads_by_advertiser(competitor, limit=200)

                # Analyze messaging
                all_text = ' '.join([
                    f"{ad.headline or ''} {ad.body_text or ''}"
                    for ad in ads
                ])

                # Extract key themes
                themes = self._extract_themes(all_text)

                # Analyze CTAs
                ctas = [ad.cta for ad in ads if ad.cta]
                cta_types = Counter([self._categorize_cta(cta) for cta in ctas])

                # Analyze tone
                tone = self._analyze_tone(all_text)

                messaging_analysis[competitor] = {
                    'primary_themes': themes[:5],
                    'cta_distribution': dict(cta_types),
                    'tone': tone,
                    'avg_message_length': len(all_text.split()) // len(ads) if ads else 0
                }

        return messaging_analysis

    def _benchmark_media_mix(self, competitors: List[str]) -> Dict[str, Any]:
        """Benchmark media mix (images vs videos).

        Args:
            competitors: List of competitors

        Returns:
            Media mix benchmarking
        """
        media_analysis = {}

        with AdRepository() as ad_repo:
            for competitor in competitors:
                ads = ad_repo.get_ads_by_advertiser(competitor, limit=500)

                image_ads = sum(1 for ad in ads if ad.image_url and not ad.video_url)
                video_ads = sum(1 for ad in ads if ad.video_url)
                total = len(ads)

                media_analysis[competitor] = {
                    'total_ads': total,
                    'image_ads': image_ads,
                    'video_ads': video_ads,
                    'video_percentage': round((video_ads / total * 100) if total > 0 else 0, 2),
                    'image_percentage': round((image_ads / total * 100) if total > 0 else 0, 2)
                }

        return media_analysis

    def _benchmark_engagement(self, competitors: List[str]) -> Dict[str, Any]:
        """Benchmark engagement indicators.

        Args:
            competitors: List of competitors

        Returns:
            Engagement benchmarking
        """
        engagement_data = {}

        with AdRepository() as ad_repo:
            for competitor in competitors:
                ads = ad_repo.get_ads_by_advertiser(competitor, limit=500)

                # Filter ads with impression data
                ads_with_impressions = [ad for ad in ads if ad.impressions]

                if ads_with_impressions:
                    impressions = [ad.impressions for ad in ads_with_impressions]
                    avg_impressions = sum(impressions) // len(impressions)

                    engagement_data[competitor] = {
                        'avg_impressions': avg_impressions,
                        'total_impressions': sum(impressions),
                        'sample_size': len(ads_with_impressions)
                    }
                else:
                    engagement_data[competitor] = {
                        'avg_impressions': 0,
                        'total_impressions': 0,
                        'sample_size': 0,
                        'note': 'No impression data available'
                    }

        return engagement_data

    def _analyze_competitive_landscape(self, competitors: List[str]) -> Dict[str, Any]:
        """Analyze the overall competitive landscape.

        Args:
            competitors: List of competitors

        Returns:
            Landscape analysis
        """
        landscape = {
            'market_concentration': 'unknown',
            'innovation_level': 'medium',
            'saturation': 'medium',
            'insights': []
        }

        # Determine market concentration (simplified)
        market_share = self._calculate_market_share(competitors, 3)
        if market_share['total_market_ads'] > 0:
            leader_share = market_share['competitor_share'].get(
                market_share['market_leader'], {}
            ).get('share_percentage', 0)

            if leader_share > 50:
                landscape['market_concentration'] = 'highly_concentrated'
                landscape['insights'].append(f"Market is dominated by {market_share['market_leader']} ({leader_share}% share)")
            elif leader_share > 30:
                landscape['market_concentration'] = 'moderately_concentrated'
            else:
                landscape['market_concentration'] = 'fragmented'
                landscape['insights'].append("Market share is distributed among competitors")

        return landscape

    def _determine_market_positioning(self, competitors: List[str]) -> Dict[str, List[str]]:
        """Determine market positioning for each competitor.

        Args:
            competitors: List of competitors

        Returns:
            Positioning map
        """
        positioning = {
            'volume_leaders': [],
            'quality_leaders': [],
            'video_adopters': [],
            'traditional_advertisers': []
        }

        # Get benchmarking data
        market_share = self._calculate_market_share(competitors, 3)
        quality = self._benchmark_creative_quality(competitors)
        media_mix = self._benchmark_media_mix(competitors)

        # Classify competitors
        for competitor in competitors:
            # Volume leaders (top 2)
            ranking = market_share['ranking']
            if competitor in ranking[:2]:
                positioning['volume_leaders'].append(competitor)

            # Quality leaders (above average)
            comp_quality = quality['scores_by_competitor'].get(competitor, {}).get('avg_score', 0)
            if comp_quality > 7.5:
                positioning['quality_leaders'].append(competitor)

            # Video adopters (>30% video)
            video_pct = media_mix.get(competitor, {}).get('video_percentage', 0)
            if video_pct > 30:
                positioning['video_adopters'].append(competitor)
            elif video_pct < 10:
                positioning['traditional_advertisers'].append(competitor)

        return positioning

    def _find_white_space(self, competitors: List[str]) -> List[Dict[str, str]]:
        """Identify white space opportunities.

        Args:
            competitors: List of competitors

        Returns:
            List of opportunities
        """
        opportunities = []

        # Analyze messaging gaps
        messaging = self._benchmark_messaging(competitors)

        all_themes = set()
        for comp_data in messaging.values():
            all_themes.update(comp_data['primary_themes'])

        # Look for underutilized CTAs
        all_cta_types = defaultdict(int)
        for comp_data in messaging.values():
            for cta_type, count in comp_data['cta_distribution'].items():
                all_cta_types[cta_type] += count

        if all_cta_types:
            least_used_cta = min(all_cta_types.items(), key=lambda x: x[1])
            opportunities.append({
                'type': 'cta_opportunity',
                'description': f"Underutilized CTA type: {least_used_cta[0]}",
                'potential': 'medium'
            })

        # Media mix opportunities
        media_mix = self._benchmark_media_mix(competitors)
        avg_video_pct = sum(d['video_percentage'] for d in media_mix.values()) / len(media_mix) if media_mix else 0

        if avg_video_pct < 20:
            opportunities.append({
                'type': 'media_opportunity',
                'description': 'Low video adoption across market - opportunity to stand out with video content',
                'potential': 'high'
            })

        return opportunities

    def _generate_benchmark_recommendations(self, benchmark: Dict[str, Any]) -> List[str]:
        """Generate strategic recommendations from benchmarking data.

        Args:
            benchmark: Benchmarking data

        Returns:
            List of recommendations
        """
        recommendations = []

        # Market share recommendations
        market_share = benchmark['market_share']
        if market_share['market_leader']:
            recommendations.append(
                f"Study {market_share['market_leader']}'s strategy - they lead with {market_share['competitor_share'][market_share['market_leader']]['share_percentage']}% share"
            )

        # Quality recommendations
        quality = benchmark['creative_quality']
        if quality['quality_leader']:
            recommendations.append(
                f"Benchmark creative quality against {quality['quality_leader']} (avg score: {quality['scores_by_competitor'][quality['quality_leader']]['avg_score']})"
            )

        # White space opportunities
        for opportunity in benchmark['white_space_opportunities']:
            if opportunity['potential'] == 'high':
                recommendations.append(opportunity['description'])

        return recommendations

    def _extract_themes(self, text: str) -> List[str]:
        """Extract themes from text (simplified)."""
        # Simplified theme extraction
        common_themes = ['quality', 'value', 'innovation', 'trust', 'convenience',
                        'performance', 'style', 'sustainability', 'affordability']

        found_themes = [theme for theme in common_themes if theme in text.lower()]
        return found_themes if found_themes else ['general']

    def _categorize_cta(self, cta: str) -> str:
        """Categorize a CTA."""
        cta_lower = cta.lower()

        if any(word in cta_lower for word in ['buy', 'shop', 'order']):
            return 'transactional'
        elif any(word in cta_lower for word in ['learn', 'discover', 'see']):
            return 'informational'
        elif any(word in cta_lower for word in ['sign up', 'subscribe', 'join']):
            return 'registration'
        else:
            return 'other'

    def _analyze_tone(self, text: str) -> str:
        """Analyze text tone (simplified)."""
        text_lower = text.lower()

        if any(word in text_lower for word in ['amazing', 'incredible', 'revolutionary', '!']):
            return 'enthusiastic'
        elif any(word in text_lower for word in ['professional', 'proven', 'trusted']):
            return 'professional'
        elif any(word in text_lower for word in ['easy', 'simple', 'friendly']):
            return 'casual'
        else:
            return 'neutral'

    def _calculate_consistency(self, scores: List[float]) -> float:
        """Calculate consistency score (inverse of standard deviation)."""
        if len(scores) < 2:
            return 1.0

        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / len(scores)
        std_dev = variance ** 0.5

        # Convert to 0-1 scale (lower std_dev = higher consistency)
        consistency = 1 / (1 + std_dev)
        return consistency
