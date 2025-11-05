"""AI-powered campaign advisor for generating actionable recommendations."""

import logging
from typing import Dict, Any, List, Optional
from anthropic import Anthropic
import json

from config import ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)


class CampaignAdvisor:
    """Generates campaign recommendations based on competitor ad analysis."""

    def __init__(self):
        """Initialize the campaign advisor."""
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)

    def generate_recommendations(
        self,
        ads_data: List[Dict[str, Any]],
        patterns: Optional[Dict[str, Any]] = None,
        visual_analyses: Optional[List[Dict[str, Any]]] = None,
        messaging_analyses: Optional[List[Dict[str, Any]]] = None,
        campaign_goal: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive campaign recommendations.

        Args:
            ads_data: List of scraped ad data
            patterns: Detected patterns dictionary
            visual_analyses: Visual analysis results
            messaging_analyses: Messaging analysis results
            campaign_goal: Optional campaign goal (e.g., "increase conversions", "brand awareness")

        Returns:
            Dictionary containing recommendations
        """
        logger.info("Generating campaign recommendations...")

        # Prepare data summary for AI analysis
        summary = self._prepare_data_summary(
            ads_data,
            patterns,
            visual_analyses,
            messaging_analyses
        )

        # Generate recommendations
        recommendations = {
            'visual_recommendations': self._generate_visual_recommendations(summary, campaign_goal),
            'messaging_recommendations': self._generate_messaging_recommendations(summary, campaign_goal),
            'strategic_recommendations': self._generate_strategic_recommendations(summary, campaign_goal),
            'tactical_actions': self._generate_tactical_actions(summary, campaign_goal)
        }

        # Generate overall campaign strategy
        recommendations['campaign_strategy'] = self._generate_campaign_strategy(
            recommendations,
            campaign_goal
        )

        logger.info("Recommendations generated successfully")
        return recommendations

    def _prepare_data_summary(
        self,
        ads_data: List[Dict[str, Any]],
        patterns: Optional[Dict[str, Any]],
        visual_analyses: Optional[List[Dict[str, Any]]],
        messaging_analyses: Optional[List[Dict[str, Any]]]
    ) -> str:
        """Prepare a summary of all analysis data.

        Args:
            ads_data: List of ad data
            patterns: Pattern analysis
            visual_analyses: Visual analyses
            messaging_analyses: Messaging analyses

        Returns:
            Summary string
        """
        summary_parts = []

        # Basic stats
        summary_parts.append(f"Total ads analyzed: {len(ads_data)}")

        # Platform distribution
        if patterns and 'metadata_patterns' in patterns:
            platforms = patterns['metadata_patterns'].get('platform_distribution', {})
            summary_parts.append(f"Platforms: {', '.join(platforms.keys())}")

        # Visual patterns
        if patterns and 'visual_patterns' in patterns:
            visual = patterns['visual_patterns']
            if visual.get('common_colors'):
                colors = [c[0] for c in visual['common_colors'][:3]]
                summary_parts.append(f"Common colors: {', '.join(colors)}")
            if visual.get('common_styles'):
                styles = [s[0] for s in visual['common_styles'][:3]]
                summary_parts.append(f"Common styles: {', '.join(styles)}")

        # Messaging patterns
        if patterns and 'messaging_patterns' in patterns:
            messaging = patterns['messaging_patterns']
            if messaging.get('most_common_power_words'):
                words = [w[0] for w in messaging['most_common_power_words'][:5]]
                summary_parts.append(f"Top power words: {', '.join(words)}")
            if messaging.get('most_common_cta_types'):
                ctas = [c[0] for c in messaging['most_common_cta_types'][:3]]
                summary_parts.append(f"Common CTAs: {', '.join(ctas)}")

        # Sample ad details
        if visual_analyses:
            summary_parts.append(f"\nVisual analyses available: {len(visual_analyses)}")
            # Include snippet of first analysis
            if visual_analyses[0].get('raw_analysis'):
                snippet = visual_analyses[0]['raw_analysis'][:500]
                summary_parts.append(f"Sample visual analysis: {snippet}...")

        if messaging_analyses:
            summary_parts.append(f"\nMessaging analyses available: {len(messaging_analyses)}")

        return '\n'.join(summary_parts)

    def _generate_visual_recommendations(
        self,
        data_summary: str,
        campaign_goal: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Generate visual design recommendations.

        Args:
            data_summary: Summary of analysis data
            campaign_goal: Optional campaign goal

        Returns:
            List of visual recommendations
        """
        try:
            prompt = f"""Based on this competitor ad analysis:

{data_summary}

Campaign Goal: {campaign_goal or 'General effectiveness'}

Provide 5-7 specific visual design recommendations for creating competitive ads. For each recommendation:
1. What to do (specific and actionable)
2. Why it works (based on the analysis)
3. Implementation tips

Format as JSON array with objects containing: "recommendation", "rationale", "implementation", "priority" (high/medium/low)"""

            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Try to parse JSON response
            response_text = response.content[0].text

            try:
                # Extract JSON from response
                json_start = response_text.find('[')
                json_end = response_text.rfind(']') + 1
                if json_start >= 0 and json_end > json_start:
                    recommendations = json.loads(response_text[json_start:json_end])
                    return recommendations
            except:
                # If JSON parsing fails, return structured text
                return [{
                    'recommendation': 'See detailed analysis',
                    'rationale': response_text,
                    'implementation': 'Review the full analysis for implementation details',
                    'priority': 'high'
                }]

        except Exception as e:
            logger.error(f"Error generating visual recommendations: {e}")
            return [{
                'recommendation': 'Error generating recommendations',
                'rationale': str(e),
                'implementation': 'Please check logs',
                'priority': 'high'
            }]

    def _generate_messaging_recommendations(
        self,
        data_summary: str,
        campaign_goal: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Generate messaging and copy recommendations.

        Args:
            data_summary: Summary of analysis data
            campaign_goal: Optional campaign goal

        Returns:
            List of messaging recommendations
        """
        try:
            prompt = f"""Based on this competitor ad analysis:

{data_summary}

Campaign Goal: {campaign_goal or 'General effectiveness'}

Provide 5-7 specific messaging and copywriting recommendations. For each:
1. What messaging strategy to use
2. Why it's effective (based on competitor data)
3. Example copy/headlines to test

Format as JSON array with objects containing: "strategy", "rationale", "examples", "priority" (high/medium/low)"""

            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            response_text = response.content[0].text

            try:
                json_start = response_text.find('[')
                json_end = response_text.rfind(']') + 1
                if json_start >= 0 and json_end > json_start:
                    recommendations = json.loads(response_text[json_start:json_end])
                    return recommendations
            except:
                return [{
                    'strategy': 'See detailed analysis',
                    'rationale': response_text,
                    'examples': ['Review full analysis for examples'],
                    'priority': 'high'
                }]

        except Exception as e:
            logger.error(f"Error generating messaging recommendations: {e}")
            return [{
                'strategy': 'Error generating recommendations',
                'rationale': str(e),
                'examples': [],
                'priority': 'high'
            }]

    def _generate_strategic_recommendations(
        self,
        data_summary: str,
        campaign_goal: Optional[str]
    ) -> Dict[str, Any]:
        """Generate high-level strategic recommendations.

        Args:
            data_summary: Summary of analysis data
            campaign_goal: Optional campaign goal

        Returns:
            Strategic recommendations dictionary
        """
        try:
            prompt = f"""Based on this competitor ad analysis:

{data_summary}

Campaign Goal: {campaign_goal or 'General effectiveness'}

Provide strategic recommendations covering:
1. Market positioning opportunities
2. Competitive advantages to leverage
3. Gaps in competitor approaches
4. Target audience insights
5. Budget allocation suggestions

Be specific and actionable."""

            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            return {
                'analysis': response.content[0].text,
                'generated_at': logger.handlers[0].formatter.formatTime(
                    logging.LogRecord('', 0, '', 0, '', (), None)
                ) if logger.handlers else 'N/A'
            }

        except Exception as e:
            logger.error(f"Error generating strategic recommendations: {e}")
            return {
                'analysis': f'Error: {str(e)}',
                'generated_at': 'N/A'
            }

    def _generate_tactical_actions(
        self,
        data_summary: str,
        campaign_goal: Optional[str]
    ) -> List[Dict[str, str]]:
        """Generate tactical action items.

        Args:
            data_summary: Summary of analysis data
            campaign_goal: Optional campaign goal

        Returns:
            List of action items
        """
        try:
            prompt = f"""Based on this competitor ad analysis:

{data_summary}

Campaign Goal: {campaign_goal or 'General effectiveness'}

Provide 10 specific, immediately actionable tasks for the marketing team. Each should be:
- Concrete and measurable
- Based on insights from the analysis
- Prioritized

Format as JSON array with objects containing: "action", "timeline", "priority" (high/medium/low), "expected_impact"""

            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            response_text = response.content[0].text

            try:
                json_start = response_text.find('[')
                json_end = response_text.rfind(']') + 1
                if json_start >= 0 and json_end > json_start:
                    actions = json.loads(response_text[json_start:json_end])
                    return actions
            except:
                # Parse as text and create action items
                lines = [line.strip() for line in response_text.split('\n') if line.strip()]
                return [{
                    'action': line,
                    'timeline': 'To be determined',
                    'priority': 'medium',
                    'expected_impact': 'Review analysis for details'
                } for line in lines[:10]]

        except Exception as e:
            logger.error(f"Error generating tactical actions: {e}")
            return [{
                'action': 'Error generating actions',
                'timeline': 'N/A',
                'priority': 'high',
                'expected_impact': str(e)
            }]

    def _generate_campaign_strategy(
        self,
        recommendations: Dict[str, Any],
        campaign_goal: Optional[str]
    ) -> str:
        """Generate an overall campaign strategy document.

        Args:
            recommendations: All recommendation data
            campaign_goal: Optional campaign goal

        Returns:
            Campaign strategy text
        """
        try:
            # Summarize all recommendations
            summary = f"""
Campaign Goal: {campaign_goal or 'General effectiveness'}

Visual Recommendations: {len(recommendations.get('visual_recommendations', []))} insights
Messaging Recommendations: {len(recommendations.get('messaging_recommendations', []))} strategies
Tactical Actions: {len(recommendations.get('tactical_actions', []))} action items
"""

            prompt = f"""Based on these comprehensive recommendations:

{summary}

Create a cohesive campaign strategy document that:
1. Summarizes key insights from competitor analysis
2. Outlines a clear creative direction
3. Provides a prioritized implementation roadmap
4. Sets success metrics and KPIs
5. Identifies potential challenges and mitigation strategies

Make it actionable and ready to present to stakeholders."""

            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=3000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Error generating campaign strategy: {e}")
            return f"Error generating strategy: {str(e)}"

    def export_recommendations(self, recommendations: Dict[str, Any], output_path: str):
        """Export recommendations to JSON file.

        Args:
            recommendations: Recommendations dictionary
            output_path: Path to output file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(recommendations, f, indent=2, ensure_ascii=False)

        logger.info(f"Recommendations exported to {output_path}")
