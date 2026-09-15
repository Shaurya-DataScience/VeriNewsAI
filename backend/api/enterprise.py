import os
from typing import Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from services.multimodal import process_multimodal_verification
from services.article_scanner import deep_scan_article
from services.hybrid_verifier import run_hybrid_verification
from services.misinformation_radar import get_trending_misinformation_alerts
from services.bias_radar import get_domain_bias_info

router = APIRouter(prefix="/api/enterprise", tags=["Enterprise Intelligence"])

class ArticleScanRequest(BaseModel):
    url: Optional[str] = None
    article_text: Optional[str] = None

class DomainQueryRequest(BaseModel):
    domain: str

# ==============================================================================
# 1. Multimodal Verification (Image & Meme Fact-Checking)
# ==============================================================================
@router.post("/multimodal/verify-image")
async def verify_image_endpoint(file: UploadFile = File(...)):
    """
    Accepts uploaded news screenshot, meme, or infographic.
    Extracts text via OCR, runs Error Level Analysis (ELA) for tampering,
    and executes hybrid fact-checking on the extracted claim.
    """
    if not file:
        raise HTTPException(status_code=400, detail="No image file provided.")

    try:
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Empty image file received.")

        # Run Multimodal Inspection
        multimodal_result = process_multimodal_verification(contents, filename=file.filename)
        candidate_claim = multimodal_result.get("candidate_claim", "")

        # Run Hybrid Claim Verification
        verification_result = await run_hybrid_verification(candidate_claim)

        return {
            "status": "SUCCESS",
            "filename": file.filename,
            "extracted_text": multimodal_result["extracted_text"],
            "image_forensics": multimodal_result["image_forensics"],
            "ai_generation_analysis": multimodal_result["ai_generation_analysis"],
            "verification": verification_result
        }
    except Exception as e:
        print(f"[EnterpriseAPI] Multimodal error: {e}")
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")

# ==============================================================================
# 2. Full Article & URL Deep-Scan ("Truth Index")
# ==============================================================================
@router.post("/article/deep-scan")
async def deep_scan_endpoint(req: ArticleScanRequest):
    """
    Ingests full article URL or text document, decomposes into atomic factual assertions,
    verifies each claim in parallel, and computes an aggregate Article Truth Index (0-100%).
    """
    target = (req.url or req.article_text or "").strip()
    if not target:
        raise HTTPException(status_code=400, detail="Must provide either 'url' or 'article_text'.")

    try:
        scan_report = await deep_scan_article(target, run_hybrid_verification)
        return scan_report
    except Exception as e:
        print(f"[EnterpriseAPI] Article scan error: {e}")
        raise HTTPException(status_code=500, detail=f"Deep-scan failed: {str(e)}")

# ==============================================================================
# 3. Real-Time Misinformation Radar & Watchdog
# ==============================================================================
@router.get("/radar/trending")
def get_radar_trending_endpoint():
    """
    Returns real-time trending viral misinformation radar alerts.
    """
    try:
        alerts = get_trending_misinformation_alerts()
        return {
            "status": "LIVE",
            "alerts_count": len(alerts),
            "alerts": alerts
        }
    except Exception as e:
        print(f"[EnterpriseAPI] Radar fetch error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch radar alerts.")

# ==============================================================================
# 4. Source Bias & Reliability Resolver
# ==============================================================================
@router.get("/bias/domain-info")
def get_bias_domain_info_endpoint(domain: str):
    """
    Returns media bias spectrum and factuality grading for a given domain.
    """
    if not domain:
        raise HTTPException(status_code=400, detail="Domain parameter required.")
    return get_domain_bias_info(domain)

# ==============================================================================
# 5. AI Stylometry & Synthetic Text Forensics Detector
# ==============================================================================
from services.ai_forensics import analyze_text_forensics

class ForensicsRequest(BaseModel):
    text: str

@router.post("/forensics/ai-detector")
def ai_forensics_endpoint(req: ForensicsRequest):
    """
    Evaluates Perplexity, Burstiness, Entropy, and repetitive synthetic LLM phrasing
    to determine Human vs AI authorship probability.
    """
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text payload required for forensic inspection.")
    try:
        return analyze_text_forensics(req.text)
    except Exception as e:
        print(f"[EnterpriseAPI] AI Forensics error: {e}")
        raise HTTPException(status_code=500, detail=f"Forensics analysis failed: {str(e)}")

# ==============================================================================
# 6. Parallel Multi-Claim & Debate Verifier
# ==============================================================================
from services.batch_verifier import decompose_speech_claims, execute_parallel_batch_verification

class BatchVerifyRequest(BaseModel):
    speech_text: Optional[str] = None
    claims: Optional[list[str]] = None

@router.post("/batch/verify-claims")
async def batch_verify_endpoint(req: BatchVerifyRequest):
    """
    Accepts speech transcript or list of claims, verifies them concurrently in parallel,
    and returns a composite veracity scorecard.
    """
    claims_to_verify = []
    if req.claims and len(req.claims) > 0:
        claims_to_verify = [c.strip() for c in req.claims if c.strip()]
    elif req.speech_text and req.speech_text.strip():
        claims_to_verify = decompose_speech_claims(req.speech_text)

    if not claims_to_verify:
        raise HTTPException(status_code=400, detail="Provide either 'claims' list or 'speech_text'.")

    try:
        scorecard = await execute_parallel_batch_verification(claims_to_verify, run_hybrid_verification)
        return scorecard
    except Exception as e:
        print(f"[EnterpriseAPI] Batch verify error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch verification failed: {str(e)}")

# ==============================================================================
# 7. Document & Speech Transcript Upload Parser
# ==============================================================================
@router.post("/batch/upload-doc")
async def upload_document_endpoint(file: UploadFile = File(...)):
    """
    Uploads a .txt, .pdf, or transcript file and parses it into discrete claims.
    """
    if not file:
        raise HTTPException(status_code=400, detail="File required.")

    try:
        contents = await file.read()
        text_content = ""

        if file.filename.lower().endswith(".pdf"):
            try:
                import pypdf
                import io
                reader = pypdf.PdfReader(io.BytesIO(contents))
                text_content = " ".join([page.extract_text() or "" for page in reader.pages])
            except Exception as pe:
                print(f"[EnterpriseAPI] pypdf parsing error: {pe}")
                text_content = contents.decode("utf-8", errors="ignore")
        else:
            text_content = contents.decode("utf-8", errors="ignore")

        extracted_claims = decompose_speech_claims(text_content)
        return {
            "filename": file.filename,
            "extracted_text_snippet": text_content[:400] + "...",
            "claims_count": len(extracted_claims),
            "claims": extracted_claims
        }
    except Exception as e:
        print(f"[EnterpriseAPI] Doc upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Document parsing failed: {str(e)}")
