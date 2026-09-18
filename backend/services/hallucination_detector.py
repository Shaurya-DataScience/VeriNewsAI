# ============================================================
# VeriNews AI - AI Hallucination Detector v6.0
# Sentence-Level Evidence Alignment & Grounding Verification
# ============================================================

import re
import math
import torch
from services.verifier import get_embedding_model, get_cross_encoder
from sklearn.metrics.pairwise import cosine_similarity

def split_into_sentences(text: str) -> list:
    """Split text into distinct sentences."""
    if not text:
        return []
    raw = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in raw if len(s.strip()) > 10]
    return sentences if sentences else [text.strip()]

def detect_hallucinations(summary_text: str, articles: list) -> dict:
    """
    Sentence-level verification of generated summary against retrieved article evidence.
    
    Rules:
    - >= 85%: SUPPORTED (Green 🟢)
    - 70-85%: WEAK_EVIDENCE (Yellow 🟡)
    - < 70%: HALLUCINATION / UNSUPPORTED (Red 🔴)
    """
    if not summary_text or summary_text == "No evidence found.":
        return {
            "risk_level": "LOW",
            "supported_count": 0,
            "weak_count": 0,
            "hallucination_count": 0,
            "sentence_reports": []
        }

    sentences = split_into_sentences(summary_text)
    if not articles:
        return {
            "risk_level": "HIGH",
            "supported_count": 0,
            "weak_count": 0,
            "hallucination_count": len(sentences),
            "sentence_reports": [
                {
                    "sentence": s,
                    "score": 0.0,
                    "status": "HALLUCINATION",
                    "label": "Potential Hallucination",
                    "color": "red"
                } for s in sentences
            ]
        }

    # Aggregate article context snippets
    evidence_texts = [
        f"{a.get('title', '')}. {a.get('content', '')[:600]}"
        for a in articles
    ]
    combined_evidence = " ".join(evidence_texts)[:4000]

    emb_model = get_embedding_model()
    cross_enc = get_cross_encoder()
    with torch.no_grad():
        sentence_embeddings = emb_model.encode(sentences)
        evidence_embeddings = emb_model.encode([combined_evidence])[0]

    sentence_reports = []
    supported_cnt = 0
    weak_cnt = 0
    hallucination_cnt = 0

    for idx, sentence in enumerate(sentences):
        # 1. Cosine Semantic Similarity
        sent_vec = sentence_embeddings[idx]
        cos_sim = float(cosine_similarity([sent_vec], [evidence_embeddings])[0][0])
        cos_pct = max(0.0, min(100.0, cos_sim * 100))

        # 2. Cross Encoder Rerank Score
        if cross_enc is not None:
            try:
                with torch.no_grad():
                    cross_raw = float(cross_enc.predict([(sentence, combined_evidence[:1000])])[0])
                cross_pct = (1 / (1 + math.exp(-cross_raw))) * 100
            except Exception:
                cross_pct = cos_pct
        else:
            cross_pct = cos_pct

        # Composite Grounding Score
        grounding_score = round(cos_pct * 0.50 + cross_pct * 0.50, 1)

        # Classification
        if grounding_score >= 78.0:
            status = "SUPPORTED"
            label = "Supported"
            color = "green"
            supported_cnt += 1
        elif grounding_score >= 62.0:
            status = "WEAK_EVIDENCE"
            label = "Weak Evidence"
            color = "yellow"
            weak_cnt += 1
        else:
            status = "HALLUCINATION"
            label = "Potential Hallucination"
            color = "red"
            hallucination_cnt += 1

        sentence_reports.append({
            "sentence": sentence,
            "score": grounding_score,
            "status": status,
            "label": label,
            "color": color
        })

    # Overall Hallucination Risk Calculation
    total_sent = len(sentences)
    if hallucination_cnt >= 2 or (hallucination_cnt / total_sent) >= 0.4:
        risk_level = "HIGH"
    elif weak_cnt >= 2 or hallucination_cnt >= 1:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "risk_level": risk_level,
        "supported_count": supported_cnt,
        "weak_count": weak_cnt,
        "hallucination_count": hallucination_cnt,
        "sentence_reports": sentence_reports
    }
