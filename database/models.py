"""Database models for storing ad data and analysis results."""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.pool import StaticPool
import os

from config import DATA_DIR

Base = declarative_base()


class Advertisement(Base):
    """Model for storing advertisement data."""

    __tablename__ = 'advertisements'

    id = Column(String, primary_key=True)
    platform = Column(String, nullable=False, index=True)
    advertiser = Column(String, index=True)
    headline = Column(Text)
    body_text = Column(Text)
    cta = Column(String)

    # Media
    image_url = Column(String)
    video_url = Column(String)
    screenshot_path = Column(String)

    # Dates and metrics
    start_date = Column(String)
    end_date = Column(String)
    impressions = Column(Integer)
    spend_estimate = Column(Float)

    # Metadata
    targeting = Column(JSON)
    page_url = Column(String)
    scraped_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Additional metadata
    country = Column(String)
    language = Column(String)
    is_active = Column(Boolean, default=True)

    # Relationships
    visual_analysis = relationship("VisualAnalysis", back_populates="ad", uselist=False, cascade="all, delete-orphan")
    messaging_analysis = relationship("MessagingAnalysis", back_populates="ad", uselist=False, cascade="all, delete-orphan")
    checkpoints = relationship("ScrapeCheckpoint", back_populates="ad", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'platform': self.platform,
            'advertiser': self.advertiser,
            'headline': self.headline,
            'body_text': self.body_text,
            'cta': self.cta,
            'image_url': self.image_url,
            'video_url': self.video_url,
            'screenshot_path': self.screenshot_path,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'impressions': self.impressions,
            'spend_estimate': self.spend_estimate,
            'targeting': self.targeting,
            'page_url': self.page_url,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'country': self.country,
            'language': self.language,
            'is_active': self.is_active
        }


class VisualAnalysis(Base):
    """Model for storing visual analysis results."""

    __tablename__ = 'visual_analyses'

    id = Column(Integer, primary_key=True)
    ad_id = Column(String, ForeignKey('advertisements.id'), unique=True, nullable=False)

    # Analysis results
    visual_composition = Column(Text)
    imagery = Column(Text)
    messaging = Column(Text)
    design_patterns = Column(Text)
    effectiveness = Column(Text)
    insights = Column(Text)
    raw_analysis = Column(Text)

    # Structured data
    colors = Column(JSON)  # List of detected colors
    quality_score = Column(Float)  # 0-10 rating

    # Metadata
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    model_used = Column(String)
    cost = Column(Float)  # Cost of analysis in USD

    # Cache info
    image_hash = Column(String, index=True)

    # Relationship
    ad = relationship("Advertisement", back_populates="visual_analysis")

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'ad_id': self.ad_id,
            'visual_composition': self.visual_composition,
            'imagery': self.imagery,
            'messaging': self.messaging,
            'design_patterns': self.design_patterns,
            'effectiveness': self.effectiveness,
            'insights': self.insights,
            'raw_analysis': self.raw_analysis,
            'colors': self.colors,
            'quality_score': self.quality_score,
            'analyzed_at': self.analyzed_at.isoformat() if self.analyzed_at else None,
            'model_used': self.model_used,
            'cost': self.cost
        }


class MessagingAnalysis(Base):
    """Model for storing messaging analysis results."""

    __tablename__ = 'messaging_analyses'

    id = Column(Integer, primary_key=True)
    ad_id = Column(String, ForeignKey('advertisements.id'), unique=True, nullable=False)

    # Metrics
    character_count = Column(Integer)
    word_count = Column(Integer)
    sentence_count = Column(Integer)
    readability_score = Column(String)

    # Analysis
    power_words = Column(JSON)
    cta_type = Column(String)
    cta_has_urgency = Column(Boolean)
    emotional_appeal = Column(String)
    deep_analysis = Column(Text)

    # Quality
    quality_score = Column(Float)  # 0-10 rating

    # Metadata
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    model_used = Column(String)
    cost = Column(Float)

    # Relationship
    ad = relationship("Advertisement", back_populates="messaging_analysis")

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'ad_id': self.ad_id,
            'character_count': self.character_count,
            'word_count': self.word_count,
            'sentence_count': self.sentence_count,
            'readability_score': self.readability_score,
            'power_words': self.power_words,
            'cta_type': self.cta_type,
            'cta_has_urgency': self.cta_has_urgency,
            'emotional_appeal': self.emotional_appeal,
            'deep_analysis': self.deep_analysis,
            'quality_score': self.quality_score,
            'analyzed_at': self.analyzed_at.isoformat() if self.analyzed_at else None,
            'model_used': self.model_used,
            'cost': self.cost
        }


class Campaign(Base):
    """Model for tracking competitor campaigns."""

    __tablename__ = 'campaigns'

    id = Column(Integer, primary_key=True)
    advertiser = Column(String, nullable=False, index=True)
    campaign_name = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)

    # Analytics
    total_ads = Column(Integer, default=0)
    total_impressions = Column(Integer)
    total_spend = Column(Float)

    # Patterns detected
    primary_theme = Column(String)
    color_palette = Column(JSON)
    messaging_strategy = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AnalysisCache(Base):
    """Model for caching expensive analysis results."""

    __tablename__ = 'analysis_cache'

    id = Column(Integer, primary_key=True)
    content_hash = Column(String, unique=True, nullable=False, index=True)
    content_type = Column(String)  # 'image', 'text', 'video'

    # Analysis results
    analysis_type = Column(String)  # 'visual', 'messaging'
    result = Column(JSON)

    # Metadata
    model_used = Column(String)
    cost = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    accessed_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    access_count = Column(Integer, default=0)


class ScrapeCheckpoint(Base):
    """Model for checkpointing scraping progress."""

    __tablename__ = 'scrape_checkpoints'

    id = Column(Integer, primary_key=True)
    session_id = Column(String, nullable=False, index=True)
    ad_id = Column(String, ForeignKey('advertisements.id'))

    platform = Column(String)
    query = Column(String)
    position = Column(Integer)  # Which ad number in the sequence

    status = Column(String)  # 'pending', 'scraped', 'analyzed', 'completed', 'failed'
    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    ad = relationship("Advertisement", back_populates="checkpoints")


class MonitoringJob(Base):
    """Model for scheduled monitoring jobs."""

    __tablename__ = 'monitoring_jobs'

    id = Column(Integer, primary_key=True)
    job_name = Column(String, nullable=False)
    advertiser = Column(String, nullable=False, index=True)
    platform = Column(String)

    # Schedule
    schedule_type = Column(String)  # 'daily', 'weekly', 'monthly'
    schedule_time = Column(String)  # e.g., '09:00'

    # Alert settings
    alert_on_new_ads = Column(Boolean, default=True)
    alert_threshold = Column(Integer)  # Number of new ads to trigger alert
    alert_email = Column(String)
    alert_webhook = Column(String)

    # Status
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime)
    next_run = Column(DateTime)
    last_ads_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CostTracking(Base):
    """Model for tracking API costs."""

    __tablename__ = 'cost_tracking'

    id = Column(Integer, primary_key=True)
    operation_type = Column(String)  # 'scrape', 'visual_analysis', 'messaging_analysis', etc.
    model_used = Column(String)

    # Costs
    tokens_used = Column(Integer)
    cost_usd = Column(Float)

    # Context
    session_id = Column(String, index=True)
    ad_id = Column(String)

    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


# Database session management
class Database:
    """Database connection and session management."""

    def __init__(self, db_url=None):
        """Initialize database connection.

        Args:
            db_url: Database URL. If None, uses SQLite in data directory.
        """
        if db_url is None:
            db_path = DATA_DIR / 'competitor_ads.db'
            db_url = f'sqlite:///{db_path}'

        # Create engine
        if 'sqlite' in db_url:
            # SQLite-specific settings
            self.engine = create_engine(
                db_url,
                connect_args={'check_same_thread': False},
                poolclass=StaticPool
            )
        else:
            self.engine = create_engine(db_url)

        # Create all tables
        Base.metadata.create_all(self.engine)

        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_session(self):
        """Get a database session."""
        return self.SessionLocal()

    def close(self):
        """Close database connection."""
        self.engine.dispose()


# Global database instance
_db_instance = None


def get_db():
    """Get global database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


def get_session():
    """Get a database session."""
    db = get_db()
    return db.get_session()
