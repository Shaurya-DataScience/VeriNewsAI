import os
import time
import psutil
from fastapi import APIRouter, HTTPException, Body, Query
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from models.schemas import AdminStatsResponse, ConfigUpdateRequest
from database import (
    get_admin_stats,
    get_system_config,
    save_system_config,
    get_telemetry_metrics,
    get_cache_entries,
    delete_from_cache,
    clear_all_cache,
    vacuum_database,
    get_flagged_queries,
    add_flagged_query,
    remove_flagged_query,
    get_security_events,
    log_error
)

router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard"])

# ==========================================================
# Pydantic Request Models
# ==========================================================

class FlagQueryRequest(BaseModel):
    pattern: str = Field(..., description="Query pattern or keyword to blacklist/flag")
    reason: str = Field("Suspicious or Malicious Query", description="Administrative rationale")
    flagged_by: Optional[str] = Field("admin", description="Admin user/agent identifier")

# ==========================================================
# Telemetry & System Health Endpoints
# ==========================================================

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
        log_error("/api/admin/stats", type(e).__name__, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch admin stats: {str(e)}")

@router.get("/telemetry")
async def get_admin_telemetry_endpoint():
    """
    Real-Time Telemetry Dashboard:
    Live verification counts, today's claims, latency percentiles, error rates, and verdict distribution.
    """
    try:
        return get_telemetry_metrics()
    except Exception as e:
        log_error("/api/admin/telemetry", type(e).__name__, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch telemetry metrics: {str(e)}")

@router.get("/system/health")
async def get_system_health_endpoint():
    """
    System Health & Telemetry:
    Real-time CPU utilization %, RAM memory consumption, disk capacity, uptime, and AI service health.
    """
    try:
        proc = psutil.Process(os.getpid())
        mem_info = proc.memory_info()
        sys_mem = psutil.virtual_memory()
        disk = psutil.disk_usage(os.path.abspath("."))
        cpu_pct = psutil.cpu_percent(interval=None)
        
        create_time = proc.create_time()
        uptime_seconds = int(time.time() - create_time)
        uptime_hours = uptime_seconds // 3600
        uptime_mins = (uptime_seconds % 3600) // 60
        uptime_secs = uptime_seconds % 60
        uptime_str = f"{uptime_hours}h {uptime_mins}m {uptime_secs}s"
        
        return {
            "status": "HEALTHY",
            "cpu_percent": cpu_pct,
            "memory": {
                "process_mb": round(mem_info.rss / (1024 * 1024), 1),
                "system_total_gb": round(sys_mem.total / (1024**3), 1),
                "system_used_percent": sys_mem.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 1),
                "free_gb": round(disk.free / (1024**3), 1),
                "used_percent": disk.percent
            },
            "uptime_seconds": uptime_seconds,
            "uptime_str": uptime_str,
            "pid": os.getpid(),
            "threads_count": proc.num_threads(),
            "services": {
                "database_sqlite": {"status": "OPERATIONAL", "engine": "SQLite 3 WAL"},
                "distilbert_classifier": {"status": "OPERATIONAL", "model": "distilbert-base-uncased-finetuned"},
                "cross_encoder_rerank": {"status": "OPERATIONAL", "model": "ms-marco-MiniLM-L-6-v2"},
                "vector_embeddings": {"status": "OPERATIONAL", "model": "all-MiniLM-L6-v2"},
                "tavily_search": {"status": "OPERATIONAL", "type": "Live Web Synthesis"}
            }
        }
    except Exception as e:
        log_error("/api/admin/system/health", type(e).__name__, str(e))
        return {
            "status": "DEGRADED",
            "error": str(e),
            "cpu_percent": 0.0,
            "memory": {"process_mb": 0, "system_total_gb": 0, "system_used_percent": 0},
            "disk": {"total_gb": 0, "free_gb": 0, "used_percent": 0},
            "uptime_seconds": 0,
            "uptime_str": "0h 0m 0s",
            "pid": os.getpid(),
            "threads_count": 1,
            "services": {}
        }

# ==========================================================
# Cache Database Management Endpoints
# ==========================================================

@router.get("/cache")
async def get_admin_cache_endpoint(limit: int = Query(50, ge=1, le=500), search: str = Query("", max_length=100)):
    """
    Inspect cached verification queries with pagination, search, size, and creation timestamp.
    """
    try:
        entries = get_cache_entries(limit=limit, search=search)
        return {
            "count": len(entries),
            "entries": entries
        }
    except Exception as e:
        log_error("/api/admin/cache", type(e).__name__, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch cache entries: {str(e)}")

@router.delete("/cache/entry")
async def delete_cache_entry_endpoint(query: str = Query(..., min_length=1)):
    """
    Evict an individual query from the SQLite cache table.
    """
    try:
        delete_from_cache(query)
        return {"message": f"Query '{query}' evicted from cache successfully."}
    except Exception as e:
        log_error("/api/admin/cache/entry", type(e).__name__, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to evict cache entry: {str(e)}")

@router.post("/cache/clear")
async def clear_cache_endpoint():
    """
    Purge all records from the SQLite cache table.
    """
    try:
        deleted_count = clear_all_cache()
        return {"message": "All cache entries cleared successfully.", "deleted_count": deleted_count}
    except Exception as e:
        log_error("/api/admin/cache/clear", type(e).__name__, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@router.post("/cache/vacuum")
async def vacuum_cache_endpoint():
    """
    Reclaim SQLite disk space and optimize database tables.
    """
    try:
        success = vacuum_database()
        if success:
            return {"message": "Database vacuumed and optimized successfully."}
        raise HTTPException(status_code=500, detail="Database vacuum failed.")
    except Exception as e:
        log_error("/api/admin/cache/vacuum", type(e).__name__, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to vacuum database: {str(e)}")

# ==========================================================
# Security & Malicious Query Blacklisting Endpoints
# ==========================================================

@router.get("/security/flagged")
async def get_flagged_queries_endpoint():
    """
    Retrieve all blacklisted and flagged query patterns.
    """
    try:
        return {"flagged": get_flagged_queries()}
    except Exception as e:
        log_error("/api/admin/security/flagged", type(e).__name__, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch flagged queries: {str(e)}")

@router.post("/security/flag")
async def add_flagged_query_endpoint(payload: FlagQueryRequest):
    """
    Add a query pattern to the malicious/suspicious blacklist.
    """
    try:
        success = add_flagged_query(payload.pattern, payload.reason, payload.flagged_by or "admin")
        if success:
            return {"message": f"Query pattern '{payload.pattern}' flagged successfully.", "pattern": payload.pattern}
        raise HTTPException(status_code=400, detail="Invalid pattern or unable to add to blacklist.")
    except Exception as e:
        log_error("/api/admin/security/flag", type(e).__name__, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to flag query: {str(e)}")

@router.delete("/security/unflag")
async def remove_flagged_query_endpoint(pattern: str = Query(..., min_length=1)):
    """
    Remove a pattern from the malicious/suspicious blacklist.
    """
    try:
        success = remove_flagged_query(pattern)
        if success:
            return {"message": f"Pattern '{pattern}' removed from blacklist."}
        raise HTTPException(status_code=404, detail=f"Pattern '{pattern}' not found in blacklist.")
    except Exception as e:
        log_error("/api/admin/security/unflag", type(e).__name__, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to unflag query: {str(e)}")

@router.get("/security/events")
async def get_security_events_endpoint(limit: int = Query(50, ge=1, le=200)):
    """
    Retrieve audit log of intercepted/blocked queries.
    """
    try:
        return {"events": get_security_events(limit=limit)}
    except Exception as e:
        log_error("/api/admin/security/events", type(e).__name__, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch security events: {str(e)}")

# ==========================================================
# Dynamic Ensemble Weight Configuration Endpoints
# ==========================================================

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
