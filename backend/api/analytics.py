from fastapi import APIRouter, HTTPException
from models.schemas import AnalyticsSummaryResponse
from database import get_analytics_summary

router = APIRouter(prefix="/api/analytics", tags=["Public Analytics Dashboard"])

@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary_endpoint():
    """
    Public Analytics Overview:
    Total verified claims, True vs False breakdown, confidence distribution, and trending misinformation.
    """
    try:
        data = get_analytics_summary()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analytics summary: {str(e)}")
