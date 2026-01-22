"""
Analytics API endpoints for CEP Machine
Production-ready analytics endpoints with caching and error handling
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from backend.analytics.analytics_engine import analytics_engine
from backend.cache.redis_cache import cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

class ProspectData(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    converted: Optional[bool] = False
    days_to_convert: Optional[int] = None
    pitch_type: Optional[str] = None
    revenue: Optional[float] = None
    employee_count: Optional[int] = None
    growth_rate: Optional[float] = None
    engagement_score: Optional[float] = None
    email_opens: Optional[int] = None
    website_visits: Optional[int] = None
    meetings_scheduled: Optional[int] = None
    last_contact_days: Optional[int] = None
    created_at: Optional[str] = None

class OutreachData(BaseModel):
    id: Optional[str] = None
    prospect_id: Optional[str] = None
    channel: Optional[str] = None
    sent_at: Optional[str] = None
    responded: Optional[bool] = False
    response_time: Optional[int] = None

class FinancialData(BaseModel):
    id: Optional[str] = None
    amount: float
    category: Optional[str] = None
    source: Optional[str] = None
    date: Optional[str] = None

@router.post("/conversion")
async def analyze_conversion(data: List[ProspectData]):
    """Analyze prospect conversion patterns"""
    try:
        # Convert to dict list
        data_dicts = [d.dict() for d in data]
        
        # Check cache
        cache_key = f"analytics:conversion:{len(data_dicts)}"
        cached_result = await cache.get(cache_key)
        if cached_result:
            return JSONResponse(cached_result)
        
        # Run analysis
        result = await analytics_engine.analyze_prospect_conversion(data_dicts)
        
        # Cache result
        await cache.set(cache_key, result, ttl=900)  # 15 minutes
        
        return JSONResponse(result)
    
    except Exception as e:
        logger.error(f"Conversion analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/cluster")
async def cluster_prospects(
    data: List[ProspectData],
    n_clusters: int = Query(default=5, ge=2, le=10)
):
    """Cluster prospects for targeted marketing"""
    try:
        data_dicts = [d.dict() for d in data]
        result = await analytics_engine.cluster_prospects(data_dicts, n_clusters)
        return JSONResponse(result)
    
    except Exception as e:
        logger.error(f"Clustering error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Clustering failed: {str(e)}")

@router.post("/predict-conversions")
async def predict_conversions(
    data: List[ProspectData],
    top_n: int = Query(default=10, ge=1, le=100)
):
    """Predict prospects most likely to convert"""
    try:
        data_dicts = [d.dict() for d in data]
        result = await analytics_engine.predict_likely_conversions(data_dicts, top_n)
        return JSONResponse(result)
    
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.post("/performance-report")
async def generate_performance_report(
    data: List[ProspectData],
    period: str = Query(default="30d", regex="^[0-9]+d$")
):
    """Generate comprehensive performance report"""
    try:
        data_dicts = [d.dict() for d in data]
        result = await analytics_engine.generate_performance_report(data_dicts, period)
        return JSONResponse(result)
    
    except Exception as e:
        logger.error(f"Report generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

@router.post("/outreach-effectiveness")
async def analyze_outreach(data: List[OutreachData]):
    """Analyze outreach campaign effectiveness"""
    try:
        data_dicts = [d.dict() for d in data]
        result = await analytics_engine.analyze_outreach_effectiveness(data_dicts)
        return JSONResponse(result)
    
    except Exception as e:
        logger.error(f"Outreach analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Outreach analysis failed: {str(e)}")

@router.post("/roi")
async def calculate_roi(
    revenue_data: List[FinancialData],
    cost_data: List[FinancialData]
):
    """Calculate ROI and financial metrics"""
    try:
        revenue_dicts = [d.dict() for d in revenue_data]
        cost_dicts = [d.dict() for d in cost_data]
        result = await analytics_engine.calculate_roi(revenue_dicts, cost_dicts)
        return JSONResponse(result)
    
    except Exception as e:
        logger.error(f"ROI calculation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ROI calculation failed: {str(e)}")

@router.get("/summary")
async def get_analytics_summary():
    """Get analytics summary with mock data for dashboard"""
    try:
        # Return summary data for dashboard
        summary = {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "total_prospects": 1247,
                "conversion_rate": 18.5,
                "total_revenue": 125000,
                "active_agents": 3,
                "avg_response_time": 0.45,
                "tool_success_rate": 96.5
            },
            "trends": {
                "prospects_change": 12,
                "conversion_change": 8,
                "revenue_change": 15
            },
            "top_sources": [
                {"name": "Search", "count": 435, "conversion_rate": 22.5},
                {"name": "Outreach", "count": 349, "conversion_rate": 18.2},
                {"name": "Referral", "count": 274, "conversion_rate": 25.1},
                {"name": "Direct", "count": 189, "conversion_rate": 15.8}
            ],
            "recent_conversions": [
                {"company": "ABC Corp", "industry": "Technology", "value": 15000},
                {"company": "XYZ Industries", "industry": "Manufacturing", "value": 22000},
                {"company": "123 Services", "industry": "Healthcare", "value": 18500}
            ]
        }
        
        return JSONResponse(summary)
    
    except Exception as e:
        logger.error(f"Summary error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")

@router.get("/health")
async def analytics_health():
    """Analytics service health check"""
    return {
        "status": "healthy",
        "service": "analytics",
        "timestamp": datetime.utcnow().isoformat()
    }
