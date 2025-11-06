"""Centralized configuration management using Pydantic."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with validation."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )

    # API Keys
    anthropic_api_key: str = Field(..., description="Anthropic Claude API key")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key (optional)")

    # Database
    database_url: str = Field(
        default="sqlite:///./data/competitor_ads.db",
        description="Database connection URL"
    )

    # Directories
    data_dir: Path = Field(default=Path("./data"), description="Data directory")
    screenshots_dir: Path = Field(default=Path("./data/screenshots"), description="Screenshots directory")
    reports_dir: Path = Field(default=Path("./reports"), description="Reports directory")

    # Scraping
    max_concurrent_requests: int = Field(default=3, ge=1, le=10, description="Max concurrent scraping requests")
    request_timeout: int = Field(default=30, ge=10, le=120, description="Request timeout in seconds")
    rate_limit_delay: int = Field(default=2, ge=1, le=10, description="Delay between requests in seconds")
    browser_headless: bool = Field(default=True, description="Run browser in headless mode")

    # Analysis
    min_ad_quality_score: float = Field(default=5.0, ge=0.0, le=10.0, description="Minimum quality score")
    enable_visual_analysis: bool = Field(default=True, description="Enable visual analysis")
    enable_messaging_analysis: bool = Field(default=True, description="Enable messaging analysis")
    use_quick_filter: bool = Field(default=True, description="Use quick quality filter")

    # Cost Limits
    max_session_cost: float = Field(default=10.0, ge=0.0, description="Maximum cost per session in USD")
    warn_cost_threshold: float = Field(default=5.0, ge=0.0, description="Cost warning threshold in USD")

    # API Server
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, ge=1024, le=65535, description="API port")
    api_secret_key: str = Field(default="change-me-in-production", description="API secret key for JWT")
    api_access_token_expire_minutes: int = Field(default=30, description="Access token expiration in minutes")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[Path] = Field(default=None, description="Log file path")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    @property
    def facebook_ad_library_url(self) -> str:
        return "https://www.facebook.com/ads/library/"

    @property
    def google_ads_transparency_url(self) -> str:
        return "https://adstransparency.google.com/"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
