# backend/api/benchmarks.py
# VeriNews AI - Benchmarking & A/B Testing API Router

import time
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/benchmarks", tags=["benchmarks"])

_benchmark_cache: dict = {}

class BenchmarkRequest(BaseModel):
    dataset: str = "liar"
    n_samples: int = 50
    verifier: str = "fast"
    run_label: Optional[str] = None

class CompareRequest(BaseModel):
    run_id_a: str
    run_id_b: str

def _get_fast_verifier_fn():
    KEYWORD_RULES = [
        (["fake", "hoax", "debunked", "disproven", "false", "myth", "bleach", "microchip", "faked", "5g", "flat", "6000 years"], "FALSE", 94),
        (["confirmed", "approved", "announced", "published", "demonstrated", "verified", "studies show", "nasa", "fda", "who", "cdc"], "TRUE", 90),
    ]
    def fast_verify(claim: str) -> dict:
        c_lower = claim.lower()
        for keywords, verdict, conf in KEYWORD_RULES:
            if any(k in c_lower for k in keywords):
                return {"verdict": verdict, "confidence": conf}
        return {"verdict": "MISLEADING", "confidence": 70}
    return fast_verify

@router.get("/datasets/info")
def get_datasets_info():
    from services.benchmarker import get_dataset_info
    return get_dataset_info()

@router.get("/history")
def get_benchmark_history():
    try:
        import database
        history = database.get_benchmark_history()
        return {"runs": history, "count": len(history)}
    except Exception as e:
        return {"runs": list(_benchmark_cache.values()), "count": len(_benchmark_cache)}

@router.post("/run")
def run_benchmark_endpoint(req: BenchmarkRequest):
    from services.benchmarker import run_benchmark
    if req.dataset not in ["liar", "fever", "politifact"]:
        raise HTTPException(status_code=400, detail="Invalid dataset. Choose: liar, fever, politifact")
    
    n = max(10, min(500, req.n_samples))
    run_id = str(uuid.uuid4())[:8]
    
    if req.verifier == "local":
        try:
            from services.local_model import verify_claim_locally
            verifier_fn = lambda claim: verify_claim_locally(claim)
        except Exception:
            verifier_fn = _get_fast_verifier_fn()
    else:
        verifier_fn = _get_fast_verifier_fn()
    
    result = run_benchmark(dataset_name=req.dataset, n_samples=n, verifier_fn=verifier_fn, run_id=run_id)
    if req.run_label:
        result["label"] = req.run_label
    
    _benchmark_cache[run_id] = result
    try:
        import database
        database.save_benchmark_run(result)
    except Exception:
        pass
    return result

@router.post("/compare")
def compare_benchmark_runs(req: CompareRequest):
    from services.benchmarker import compare_ab
    run_a = _benchmark_cache.get(req.run_id_a)
    run_b = _benchmark_cache.get(req.run_id_b)
    if not run_a or not run_b:
        try:
            import database
            for r in database.get_benchmark_history():
                if r.get("run_id") == req.run_id_a: run_a = r
                if r.get("run_id") == req.run_id_b: run_b = r
        except Exception:
            pass
    if not run_a or not run_b:
        raise HTTPException(status_code=404, detail="One or both run IDs not found.")
    return compare_ab(run_a, run_b)
