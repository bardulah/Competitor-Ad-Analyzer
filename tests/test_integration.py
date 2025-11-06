"""Integration tests that actually test the system end-to-end."""

import pytest
import os
import tempfile
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, Advertisement
from database.repositories import AdRepository
from core.config import Settings
from exceptions import RecordNotFoundError, DuplicateRecordError


@pytest.fixture
def test_settings():
    """Create test settings with temporary database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = Path(tmpdir) / "test.db"
        settings = Settings(
            anthropic_api_key="test-key",
            database_url=f"sqlite:///{test_db}",
            data_dir=Path(tmpdir) / "data",
            screenshots_dir=Path(tmpdir) / "screenshots",
            reports_dir=Path(tmpdir) / "reports",
        )
        yield settings


@pytest.fixture
def test_db(test_settings):
    """Create test database."""
    engine = create_engine(test_settings.database_url)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(engine)


class TestDatabaseOperations:
    """Test actual database operations."""

    def test_save_and_retrieve_ad(self, test_db):
        """Test saving and retrieving an advertisement."""
        # Create ad
        ad_data = {
            'id': 'test_ad_001',
            'platform': 'facebook',
            'advertiser': 'Test Company',
            'headline': 'Test Headline',
            'body_text': 'Test body text',
            'cta': 'Shop Now',
            'is_active': True
        }

        with AdRepository(test_db) as repo:
            # Save ad
            ad = repo.save_ad(ad_data)
            assert ad.id == 'test_ad_001'
            assert ad.advertiser == 'Test Company'

            # Retrieve ad
            retrieved = repo.get_ad('test_ad_001')
            assert retrieved is not None
            assert retrieved.headline == 'Test Headline'

    def test_duplicate_ad_handling(self, test_db):
        """Test that duplicate ads are handled properly."""
        ad_data = {
            'id': 'test_ad_002',
            'platform': 'facebook',
            'advertiser': 'Test Company',
            'is_active': True
        }

        with AdRepository(test_db) as repo:
            # Save first time
            ad1 = repo.save_ad(ad_data)
            assert ad1.id == 'test_ad_002'

            # Save again - should update, not error
            ad_data['headline'] = 'Updated Headline'
            ad2 = repo.save_ad(ad_data)
            assert ad2.headline == 'Updated Headline'

            # Verify only one record exists
            all_ads = test_db.query(Advertisement).filter_by(id='test_ad_002').all()
            assert len(all_ads) == 1

    def test_get_ads_by_advertiser(self, test_db):
        """Test filtering ads by advertiser."""
        # Create multiple ads
        ads = [
            {'id': 'ad_nike_1', 'platform': 'facebook', 'advertiser': 'Nike', 'is_active': True},
            {'id': 'ad_nike_2', 'platform': 'google', 'advertiser': 'Nike', 'is_active': True},
            {'id': 'ad_adidas_1', 'platform': 'facebook', 'advertiser': 'Adidas', 'is_active': True},
        ]

        with AdRepository(test_db) as repo:
            for ad_data in ads:
                repo.save_ad(ad_data)

            # Get Nike ads
            nike_ads = repo.get_ads_by_advertiser('Nike', limit=100)
            assert len(nike_ads) == 2
            assert all(ad.advertiser == 'Nike' for ad in nike_ads)

            # Get Adidas ads
            adidas_ads = repo.get_ads_by_advertiser('Adidas', limit=100)
            assert len(adidas_ads) == 1

    def test_get_ads_by_platform(self, test_db):
        """Test filtering ads by platform."""
        ads = [
            {'id': 'ad_fb_1', 'platform': 'facebook', 'advertiser': 'Test', 'is_active': True},
            {'id': 'ad_fb_2', 'platform': 'facebook', 'advertiser': 'Test', 'is_active': True},
            {'id': 'ad_google_1', 'platform': 'google', 'advertiser': 'Test', 'is_active': True},
        ]

        with AdRepository(test_db) as repo:
            for ad_data in ads:
                repo.save_ad(ad_data)

            # Get Facebook ads
            fb_ads = repo.get_ads_by_platform('facebook', limit=100)
            assert len(fb_ads) == 2

            # Get Google ads
            google_ads = repo.get_ads_by_platform('google', limit=100)
            assert len(google_ads) == 1

    def test_search_ads(self, test_db):
        """Test searching ads by text."""
        ads = [
            {
                'id': 'ad_search_1',
                'platform': 'facebook',
                'advertiser': 'Nike',
                'headline': 'Buy running shoes',
                'body_text': 'Best shoes for marathon',
                'is_active': True
            },
            {
                'id': 'ad_search_2',
                'platform': 'facebook',
                'advertiser': 'Adidas',
                'headline': 'Soccer cleats',
                'body_text': 'Professional football shoes',
                'is_active': True
            },
        ]

        with AdRepository(test_db) as repo:
            for ad_data in ads:
                repo.save_ad(ad_data)

            # Search for 'shoes'
            results = repo.search_ads('shoes', limit=100)
            assert len(results) == 2

            # Search for 'running'
            results = repo.search_ads('running', limit=100)
            assert len(results) == 1
            assert results[0].advertiser == 'Nike'


class TestConfiguration:
    """Test configuration management."""

    def test_settings_validation(self):
        """Test that settings are validated properly."""
        # Valid settings
        settings = Settings(anthropic_api_key="test-key")
        assert settings.anthropic_api_key == "test-key"
        assert settings.max_concurrent_requests >= 1

    def test_settings_create_directories(self, test_settings):
        """Test that settings create required directories."""
        assert test_settings.data_dir.exists()
        assert test_settings.screenshots_dir.exists()
        assert test_settings.reports_dir.exists()

    def test_settings_from_env(self, monkeypatch):
        """Test loading settings from environment."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-test-key")
        monkeypatch.setenv("MAX_CONCURRENT_REQUESTS", "5")

        settings = Settings()
        assert settings.anthropic_api_key == "env-test-key"
        assert settings.max_concurrent_requests == 5


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="Requires ANTHROPIC_API_KEY for live API test"
)
class TestLiveAPIIntegration:
    """Tests that use real API (skip if no API key)."""

    def test_anthropic_connection(self):
        """Test that we can connect to Anthropic API."""
        from anthropic import Anthropic

        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Simple test message
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=50,
            messages=[{"role": "user", "content": "Say 'test successful' and nothing else."}]
        )

        assert response.content[0].text
        assert len(response.content[0].text) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
