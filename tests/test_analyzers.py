"""Tests for analyzer modules."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from analyzers.cached_analyzer import CachedVisualAnalyzer, CachedMessagingAnalyzer
from analyzers.trend_analyzer import TrendAnalyzer
from analyzers.competitive_benchmarking import CompetitiveBenchmarking


class TestCachedVisualAnalyzer:
    """Tests for CachedVisualAnalyzer."""

    @patch('analyzers.cached_analyzer.Anthropic')
    def test_quick_quality_check(self, mock_anthropic):
        """Test quick quality filtering."""
        # Mock response
        mock_response = Mock()
        mock_response.content = [Mock(text="7.5")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=10)

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        analyzer = CachedVisualAnalyzer()

        # Create a temporary test image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'fake image data')
            temp_path = f.name

        try:
            # This would normally analyze, but we're mocking
            score = analyzer._quick_quality_check("fake_data", "image/png")
            assert 0 <= score <= 10

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_calculate_file_hash(self):
        """Test file hash calculation."""
        analyzer = CachedVisualAnalyzer()

        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'test content')
            temp_path = f.name

        try:
            hash1 = analyzer._calculate_file_hash(temp_path)
            hash2 = analyzer._calculate_file_hash(temp_path)

            assert hash1 == hash2
            assert len(hash1) == 32  # MD5 hash length

        finally:
            os.remove(temp_path)


class TestCachedMessagingAnalyzer:
    """Tests for CachedMessagingAnalyzer."""

    @patch('analyzers.cached_analyzer.Anthropic')
    def test_analyze_text(self, mock_anthropic):
        """Test text analysis."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Good messaging")]
        mock_response.usage = Mock(input_tokens=50, output_tokens=20)

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        analyzer = CachedMessagingAnalyzer()
        result = analyzer._analyze_with_sonnet("Test ad copy")

        assert 'analysis' in result
        assert result['model_used'] == 'claude-3-5-sonnet-20241022'

    def test_empty_text(self):
        """Test handling of empty text."""
        analyzer = CachedMessagingAnalyzer()
        result = analyzer.analyze_text("", use_cache=False)

        assert 'error' in result


class TestTrendAnalyzer:
    """Tests for TrendAnalyzer."""

    def test_initialization(self):
        """Test analyzer initialization."""
        analyzer = TrendAnalyzer()
        assert analyzer is not None

    def test_group_ads_by_month(self):
        """Test grouping ads by month."""
        from datetime import datetime
        from database.models import Advertisement

        analyzer = TrendAnalyzer()

        # Create mock ads
        ads = [
            Advertisement(id='1', scraped_at=datetime(2024, 1, 15)),
            Advertisement(id='2', scraped_at=datetime(2024, 1, 20)),
            Advertisement(id='3', scraped_at=datetime(2024, 2, 10)),
        ]

        grouped = analyzer._group_ads_by_month(ads)

        assert '2024-01' in grouped
        assert '2024-02' in grouped
        assert len(grouped['2024-01']) == 2
        assert len(grouped['2024-02']) == 1

    def test_categorize_cta(self):
        """Test CTA categorization."""
        analyzer = TrendAnalyzer()

        assert analyzer._categorize_cta("Buy Now") == 'transactional'
        assert analyzer._categorize_cta("Learn More") == 'informational'
        assert analyzer._categorize_cta("Sign Up") == 'registration'
        assert analyzer._categorize_cta("Download Free") == 'acquisition'


class TestCompetitiveBenchmarking:
    """Tests for CompetitiveBenchmarking."""

    def test_initialization(self):
        """Test benchmarking initialization."""
        benchmarking = CompetitiveBenchmarking()
        assert benchmarking is not None
        assert benchmarking.trend_analyzer is not None

    def test_categorize_cta(self):
        """Test CTA categorization."""
        benchmarking = CompetitiveBenchmarking()

        assert benchmarking._categorize_cta("shop now") == 'transactional'
        assert benchmarking._categorize_cta("discover more") == 'informational'
        assert benchmarking._categorize_cta("join today") == 'registration'

    def test_analyze_tone(self):
        """Test tone analysis."""
        benchmarking = CompetitiveBenchmarking()

        assert benchmarking._analyze_tone("Amazing! Revolutionary!") == 'enthusiastic'
        assert benchmarking._analyze_tone("Professional trusted proven") == 'professional'
        assert benchmarking._analyze_tone("Easy and simple") == 'casual'
        assert benchmarking._analyze_tone("Standard text") == 'neutral'

    def test_calculate_consistency(self):
        """Test consistency calculation."""
        benchmarking = CompetitiveBenchmarking()

        # Perfect consistency
        scores1 = [7.0, 7.0, 7.0]
        consistency1 = benchmarking._calculate_consistency(scores1)
        assert consistency1 == 1.0

        # Variable scores
        scores2 = [5.0, 7.0, 9.0]
        consistency2 = benchmarking._calculate_consistency(scores2)
        assert 0 < consistency2 < 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
