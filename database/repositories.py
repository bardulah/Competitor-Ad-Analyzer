"""Database operations and queries."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_, or_
from sqlalchemy.orm import Session
import logging

from database.models import (
    Advertisement, VisualAnalysis, MessagingAnalysis, Campaign,
    AnalysisCache, ScrapeCheckpoint, MonitoringJob, CostTracking,
    get_session
)

logger = logging.getLogger(__name__)


class AdRepository:
    """Repository for advertisement operations."""

    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()
        self._should_close = session is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close:
            self.session.close()

    def save_ad(self, ad_data: Dict[str, Any]) -> Advertisement:
        """Save or update an advertisement."""
        ad = self.session.query(Advertisement).filter_by(id=ad_data['id']).first()

        if ad:
            # Update existing
            for key, value in ad_data.items():
                if hasattr(ad, key):
                    setattr(ad, key, value)
        else:
            # Create new
            ad = Advertisement(**ad_data)
            self.session.add(ad)

        self.session.commit()
        self.session.refresh(ad)
        return ad

    def get_ad(self, ad_id: str) -> Optional[Advertisement]:
        """Get an advertisement by ID."""
        return self.session.query(Advertisement).filter_by(id=ad_id).first()

    def get_ads_by_advertiser(self, advertiser: str, limit: int = 100) -> List[Advertisement]:
        """Get all ads from a specific advertiser."""
        return self.session.query(Advertisement)\
            .filter_by(advertiser=advertiser)\
            .order_by(desc(Advertisement.scraped_at))\
            .limit(limit)\
            .all()

    def get_ads_by_platform(self, platform: str, limit: int = 100) -> List[Advertisement]:
        """Get ads from a specific platform."""
        return self.session.query(Advertisement)\
            .filter_by(platform=platform)\
            .order_by(desc(Advertisement.scraped_at))\
            .limit(limit)\
            .all()

    def get_recent_ads(self, days: int = 7, limit: int = 100) -> List[Advertisement]:
        """Get ads scraped in the last N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return self.session.query(Advertisement)\
            .filter(Advertisement.scraped_at >= cutoff)\
            .order_by(desc(Advertisement.scraped_at))\
            .limit(limit)\
            .all()

    def search_ads(self, query: str, limit: int = 100) -> List[Advertisement]:
        """Search ads by text in headline or body."""
        search_pattern = f"%{query}%"
        return self.session.query(Advertisement)\
            .filter(
                or_(
                    Advertisement.headline.like(search_pattern),
                    Advertisement.body_text.like(search_pattern),
                    Advertisement.advertiser.like(search_pattern)
                )
            )\
            .order_by(desc(Advertisement.scraped_at))\
            .limit(limit)\
            .all()

    def get_ads_without_analysis(self, analysis_type: str = 'visual', limit: int = 50) -> List[Advertisement]:
        """Get ads that haven't been analyzed yet."""
        if analysis_type == 'visual':
            return self.session.query(Advertisement)\
                .outerjoin(VisualAnalysis)\
                .filter(VisualAnalysis.id == None)\
                .filter(Advertisement.screenshot_path != None)\
                .limit(limit)\
                .all()
        elif analysis_type == 'messaging':
            return self.session.query(Advertisement)\
                .outerjoin(MessagingAnalysis)\
                .filter(MessagingAnalysis.id == None)\
                .limit(limit)\
                .all()
        return []

    def delete_old_ads(self, days: int = 90) -> int:
        """Delete ads older than N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        count = self.session.query(Advertisement)\
            .filter(Advertisement.scraped_at < cutoff)\
            .delete()
        self.session.commit()
        return count


class AnalysisRepository:
    """Repository for analysis operations."""

    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()
        self._should_close = session is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close:
            self.session.close()

    def save_visual_analysis(self, ad_id: str, analysis_data: Dict[str, Any]) -> VisualAnalysis:
        """Save visual analysis results."""
        analysis = self.session.query(VisualAnalysis).filter_by(ad_id=ad_id).first()

        if analysis:
            for key, value in analysis_data.items():
                if hasattr(analysis, key):
                    setattr(analysis, key, value)
        else:
            analysis_data['ad_id'] = ad_id
            analysis = VisualAnalysis(**analysis_data)
            self.session.add(analysis)

        self.session.commit()
        self.session.refresh(analysis)
        return analysis

    def save_messaging_analysis(self, ad_id: str, analysis_data: Dict[str, Any]) -> MessagingAnalysis:
        """Save messaging analysis results."""
        analysis = self.session.query(MessagingAnalysis).filter_by(ad_id=ad_id).first()

        if analysis:
            for key, value in analysis_data.items():
                if hasattr(analysis, key):
                    setattr(analysis, key, value)
        else:
            analysis_data['ad_id'] = ad_id
            analysis = MessagingAnalysis(**analysis_data)
            self.session.add(analysis)

        self.session.commit()
        self.session.refresh(analysis)
        return analysis

    def get_top_performing_ads(self, metric: str = 'quality_score', limit: int = 10) -> List[Advertisement]:
        """Get top-performing ads based on analysis metrics."""
        if metric == 'visual_quality':
            return self.session.query(Advertisement)\
                .join(VisualAnalysis)\
                .order_by(desc(VisualAnalysis.quality_score))\
                .limit(limit)\
                .all()
        elif metric == 'messaging_quality':
            return self.session.query(Advertisement)\
                .join(MessagingAnalysis)\
                .order_by(desc(MessagingAnalysis.quality_score))\
                .limit(limit)\
                .all()
        return []


class CacheRepository:
    """Repository for cache operations."""

    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()
        self._should_close = session is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close:
            self.session.close()

    def get_cached_analysis(self, content_hash: str, analysis_type: str) -> Optional[Dict[str, Any]]:
        """Get cached analysis result."""
        cache = self.session.query(AnalysisCache)\
            .filter_by(content_hash=content_hash, analysis_type=analysis_type)\
            .first()

        if cache:
            # Update access stats
            cache.accessed_at = datetime.utcnow()
            cache.access_count += 1
            self.session.commit()

            logger.info(f"Cache hit for {content_hash} (accessed {cache.access_count} times)")
            return cache.result

        return None

    def save_to_cache(self, content_hash: str, analysis_type: str,
                     result: Dict[str, Any], content_type: str,
                     model_used: str, cost: float):
        """Save analysis result to cache."""
        cache = AnalysisCache(
            content_hash=content_hash,
            content_type=content_type,
            analysis_type=analysis_type,
            result=result,
            model_used=model_used,
            cost=cost
        )
        self.session.add(cache)
        self.session.commit()
        logger.info(f"Saved to cache: {content_hash}")

    def clear_old_cache(self, days: int = 30) -> int:
        """Clear cache entries older than N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        count = self.session.query(AnalysisCache)\
            .filter(AnalysisCache.accessed_at < cutoff)\
            .delete()
        self.session.commit()
        return count


class CheckpointRepository:
    """Repository for checkpoint operations."""

    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()
        self._should_close = session is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close:
            self.session.close()

    def save_checkpoint(self, session_id: str, platform: str, query: str,
                       position: int, ad_id: Optional[str] = None,
                       status: str = 'scraped') -> ScrapeCheckpoint:
        """Save a scraping checkpoint."""
        checkpoint = ScrapeCheckpoint(
            session_id=session_id,
            platform=platform,
            query=query,
            position=position,
            ad_id=ad_id,
            status=status
        )
        self.session.add(checkpoint)
        self.session.commit()
        return checkpoint

    def get_last_checkpoint(self, session_id: str) -> Optional[ScrapeCheckpoint]:
        """Get the last checkpoint for a session."""
        return self.session.query(ScrapeCheckpoint)\
            .filter_by(session_id=session_id)\
            .order_by(desc(ScrapeCheckpoint.position))\
            .first()

    def update_checkpoint_status(self, checkpoint_id: int, status: str,
                                 error_message: Optional[str] = None):
        """Update checkpoint status."""
        checkpoint = self.session.query(ScrapeCheckpoint).filter_by(id=checkpoint_id).first()
        if checkpoint:
            checkpoint.status = status
            if error_message:
                checkpoint.error_message = error_message
            checkpoint.updated_at = datetime.utcnow()
            self.session.commit()


class CostRepository:
    """Repository for cost tracking operations."""

    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()
        self._should_close = session is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close:
            self.session.close()

    def track_cost(self, operation_type: str, model_used: str,
                  cost_usd: float, session_id: str,
                  tokens_used: int = 0, ad_id: Optional[str] = None):
        """Track API cost."""
        cost = CostTracking(
            operation_type=operation_type,
            model_used=model_used,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            session_id=session_id,
            ad_id=ad_id
        )
        self.session.add(cost)
        self.session.commit()

    def get_session_cost(self, session_id: str) -> float:
        """Get total cost for a session."""
        result = self.session.query(func.sum(CostTracking.cost_usd))\
            .filter_by(session_id=session_id)\
            .scalar()
        return result or 0.0

    def get_total_cost(self, days: Optional[int] = None) -> float:
        """Get total cost, optionally for last N days."""
        query = self.session.query(func.sum(CostTracking.cost_usd))

        if days:
            cutoff = datetime.utcnow() - timedelta(days=days)
            query = query.filter(CostTracking.timestamp >= cutoff)

        result = query.scalar()
        return result or 0.0

    def get_cost_breakdown(self, days: int = 30) -> Dict[str, float]:
        """Get cost breakdown by operation type."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        results = self.session.query(
            CostTracking.operation_type,
            func.sum(CostTracking.cost_usd)
        ).filter(CostTracking.timestamp >= cutoff)\
         .group_by(CostTracking.operation_type)\
         .all()

        return {op_type: float(cost) for op_type, cost in results}
