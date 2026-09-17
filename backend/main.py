import os
import time
import json
import hashlib
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

import database
from services.search import search_news
from services.verifier import verify_claim, extract_key_evidence
from services.similarity_search import get_similar_claims, register_verified_claim, find_dataset_match
from services.hallucination_detector import detect_hallucinations
from services.monitor import add_claim_to_monitoring, get_monitored_claims_list
from services.summarizer import stream_summary
from services.hybrid_verifier import run_hybrid_verification

# ==========================================================
# Startup Environment Safeguards
# ==========================================================

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv()

START_TIME = time.time()
TAVILY_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_KEY:
    print("[WARNING] TAVILY_API_KEY is not set. Real-time web news search will fall back to mock search mode.")

# ==========================================================
# Global Sessions for Streaming
# ==========================================================
SEARCH_SESSIONS = {}

# ==========================================================
# FastAPI
# ==========================================================

app = FastAPI(
    title="VeriNews AI API",
    version="7.0.0",
    description="Enterprise AI Fact Verification & Neural Grounding Platform"
)

# ==========================================================
# Production CORS Configuration (Supports Vercel, Cloud Hosting & Localhost)
# ==========================================================

raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
if not raw_origins or raw_origins.strip() == "*":
    cors_origins = ["*"]
    cors_credentials = False
else:
    cors_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
    cors_credentials = True

from api.verification import router as verification_router
from api.admin import router as admin_router
from api.analytics import router as analytics_router
from api.enterprise import router as enterprise_router
from api.benchmarks import router as benchmarks_router

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

from starlette.requests import Request

@app.middleware("http")
async def telemetry_error_logging_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        if response.status_code >= 500:
            database.log_error(str(request.url.path), f"HTTP_{response.status_code}", f"Server returned status {response.status_code}")
        return response
    except Exception as exc:
        database.log_error(str(request.url.path), type(exc).__name__, str(exc))
        raise exc

# Register Phase 2 & Enterprise Routers
app.include_router(verification_router)
app.include_router(admin_router)
app.include_router(analytics_router)
app.include_router(enterprise_router)
app.include_router(benchmarks_router)

# ==========================================================
# Home Endpoint
# ==========================================================

@app.get("/")
def home():
    return {
        "status": "running",
        "project": "VeriNews AI Enterprise",
        "version": "6.0.0",
        "message": "Backend is running successfully 🚀"
    }

# ==========================================================
# Offline Mode & Local Phi-3-mini Endpoints
# ==========================================================

@app.get("/api/offline-mode")
def offline_mode_status():
    """Returns whether local AI model is available for offline inference."""
    try:
        from services.local_model import get_model_status
        status = get_model_status()
        return {
            "offline_capable": status.get("is_downloaded", False),
            "model_loaded": status.get("is_loaded", False),
            "model_name": status.get("model_short", "Phi-3-mini-4k"),
            "tavily_configured": bool(os.getenv("TAVILY_API_KEY"))
        }
    except Exception:
        return {
            "offline_capable": False,
            "model_loaded": False,
            "model_name": "Phi-3-mini-4k",
            "tavily_configured": bool(os.getenv("TAVILY_API_KEY"))
        }

@app.post("/api/local-model/verify")
async def local_model_verify(payload: dict):
    """Verify a claim using the local Phi-3-mini model (offline, no internet needed)."""
    claim = payload.get("claim", "").strip()
    if not claim:
        raise HTTPException(status_code=400, detail="Claim cannot be empty.")
    try:
        from services.local_model import verify_claim_locally
        result = verify_claim_locally(claim)
        return result
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Local model unavailable: {str(e)}")

@app.get("/api/local-model/status")
def local_model_status():
    """Get Phi-3-mini download status and memory usage."""
    try:
        from services.local_model import get_model_status
        return get_model_status()
    except Exception as e:
        return {"error": str(e), "is_downloaded": False, "is_loaded": False}

@app.post("/api/local-model/download")
async def download_local_model():
    """Trigger Phi-3-mini model download. Returns download status."""
    try:
        from services.local_model import download_model_with_progress
        results = []
        for progress_json in download_model_with_progress():
            results.append(progress_json)
        return {"status": "complete", "steps": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

# ==========================================================
# Real-Time Search Suggestions & Autocomplete Endpoint
# ==========================================================

@app.get("/api/search/suggestions")
def search_suggestions_endpoint(q: str = "", limit: int = 6):
    """
    Sub-10ms prefix autocomplete matching against verified claims and cache.
    """
    if not q or len(q.strip()) < 2:
        return {"query": q, "suggestions": []}
    
    suggestions = database.get_search_suggestions(q.strip(), limit=min(12, max(1, limit)))
    return {
        "query": q,
        "count": len(suggestions),
        "suggestions": suggestions
    }

# ==========================================================
# Search Endpoint (v6.0 Enterprise Pipeline with Cache TTL)
# ==========================================================

@app.get("/search")
async def search(query: str, force_refresh: bool = False):
    """Unified Search Endpoint routing to Phase 2 Hybrid Verification Pipeline with Cache Invalidation."""
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query parameter cannot be empty.")

    clean_query = query.strip()
    try:
        # If force_refresh requested, bust cache
        if force_refresh:
            database.delete_from_cache(clean_query)
        else:
            # Check Cache (valid within 24h TTL)
            cached_result = database.get_from_cache(clean_query, max_age_hours=24)
            if cached_result and "summary" in cached_result and cached_result["summary"]:
                cached_result["cached"] = True
                cached_result["similar_claims"] = get_similar_claims(clean_query, top_k=5)
                return cached_result

        result = await run_hybrid_verification(clean_query)
        
        # Save session for summary streaming
        SEARCH_SESSIONS[result["search_id"]] = {
            "query": clean_query,
            "articles": result.get("supporting_sources", []) + result.get("neutral_sources", [])
        }
        return result
    except Exception as e:
        print(f"VeriNews AI Search Error: {e}")
        raise HTTPException(status_code=500, detail=f"Unable to verify the claim: {str(e)}")

@app.post("/api/cache/purge")
def purge_cache_endpoint(max_age_hours: int = 24):
    """Purge expired cache entries beyond max_age_hours."""
    purged = database.purge_expired_cache(max_age_hours=max_age_hours)
    return {
        "status": "success",
        "purged_records": purged,
        "max_age_hours": max_age_hours
    }


# ==========================================================
# Streaming Summary & Hallucination Detection Endpoint
# ==========================================================

@app.get("/stream_summary/{search_id}")
@app.get("/stream-summary/{search_id}")
def stream_summary_endpoint(search_id: str):
    if search_id not in SEARCH_SESSIONS:
        def empty_generator():
            yield f"data: {json.dumps({'token': '[DONE]'})}\n\n"
        return StreamingResponse(empty_generator(), media_type="text/event-stream")
        
    session = SEARCH_SESSIONS.pop(search_id)
    query = session["query"]
    articles = session["articles"]

    def event_generator():
        full_summary = ""
        try:
            for token in stream_summary(articles):
                full_summary += token
                yield f"data: {json.dumps({'token': token})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
        # Run Hallucination Detection (Feature 2)
        hallucination_report = detect_hallucinations(full_summary, articles)
        yield f"data: {json.dumps({'hallucination_report': hallucination_report})}\n\n"
        yield f"data: {json.dumps({'token': '[DONE]'})}\n\n"
        
        # Update Cache with final summary and hallucination report
        cached_result = database.get_from_cache(query)
        if cached_result:
            cached_result["summary"] = full_summary
            cached_result["hallucination_report"] = hallucination_report
            database.save_to_cache(query, cached_result)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ==========================================================
# v6.0 Enterprise Feature Endpoints
# ==========================================================

@app.get("/similar")
def get_similar_endpoint(claim: str):
    """Feature 1: Vector similarity search over past claims."""
    if not claim:
        return []
    return get_similar_claims(claim, top_k=5)

@app.post("/monitor")
def monitor_claim_endpoint(payload: dict):
    """Feature 7: Register a claim for live background monitoring."""
    claim = payload.get("claim", "")
    verdict = payload.get("verdict", "UNVERIFIED")
    confidence = payload.get("confidence", 0)
    return add_claim_to_monitoring(claim, verdict, confidence)

@app.get("/api/admin/datasets")
def get_datasets_telemetry_endpoint():
    """Step 15: Telemetry endpoint returning dataset claim counts and label distributions."""
    return database.get_dataset_statistics()

@app.post("/api/admin/datasets/stream-ingest")
def stream_ingest_dataset_endpoint(payload: dict):
    """Option C: Admin endpoint to trigger automated dataset streaming ingestion."""
    from training.stream_huggingface_ingestion import stream_and_ingest_dataset
    dataset = payload.get("dataset", "fever")
    limit = int(payload.get("limit", 5000))
    batch = int(payload.get("batch", 500))
    return stream_and_ingest_dataset(dataset_name=dataset, limit=limit, batch_size=batch)

@app.get("/monitor/history")
def get_monitor_history():
    """Feature 7: Retrieve all monitored claims and verification history."""
    return get_monitored_claims_list()

# ==========================================================
# Production Health & Uptime Endpoints
# ==========================================================

@app.get("/health")
@app.get("/healthz")
@app.get("/api/health")
def health():
    db_status = "connected"
    try:
        conn = database.get_connection()
        conn.execute("SELECT 1")
        conn.close()
    except Exception:
        db_status = "degraded"

    uptime_seconds = round(time.time() - START_TIME, 2)
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "project": "VeriNews AI Enterprise",
        "version": "6.0.0",
        "uptime_seconds": uptime_seconds,
        "database": db_status,
        "tavily_api_configured": bool(os.getenv("TAVILY_API_KEY"))
    }

# ==========================================================
# Frontend Static Asset Serving (Production & Docker Deployments)
# ==========================================================
from fastapi.staticfiles import StaticFiles

frontend_candidates = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "frontend")),
    "/app/frontend"
]
for candidate in frontend_candidates:
    if os.path.isdir(candidate) and os.path.isfile(os.path.join(candidate, "index.html")):
        app.mount("/", StaticFiles(directory=candidate, html=True), name="frontend")
        break
