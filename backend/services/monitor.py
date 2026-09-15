# ============================================================
# VeriNews AI - Live Claim Monitoring Service v6.0
# Automated Background Verification & Change Tracker
# ============================================================

import hashlib
from datetime import datetime
import database

def add_claim_to_monitoring(claim: str, verdict: str = "UNVERIFIED", confidence: int = 0) -> dict:
    """Register a claim for live monitoring."""
    if not claim or not claim.strip():
        return {"status": "error", "message": "Claim text cannot be empty."}

    claim_text = claim.strip()
    claim_id = hashlib.md5(claim_text.lower().encode()).hexdigest()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    success = database.save_monitored_claim(claim_id, claim_text, verdict, confidence, timestamp)
    if success:
        return {
            "status": "success",
            "message": f"Claim registered for live monitoring.",
            "claim_id": claim_id,
            "claim": claim_text,
            "last_checked": timestamp,
            "verdict": verdict,
            "confidence": confidence
        }
    else:
        return {"status": "error", "message": "Failed to save monitored claim."}

def get_monitored_claims_list() -> list:
    """Retrieve all claims currently under live monitoring."""
    return database.get_monitored_claims()
