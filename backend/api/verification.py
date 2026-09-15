from fastapi import APIRouter, HTTPException, Query, Body
from typing import Dict, Any, Optional

from models.schemas import ClaimVerifyRequest, HybridVerificationResponse
from services.hybrid_verifier import run_hybrid_verification

router = APIRouter(prefix="/api", tags=["Verification Engine"])

@router.post("/verify", response_model=HybridVerificationResponse)
async def verify_claim_endpoint(payload: ClaimVerifyRequest):
    """
    Intelligent Hybrid Verification Endpoint:
    Processes news claim using Local Vector Search -> Cross Encoder Rerank -> Short-Circuit or Tavily Search -> DistilBERT Classifier -> Weighted Ensemble.
    """
    if not payload.claim or not payload.claim.strip():
        raise HTTPException(status_code=400, detail="Claim text cannot be empty.")
    
    try:
        result = await run_hybrid_verification(payload.claim.strip())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hybrid verification failed: {str(e)}")

@router.get("/search")
async def search_claim_endpoint(query: str = Query(..., description="Claim text or query")):
    """GET endpoint compatible with frontend search requests."""
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query parameter cannot be empty.")
    
    try:
        result = await run_hybrid_verification(query.strip())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
