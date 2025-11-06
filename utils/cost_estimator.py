"""Cost estimation system for API usage."""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from database import CostRepository

logger = logging.getLogger(__name__)


# Model pricing per 1M tokens (input / output)
MODEL_PRICING = {
    'claude-3-haiku-20240307': (0.25, 1.25),
    'claude-3-5-sonnet-20241022': (3.00, 15.00),
    'claude-opus-3-20240229': (15.00, 75.00),
}

# Average token estimates for different operations
OPERATION_ESTIMATES = {
    'quick_visual_analysis': {
        'input_tokens': 1500,  # Image + prompt
        'output_tokens': 100,
        'model': 'claude-3-haiku-20240307'
    },
    'deep_visual_analysis': {
        'input_tokens': 2000,  # Image + detailed prompt
        'output_tokens': 800,
        'model': 'claude-3-5-sonnet-20241022'
    },
    'messaging_analysis': {
        'input_tokens': 500,  # Text + prompt
        'output_tokens': 400,
        'model': 'claude-3-5-sonnet-20241022'
    },
    'video_frame_analysis': {
        'input_tokens': 1800,  # Frame + prompt
        'output_tokens': 200,
        'model': 'claude-3-5-sonnet-20241022'
    },
    'pattern_detection': {
        'input_tokens': 3000,  # Multiple ads summary
        'output_tokens': 1000,
        'model': 'claude-3-5-sonnet-20241022'
    },
    'recommendation_generation': {
        'input_tokens': 4000,  # All analysis data
        'output_tokens': 2000,
        'model': 'claude-3-5-sonnet-20241022'
    },
    'creative_generation_dalle': {
        'cost': 0.040,  # Fixed cost per image (DALL-E 3 standard)
    }
}


@dataclass
class CostEstimate:
    """Container for cost estimate data."""
    operation: str
    estimated_cost: float
    estimated_tokens: int
    model: str
    quantity: int = 1

    @property
    def total_cost(self) -> float:
        """Calculate total cost for quantity."""
        return self.estimated_cost * self.quantity


class CostEstimator:
    """Estimates and tracks API costs."""

    def __init__(self):
        """Initialize cost estimator."""
        pass

    def estimate_scraping_cost(self, num_ads: int, platforms: List[str] = None,
                               analyze_visual: bool = True,
                               analyze_messaging: bool = True,
                               quick_filter: bool = True,
                               video_ads_percentage: float = 0.1) -> Dict[str, Any]:
        """Estimate cost for a complete scraping and analysis session.

        Args:
            num_ads: Number of ads to scrape
            platforms: List of platforms
            analyze_visual: Whether to perform visual analysis
            analyze_messaging: Whether to perform messaging analysis
            quick_filter: Whether to use quick quality filter
            video_ads_percentage: Estimated percentage of video ads

        Returns:
            Cost breakdown dictionary
        """
        if platforms is None:
            platforms = ['facebook', 'google']

        estimates = []
        total_cost = 0.0

        # Scraping cost (minimal - mainly bandwidth/infrastructure)
        scraping_cost = num_ads * len(platforms) * 0.001  # $0.001 per ad
        estimates.append({
            'operation': 'Scraping',
            'quantity': num_ads * len(platforms),
            'unit_cost': 0.001,
            'total_cost': scraping_cost
        })
        total_cost += scraping_cost

        # Visual analysis
        if analyze_visual:
            num_image_ads = int(num_ads * (1 - video_ads_percentage))
            num_video_ads = int(num_ads * video_ads_percentage)

            if quick_filter:
                # All ads go through quick filter first
                quick_filter_cost = self._estimate_operation_cost(
                    'quick_visual_analysis',
                    num_image_ads
                )
                estimates.append(quick_filter_cost)
                total_cost += quick_filter_cost['total_cost']

                # Assume 50% pass the quick filter and get deep analysis
                deep_analysis_count = int(num_image_ads * 0.5)
                deep_cost = self._estimate_operation_cost(
                    'deep_visual_analysis',
                    deep_analysis_count
                )
                estimates.append(deep_cost)
                total_cost += deep_cost['total_cost']
            else:
                # All get deep analysis
                deep_cost = self._estimate_operation_cost(
                    'deep_visual_analysis',
                    num_image_ads
                )
                estimates.append(deep_cost)
                total_cost += deep_cost['total_cost']

            # Video analysis (5 frames per video)
            if num_video_ads > 0:
                video_cost = self._estimate_operation_cost(
                    'video_frame_analysis',
                    num_video_ads * 5  # 5 frames per video
                )
                estimates.append(video_cost)
                total_cost += video_cost['total_cost']

        # Messaging analysis
        if analyze_messaging:
            messaging_cost = self._estimate_operation_cost(
                'messaging_analysis',
                num_ads
            )
            estimates.append(messaging_cost)
            total_cost += messaging_cost['total_cost']

        # Pattern detection (once per session)
        pattern_cost = self._estimate_operation_cost('pattern_detection', 1)
        estimates.append(pattern_cost)
        total_cost += pattern_cost['total_cost']

        # Recommendation generation (once per session)
        rec_cost = self._estimate_operation_cost('recommendation_generation', 1)
        estimates.append(rec_cost)
        total_cost += rec_cost['total_cost']

        return {
            'total_estimated_cost': round(total_cost, 2),
            'breakdown': estimates,
            'parameters': {
                'num_ads': num_ads,
                'platforms': platforms,
                'analyze_visual': analyze_visual,
                'analyze_messaging': analyze_messaging,
                'quick_filter_enabled': quick_filter,
                'estimated_video_ads': int(num_ads * video_ads_percentage)
            },
            'notes': [
                'Costs are estimates and may vary based on actual content',
                'Caching can significantly reduce costs for repeat analyses',
                f'Quick filter enabled: saves ~50% on visual analysis costs',
                'First-time scraping will be more expensive than cached re-analysis'
            ]
        }

    def _estimate_operation_cost(self, operation: str, quantity: int) -> Dict[str, Any]:
        """Estimate cost for a specific operation.

        Args:
            operation: Operation type
            quantity: Number of operations

        Returns:
            Cost estimate dictionary
        """
        if operation not in OPERATION_ESTIMATES:
            return {
                'operation': operation,
                'quantity': quantity,
                'unit_cost': 0.0,
                'total_cost': 0.0,
                'model': 'unknown'
            }

        estimate = OPERATION_ESTIMATES[operation]

        # Handle fixed-cost operations (like DALL-E)
        if 'cost' in estimate:
            unit_cost = estimate['cost']
            total_cost = unit_cost * quantity
            return {
                'operation': operation,
                'quantity': quantity,
                'unit_cost': round(unit_cost, 4),
                'total_cost': round(total_cost, 4),
                'model': 'DALL-E 3'
            }

        # Calculate token-based cost
        model = estimate['model']
        input_tokens = estimate['input_tokens']
        output_tokens = estimate['output_tokens']

        if model in MODEL_PRICING:
            input_cost_per_m, output_cost_per_m = MODEL_PRICING[model]
            unit_cost = (input_tokens / 1_000_000 * input_cost_per_m +
                        output_tokens / 1_000_000 * output_cost_per_m)
            total_cost = unit_cost * quantity

            return {
                'operation': operation,
                'quantity': quantity,
                'unit_cost': round(unit_cost, 4),
                'total_cost': round(total_cost, 4),
                'model': model,
                'tokens_per_operation': input_tokens + output_tokens
            }

        return {
            'operation': operation,
            'quantity': quantity,
            'unit_cost': 0.0,
            'total_cost': 0.0
        }

    def estimate_creative_generation(self, num_variations: int = 5) -> Dict[str, Any]:
        """Estimate cost for generating ad creative variations.

        Args:
            num_variations: Number of creative variations to generate

        Returns:
            Cost estimate
        """
        # DALL-E cost per image
        dalle_cost = num_variations * 0.040

        # Analysis of generated images
        analysis_cost = self._estimate_operation_cost(
            'deep_visual_analysis',
            num_variations
        )

        total_cost = dalle_cost + analysis_cost['total_cost']

        return {
            'total_estimated_cost': round(total_cost, 2),
            'num_variations': num_variations,
            'dalle_cost': round(dalle_cost, 2),
            'analysis_cost': round(analysis_cost['total_cost'], 2),
            'cost_per_variation': round(total_cost / num_variations, 4)
        }

    def get_session_actual_cost(self, session_id: str) -> Dict[str, Any]:
        """Get actual costs for a completed session.

        Args:
            session_id: Session identifier

        Returns:
            Actual cost breakdown
        """
        with CostRepository() as cost_repo:
            total_cost = cost_repo.get_session_cost(session_id)
            breakdown = cost_repo.get_cost_breakdown(days=365)  # Get all costs

            return {
                'session_id': session_id,
                'total_cost': round(total_cost, 4),
                'breakdown': breakdown
            }

    def get_cost_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate a cost report for the specified time period.

        Args:
            days: Number of days to look back

        Returns:
            Cost report
        """
        with CostRepository() as cost_repo:
            total_cost = cost_repo.get_total_cost(days=days)
            breakdown = cost_repo.get_cost_breakdown(days=days)

            return {
                'period_days': days,
                'total_cost': round(total_cost, 2),
                'breakdown': {k: round(v, 4) for k, v in breakdown.items()},
                'average_daily_cost': round(total_cost / days if days > 0 else 0, 4)
            }

    def estimate_with_caching(self, num_ads: int, cache_hit_rate: float = 0.3) -> Dict[str, Any]:
        """Estimate costs considering cache hit rate.

        Args:
            num_ads: Number of ads
            cache_hit_rate: Expected cache hit rate (0.0 to 1.0)

        Returns:
            Cost estimate with caching
        """
        # Full cost without cache
        no_cache_estimate = self.estimate_scraping_cost(num_ads, analyze_visual=True, analyze_messaging=True)
        full_cost = no_cache_estimate['total_estimated_cost']

        # Estimate cache savings (mainly on analysis)
        # Assume scraping and final analysis always happen, but individual ad analysis can be cached
        scraping_cost = num_ads * 0.001
        analysis_cost = full_cost - scraping_cost

        cached_analysis_cost = analysis_cost * (1 - cache_hit_rate)
        total_with_cache = scraping_cost + cached_analysis_cost

        savings = full_cost - total_with_cache
        savings_percentage = (savings / full_cost) * 100 if full_cost > 0 else 0

        return {
            'full_cost': round(full_cost, 2),
            'cost_with_cache': round(total_with_cache, 2),
            'savings': round(savings, 2),
            'savings_percentage': round(savings_percentage, 1),
            'cache_hit_rate': cache_hit_rate * 100,
            'notes': [
                f'Caching saves ${savings:.2f} ({savings_percentage:.1f}%)',
                'Cache hit rate depends on how many ads you\'ve analyzed before',
                'Analyzing the same competitor multiple times has high cache benefits'
            ]
        }

    def print_estimate(self, estimate: Dict[str, Any]):
        """Print a formatted cost estimate.

        Args:
            estimate: Estimate dictionary from estimate_scraping_cost
        """
        print("\n" + "="*60)
        print("COST ESTIMATE")
        print("="*60)

        print(f"\nTotal Estimated Cost: ${estimate['total_estimated_cost']:.2f}")

        print("\nBreakdown:")
        print("-" * 60)

        for item in estimate['breakdown']:
            operation = item['operation']
            quantity = item['quantity']
            unit_cost = item.get('unit_cost', 0)
            total = item['total_cost']
            model = item.get('model', 'N/A')

            print(f"  {operation:30} x{quantity:4}  @${unit_cost:.4f} = ${total:7.4f}")
            print(f"    Model: {model}")

        if 'notes' in estimate:
            print("\nNotes:")
            for note in estimate['notes']:
                print(f"  • {note}")

        print("="*60 + "\n")
