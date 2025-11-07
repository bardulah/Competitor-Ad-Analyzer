"""Sentry integration for error tracking and monitoring."""

import logging
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from core.config import get_settings


def setup_sentry():
    """Setup Sentry error tracking.

    Get your Sentry DSN from: https://sentry.io
    Set SENTRY_DSN environment variable.
    """
    settings = get_settings()
    sentry_dsn = getattr(settings, 'sentry_dsn', None)

    if not sentry_dsn:
        logging.warning("SENTRY_DSN not set. Error tracking disabled.")
        return

    # Determine environment
    environment = getattr(settings, 'environment', 'production')

    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=environment,

        # Enable performance monitoring
        traces_sample_rate=1.0 if environment == 'development' else 0.1,

        # Enable profiling
        profiles_sample_rate=1.0 if environment == 'development' else 0.1,

        # Integrations
        integrations=[
            FastApiIntegration(transaction_style="url"),
            SqlalchemyIntegration(),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            ),
        ],

        # Send PII (be careful in production)
        send_default_pii=False,

        # Release tracking
        release=f"competitor-ad-analyzer@{get_version()}",

        # Don't capture health check errors
        ignore_errors=[
            KeyboardInterrupt,
        ],

        # Before send callback to filter events
        before_send=before_send_filter,
    )

    logging.info(f"Sentry initialized for environment: {environment}")


def before_send_filter(event, hint):
    """Filter events before sending to Sentry."""

    # Don't send health check failures
    if event.get('request', {}).get('url', '').endswith('/health'):
        return None

    # Don't send expected errors
    if 'exception' in event:
        exc_type = event['exception']['values'][0].get('type', '')
        if exc_type in ['RateLimitError', 'NoAdsFoundError']:
            return None

    return event


def get_version():
    """Get application version."""
    try:
        with open('VERSION', 'r') as f:
            return f.read().strip()
    except:
        return '2.1.0'


# Context managers for tracking
def track_scraping(platform: str, query: str):
    """Context manager to track scraping operations."""
    with sentry_sdk.start_transaction(op="scrape", name=f"scrape_{platform}"):
        sentry_sdk.set_context("scraping", {
            "platform": platform,
            "query": query
        })
        yield


def track_analysis(analysis_type: str, ad_id: str):
    """Context manager to track analysis operations."""
    with sentry_sdk.start_transaction(op="analyze", name=f"analyze_{analysis_type}"):
        sentry_sdk.set_context("analysis", {
            "type": analysis_type,
            "ad_id": ad_id
        })
        yield


# Helper functions
def capture_message(message: str, level: str = "info"):
    """Capture a message in Sentry."""
    sentry_sdk.capture_message(message, level=level)


def capture_exception(exception: Exception):
    """Capture an exception in Sentry."""
    sentry_sdk.capture_exception(exception)


def set_user(user_id: str, email: str = None):
    """Set user context for error tracking."""
    sentry_sdk.set_user({
        "id": user_id,
        "email": email
    })
