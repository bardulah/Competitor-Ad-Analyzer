"""FastAPI server for web-based access to the ad analyzer."""

import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio

from database import AdRepository, AnalysisRepository, CostRepository
from scrapers.async_scraper import scrape_multiple_platforms
from analyzers.cached_analyzer import CachedVisualAnalyzer, CachedMessagingAnalyzer
from analyzers.trend_analyzer import TrendAnalyzer
from analyzers.competitive_benchmarking import CompetitiveBenchmarking
from utils.cost_estimator import CostEstimator

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Competitor Ad Analyzer API",
    description="API for scraping and analyzing competitor advertisements",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ScrapeRequest(BaseModel):
    query: str
    limit: int = 50
    platforms: Optional[List[str]] = None
    country: str = "US"

class ScrapeResponse(BaseModel):
    session_id: str
    status: str
    message: str
    ads_scraped: int

class AnalysisRequest(BaseModel):
    advertiser: Optional[str] = None
    ad_ids: Optional[List[str]] = None
    analyze_visuals: bool = True
    analyze_messaging: bool = True
    use_cache: bool = True

class CostEstimateRequest(BaseModel):
    num_ads: int
    platforms: Optional[List[str]] = None
    analyze_visual: bool = True
    analyze_messaging: bool = True

class TrendRequest(BaseModel):
    advertiser: str
    months: int = 6

class BenchmarkRequest(BaseModel):
    competitors: List[str]
    months: int = 3


# Routes

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Competitor Ad Analyzer API",
        "version": "2.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_ads(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """Scrape ads from ad libraries.

    This endpoint starts a background scraping task.
    """
    try:
        import uuid
        session_id = str(uuid.uuid4())

        # Add scraping task to background
        background_tasks.add_task(
            run_scraping_task,
            session_id,
            request.query,
            request.limit,
            request.platforms
        )

        return ScrapeResponse(
            session_id=session_id,
            status="started",
            message=f"Scraping task started for query: {request.query}",
            ads_scraped=0
        )

    except Exception as e:
        logger.error(f"Error starting scrape: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_scraping_task(session_id: str, query: str, limit: int, platforms: Optional[List[str]]):
    """Background task for scraping."""
    try:
        logger.info(f"Starting scraping task {session_id}")
        results = await scrape_multiple_platforms(query, limit, platforms)

        total_ads = sum(len(ads) for ads in results.values())
        logger.info(f"Scraping task {session_id} completed: {total_ads} ads")

    except Exception as e:
        logger.error(f"Error in scraping task {session_id}: {e}")

@app.get("/ads")
async def get_ads(
    advertiser: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = Query(default=100, le=1000)
):
    """Get scraped ads with optional filtering."""
    try:
        with AdRepository() as ad_repo:
            if advertiser:
                ads = ad_repo.get_ads_by_advertiser(advertiser, limit)
            elif platform:
                ads = ad_repo.get_ads_by_platform(platform, limit)
            else:
                ads = ad_repo.get_recent_ads(days=30, limit=limit)

            return {
                "total": len(ads),
                "ads": [ad.to_dict() for ad in ads]
            }

    except Exception as e:
        logger.error(f"Error retrieving ads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ads/{ad_id}")
async def get_ad(ad_id: str):
    """Get a specific ad by ID."""
    try:
        with AdRepository() as ad_repo:
            ad = ad_repo.get_ad(ad_id)

            if not ad:
                raise HTTPException(status_code=404, detail="Ad not found")

            ad_dict = ad.to_dict()

            # Include analyses if available
            if ad.visual_analysis:
                ad_dict['visual_analysis'] = ad.visual_analysis.to_dict()
            if ad.messaging_analysis:
                ad_dict['messaging_analysis'] = ad.messaging_analysis.to_dict()

            return ad_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving ad {ad_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_ads(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Analyze scraped ads."""
    try:
        import uuid
        session_id = str(uuid.uuid4())

        # Add analysis task to background
        background_tasks.add_task(
            run_analysis_task,
            session_id,
            request.advertiser,
            request.ad_ids,
            request.analyze_visuals,
            request.analyze_messaging,
            request.use_cache
        )

        return {
            "session_id": session_id,
            "status": "started",
            "message": "Analysis task started"
        }

    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_analysis_task(session_id: str, advertiser: Optional[str],
                            ad_ids: Optional[List[str]], analyze_visuals: bool,
                            analyze_messaging: bool, use_cache: bool):
    """Background task for analysis."""
    try:
        logger.info(f"Starting analysis task {session_id}")

        # Get ads to analyze
        with AdRepository() as ad_repo:
            if ad_ids:
                ads = [ad_repo.get_ad(ad_id) for ad_id in ad_ids]
                ads = [ad for ad in ads if ad is not None]
            elif advertiser:
                ads = ad_repo.get_ads_by_advertiser(advertiser, limit=100)
            else:
                ads = ad_repo.get_recent_ads(days=7, limit=50)

        logger.info(f"Analyzing {len(ads)} ads")

        # Analyze
        if analyze_visuals:
            visual_analyzer = CachedVisualAnalyzer(session_id=session_id)
            for ad in ads:
                if ad.screenshot_path:
                    await asyncio.to_thread(
                        visual_analyzer.analyze_image,
                        ad.screenshot_path,
                        use_cache
                    )

        if analyze_messaging:
            messaging_analyzer = CachedMessagingAnalyzer(session_id=session_id)
            for ad in ads:
                text = f"{ad.headline or ''} {ad.body_text or ''}"
                if text.strip():
                    await asyncio.to_thread(
                        messaging_analyzer.analyze_text,
                        text,
                        use_cache
                    )

        logger.info(f"Analysis task {session_id} completed")

    except Exception as e:
        logger.error(f"Error in analysis task {session_id}: {e}")

@app.post("/estimate-cost")
async def estimate_cost(request: CostEstimateRequest):
    """Estimate cost for a scraping and analysis operation."""
    try:
        estimator = CostEstimator()

        estimate = estimator.estimate_scraping_cost(
            num_ads=request.num_ads,
            platforms=request.platforms,
            analyze_visual=request.analyze_visual,
            analyze_messaging=request.analyze_messaging
        )

        return estimate

    except Exception as e:
        logger.error(f"Error estimating cost: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cost-report")
async def get_cost_report(days: int = Query(default=30, le=365)):
    """Get cost report for specified period."""
    try:
        estimator = CostEstimator()
        report = estimator.get_cost_report(days=days)

        return report

    except Exception as e:
        logger.error(f"Error generating cost report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trends")
async def analyze_trends(request: TrendRequest):
    """Analyze trends for an advertiser."""
    try:
        analyzer = TrendAnalyzer()
        trends = analyzer.analyze_advertiser_trends(
            request.advertiser,
            request.months
        )

        return trends

    except Exception as e:
        logger.error(f"Error analyzing trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/benchmark")
async def benchmark_competitors(request: BenchmarkRequest):
    """Benchmark multiple competitors."""
    try:
        benchmarking = CompetitiveBenchmarking()
        benchmark = benchmarking.benchmark_competitors(
            request.competitors,
            request.months
        )

        return benchmark

    except Exception as e:
        logger.error(f"Error benchmarking: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/advertisers")
async def list_advertisers():
    """List all tracked advertisers."""
    try:
        with AdRepository() as ad_repo:
            session = ad_repo.session
            from sqlalchemy import distinct
            from database.models import Advertisement

            advertisers = session.query(distinct(Advertisement.advertiser))\
                .filter(Advertisement.advertiser != None)\
                .all()

            advertiser_list = [a[0] for a in advertisers if a[0]]

            return {
                "total": len(advertiser_list),
                "advertisers": advertiser_list
            }

    except Exception as e:
        logger.error(f"Error listing advertisers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_statistics():
    """Get overall statistics."""
    try:
        with AdRepository() as ad_repo:
            session = ad_repo.session
            from database.models import Advertisement, VisualAnalysis, MessagingAnalysis
            from sqlalchemy import func

            total_ads = session.query(func.count(Advertisement.id)).scalar()
            total_analyzed_visual = session.query(func.count(VisualAnalysis.id)).scalar()
            total_analyzed_messaging = session.query(func.count(MessagingAnalysis.id)).scalar()

            # Get recent activity
            recent_ads = session.query(func.count(Advertisement.id))\
                .filter(Advertisement.scraped_at >= func.date('now', '-7 days'))\
                .scalar()

            return {
                "total_ads": total_ads,
                "analyzed_visual": total_analyzed_visual,
                "analyzed_messaging": total_analyzed_messaging,
                "recent_ads_7days": recent_ads
            }

    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
