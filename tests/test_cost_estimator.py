"""Tests for cost estimator."""

import pytest
from utils.cost_estimator import CostEstimator


class TestCostEstimator:
    """Tests for CostEstimator."""

    def test_initialization(self):
        """Test estimator initialization."""
        estimator = CostEstimator()
        assert estimator is not None

    def test_estimate_scraping_cost(self):
        """Test cost estimation for scraping."""
        estimator = CostEstimator()

        estimate = estimator.estimate_scraping_cost(
            num_ads=50,
            platforms=['facebook'],
            analyze_visual=True,
            analyze_messaging=True
        )

        assert 'total_estimated_cost' in estimate
        assert estimate['total_estimated_cost'] > 0
        assert 'breakdown' in estimate
        assert len(estimate['breakdown']) > 0

    def test_estimate_with_quick_filter(self):
        """Test that quick filter reduces costs."""
        estimator = CostEstimator()

        # Without quick filter
        estimate_full = estimator.estimate_scraping_cost(
            num_ads=100,
            quick_filter=False,
            analyze_visual=True
        )

        # With quick filter
        estimate_filtered = estimator.estimate_scraping_cost(
            num_ads=100,
            quick_filter=True,
            analyze_visual=True
        )

        # Quick filter should be cheaper
        assert estimate_filtered['total_estimated_cost'] < estimate_full['total_estimated_cost']

    def test_estimate_creative_generation(self):
        """Test creative generation cost estimate."""
        estimator = CostEstimator()

        estimate = estimator.estimate_creative_generation(num_variations=5)

        assert 'total_estimated_cost' in estimate
        assert estimate['num_variations'] == 5
        assert estimate['total_estimated_cost'] > 0

    def test_estimate_with_caching(self):
        """Test cost estimation with caching."""
        estimator = CostEstimator()

        estimate = estimator.estimate_with_caching(
            num_ads=100,
            cache_hit_rate=0.5
        )

        assert 'full_cost' in estimate
        assert 'cost_with_cache' in estimate
        assert 'savings' in estimate
        assert estimate['cost_with_cache'] < estimate['full_cost']
        assert estimate['savings'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
