from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any

from models.schemas import AdminStatsResponse, ConfigUpdateRequest
from database import get_admin_stats, get_system_config, save_system_config

router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard"])

@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats_endpoint():
    """
    Admin Dashboard Statistics:
    Database size, embedding count, cache hit ratio, dataset stats, and search latency.
    """
    try:
        stats = get_admin_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch admin stats: {str(e)}")

@router.get("/config")
async def get_system_config_endpoint():
    """Get current dynamic verification weights and vector similarity threshold."""
    return get_system_config()

@router.post("/config")
async def update_system_config_endpoint(payload: ConfigUpdateRequest):
    """
    Update dynamic verification weights & vector similarity threshold.
    """
    current = get_system_config()
    if payload.weights is not None:
        current["weights"] = payload.weights.dict()
    if payload.similarity_threshold is not None:
        current["similarity_threshold"] = payload.similarity_threshold

    success = save_system_config(current)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save configuration update.")

    return {"message": "Configuration updated successfully", "config": current}
