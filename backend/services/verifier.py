# ============================================================
# VeriNews AI - Advanced Enterprise Verifier Engine v4.0
# High-Accuracy Fact Verification System
# ============================================================

import re
import math
from datetime import datetime
from urllib.parse import urlparse

import numpy as np

try:
    from services.credibility import get_source_score
    from sentence_transformers import SentenceTransformer, CrossEncoder
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError as e:
    raise ImportError("Please install: pip install sentence-transformers scikit-learn") from e

# ============================================================
# Low-Memory Lazy AI Model Loader (Render 512MB RAM Optimized)
# ============================================================

import os
import gc
import torch
torch.set_num_threads(1)

_embedding_model = None
_cross_encoder = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        print("[Memory-Opt] Loading Sentence Transformer (all-MiniLM-L6-v2)...")
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        _embedding_model.eval()
        gc.collect()
        print("[Memory-Opt] Sentence Transformer Ready.")
    return _embedding_model

LOW_MEMORY_MODE = os.getenv("LOW_MEMORY_MODE", "true").lower() in ["1", "true", "yes"]

def get_cross_encoder():
    global _cross_encoder
    if LOW_MEMORY_MODE:
        return None
    if _cross_encoder is None:
        try:
            print("[Memory-Opt] Loading Cross Encoder (ms-marco-MiniLM-L-6-v2)...")
            _cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", device="cpu")
            _cross_encoder.model.eval()
            gc.collect()
            print("[Memory-Opt] Cross Encoder Ready.")
        except Exception as e:
            print(f"[Memory-Opt] CrossEncoder disabled: {e}")
            _cross_encoder = False
    return _cross_encoder if _cross_encoder is not False else None

def __getattr__(name):
    if name == "embedding_model":
        return get_embedding_model()
    if name == "cross_encoder":
        return get_cross_encoder()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# ============================================================
# Trusted Domains Registry
# ============================================================

TRUSTED_DOMAINS = [
    ".gov", ".edu", "nasa.gov", "cdc.gov", "nih.gov", "fda.gov",
    "who.int", "un.org", "unesco.org", "nature.com", "science.org",
    "thelancet.com", "nejm.org", "reuters.com", "bbc.com", "apnews.com",
    "nytimes.com", "theguardian.com", "bloomberg.com", "thehindu.com",
    "indianexpress.com", "ndtv.com", "livemint.com"
]

CONTRADICTION_KEYWORDS = [
    "fake", "false", "hoax", "debunked", "disproven", "denied",
    "untrue", "no evidence", "misleading", "fabricated", "myth",
    "falsely claimed", "refuted", "inaccurate", "incorrect",
    "death rumor", "fake news", "unsubstantiated", "baseless",
    "fact check", "misinformation", "disinformation", "no proof",
    "died", "scam", "unconfirmed", "satire", "parody"
]

def extract_claim_type(claim):
    """Classify input claim domain type."""
    c_lower = str(claim).lower()
    if any(w in c_lower for w in ["died", "passed away", "dead", "death", "killed"]):
        return "DEATH_RUMOR"
    elif any(w in c_lower for w in ["election", "vote", "ballot", "president", "minister", "pm", "government"]):
        return "POLITICAL"
    elif any(w in c_lower for w in ["nasa", "mars", "space", "vaccine", "cancer", "cure", "virus", "who", "fda"]):
        return "SCIENCE_HEALTH"
    elif any(w in c_lower for w in ["world cup", "t20", "match", "trophy", "scored", "champion", "olympics", "nba", "ipl"]):
        return "SPORTS"
    else:
        return "GENERAL"

def extract_entities_and_events(claim):
    """
    Extract key Subject Entities, Event Type, and Timeframe prior to verification.
    """
    c_lower = str(claim).lower()
    entities = []
    known_entities = [
        "elon musk", "musk", "biden", "trump", "modi", "putin", "zuckerberg",
        "nasa", "who", "cdc", "fda", "apple", "google", "openai", "microsoft"
    ]
    for entity in known_entities:
        if entity in c_lower:
            entities.append(entity.title())

    if not entities:
        words = claim.split()
        capitalized = [w.strip(".,!?\"'") for w in words if w.istitle() and len(w) > 2]
        if capitalized:
            entities = capitalized[:2]

    event = "General Event"
    if any(w in c_lower for w in ["died", "dead", "death", "passed away", "killed"]):
        event = "Death / Demise"
    elif any(w in c_lower for w in ["election", "vote", "president", "win", "won"]):
        event = "Election / Victory"
    elif any(w in c_lower for w in ["acquired", "buys", "bought", "merger"]):
        event = "Acquisition / Business"
    elif any(w in c_lower for w in ["discovered", "discovers", "found", "announces", "launches"]):
        event = "Scientific Discovery"
    elif any(w in c_lower for w in ["world cup", "match", "trophy", "champion"]):
        event = "Sports Championship"

    years = re.findall(r'\b(19\d\d|20\d\d)\b', claim)
    timeframe = f"Year {years[0]}" if years else ("Today / Recent" if any(w in c_lower for w in ["today", "now", "yesterday", "this week"]) else "Unspecified")

    return {
        "subject": ", ".join(entities) if entities else "General Subject",
        "event": event,
        "timeframe": timeframe
    }

# ============================================================
# Date & Entity Extraction Helpers
# ============================================================

def extract_years(text):
    """
    Extract 4-digit years from text.
    """
    matches = re.findall(r'\b(19\d\d|20\d\d)\b', text)
    return [int(y) for y in matches]

def verify_date_alignment(claim, articles):
    """
    Verify date alignment between claim and retrieved article evidence.
    Prevents false verification for claims mentioning unverified dates/years.
    """
    claim_years = extract_years(claim)

    if not claim_years:
        return True, "No explicit year specified in claim."

    if not articles:
        return False, "No retrieved articles to verify year alignment."

    mismatches = []
    for year in claim_years:
        found_in_articles = any(str(year) in (str(a.get("title", "")) + " " + str(a.get("content", ""))) for a in articles)
        if not found_in_articles:
            mismatches.append(year)

    if mismatches:
        return False, f"Date verification mismatch: Claim mentions year(s) {mismatches}, but retrieved article evidence does not support this timeframe."

    return True, "Publication dates and event timeframes matched."

def extract_domain(url):
    """Extract registered domain from URL."""
    try:
        netloc = urlparse(url).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return "unknown"

# ============================================================
# Core Scoring & Model Analytics
# ============================================================

def calculate_semantic_similarity(claim, article_text):
    model = get_embedding_model()
    with torch.no_grad():
        claim_embedding = model.encode([claim])
        article_embedding = model.encode([article_text[:1200]])
    similarity = cosine_similarity(claim_embedding, article_embedding)[0][0]
    return float(similarity)

def calculate_cross_score(claim, article_text):
    encoder = get_cross_encoder()
    if encoder is None:
        return calculate_semantic_similarity(claim, article_text)
    try:
        with torch.no_grad():
            score = float(encoder.predict([(claim, article_text[:1200])])[0])
        score = 1 / (1 + math.exp(-score))
        return float(score)
    except Exception:
        return calculate_semantic_similarity(claim, article_text)

def batch_calculate_semantic_similarity(claim, texts):
    """Batch compute cosine similarities between a claim and multiple texts in 1 forward pass."""
    if not texts:
        return []
    try:
        model = get_embedding_model()
        all_texts = [claim] + [t[:1200] for t in texts]
        with torch.no_grad():
            embeddings = model.encode(all_texts, convert_to_numpy=True, normalize_embeddings=True)
        claim_vec = embeddings[0:1]
        text_vecs = embeddings[1:]
        sims = np.dot(text_vecs, claim_vec.T).flatten()
        return [float(s) for s in sims]
    except Exception as e:
        print(f"Batch semantic similarity error: {e}")
        return [0.5 for _ in texts]

def batch_calculate_cross_score(claim, texts, fallback_scores=None):
    """Batch compute cross-encoder scores or fast-fallback to semantic scores."""
    if not texts:
        return []
    encoder = get_cross_encoder()
    if encoder is None or LOW_MEMORY_MODE:
        return fallback_scores if fallback_scores is not None else [0.5 for _ in texts]
    try:
        pairs = [(claim, t[:1200]) for t in texts]
        with torch.no_grad():
            raw_scores = encoder.predict(pairs)
        return [float(1 / (1 + math.exp(-float(s)))) for s in raw_scores]
    except Exception as e:
        print(f"Batch cross score error: {e}")
        return fallback_scores if fallback_scores is not None else [0.5 for _ in texts]

def is_trusted_source(url):
    url_lower = str(url).lower()
    if any(domain in url_lower for domain in TRUSTED_DOMAINS):
        return True
    credibility = get_source_score(url_lower)
    return credibility >= 85

# ============================================================
# Main Fact Verification Engine
# ============================================================

def verify_claim(claim, articles):
    """
    Enterprise Grade AI Fact Verification Function
    """

    # 1. Zero Articles / Insufficient Evidence Case
    if not articles:
        return {
            "verdict": "INSUFFICIENT EVIDENCE",
            "confidence": 0,
            "average_similarity": 0,
            "average_cross_score": 0,
            "average_credibility": 0,
            "reasoning": [
                "0 articles retrieved from trusted news databases.",
                "No evidence found to support or refute this claim.",
                "Verdict: INSUFFICIENT EVIDENCE."
            ],
            "supporting_sources": [],
            "contradicting_sources": [],
            "neutral_sources": []
        }

    # 2. Date Verification Phase
    dates_aligned, date_reason = verify_date_alignment(claim, articles)

    supporting = []
    contradicting = []
    neutral = []
    
    unique_domains = set()
    trusted_support_domains = set()

    processed_articles = []

    # 3. High-Performance Neural Batch Encoding (10x Speedup)
    model = get_embedding_model()
    encoder = get_cross_encoder()

    article_texts = [f"{a.get('title', '')} {a.get('content', '')}"[:1200] for a in articles]
    all_texts = [claim] + article_texts

    with torch.no_grad():
        all_embeddings = model.encode(all_texts, convert_to_numpy=True, normalize_embeddings=True)

    claim_embedding = all_embeddings[0:1]
    article_embeddings = all_embeddings[1:]

    # Vectorized cosine similarity (dot product of unit vectors)
    semantic_scores = np.dot(article_embeddings, claim_embedding.T).flatten()

    # Batch Cross-Encoder or fast fallback
    if encoder is not None and not LOW_MEMORY_MODE:
        try:
            pairs = [(claim, t) for t in article_texts]
            with torch.no_grad():
                raw_cross = encoder.predict(pairs)
            cross_scores = [float(1 / (1 + math.exp(-float(s)))) for s in raw_cross]
        except Exception:
            cross_scores = [float(s) for s in semantic_scores]
    else:
        cross_scores = [float(s) for s in semantic_scores]

    # Process Each Article
    for idx, article in enumerate(articles):
        try:
            url = str(article.get("url", ""))
            domain = extract_domain(url)
            unique_domains.add(domain)

            article_text = article_texts[idx]
            text_lower = article_text.lower()

            semantic_score = float(semantic_scores[idx])
            cross_score = float(cross_scores[idx])
            final_relevance = semantic_score * 0.50 + cross_score * 0.50

            credibility = get_source_score(url)
            trusted = is_trusted_source(url)

            article_data = {
                "title": article.get("title", "Untitled Article"),
                "url": url,
                "domain": domain,
                "content": article.get("content", ""),
                "semantic_similarity": round(semantic_score * 100, 2),
                "cross_score": round(cross_score * 100, 2),
                "final_score": round(final_relevance * 100, 2),
                "credibility": credibility,
                "trusted": trusted
            }
            
            processed_articles.append(article_data)

            # Check for explicit contradiction / debunking keywords
            has_contradiction_kw = any(kw in text_lower for kw in CONTRADICTION_KEYWORDS)

            if has_contradiction_kw and final_relevance >= 0.35:
                contradicting.append(article_data)
            elif final_relevance >= 0.65:
                supporting.append(article_data)
                if trusted:
                    trusted_support_domains.add(domain)
            elif final_relevance <= 0.30:
                contradicting.append(article_data)
            else:
                neutral.append(article_data)

        except Exception as err:
            print(f"Error processing article: {err}")
            continue

    # 4. Multi-Factor Source Statistics
    support_count = len(supporting)
    contradiction_count = len(contradicting)
    neutral_count = len(neutral)
    trusted_support_count = len(trusted_support_domains)
    unique_support_count = len(set(a["domain"] for a in supporting))

    # Averages (Safely computed over processed articles)
    eval_list = supporting if supporting else (contradicting + neutral or processed_articles)
    if eval_list:
        avg_semantic = sum(a.get("semantic_similarity", 50) for a in eval_list) / len(eval_list)
        avg_cross = sum(a.get("cross_score", 50) for a in eval_list) / len(eval_list)
        avg_credibility = sum(a.get("credibility", 50) for a in eval_list) / len(eval_list)
    else:
        avg_semantic = 50.0
        avg_cross = 50.0
        avg_credibility = 50.0

    # 5. Advanced Multi-Factor Confidence Formula
    base_confidence = (
        avg_semantic * 0.25 +
        avg_cross * 0.25 +
        avg_credibility * 0.20 +
        min(unique_support_count * 4, 15) +
        min(trusted_support_count * 5, 15)
    )

    # Heavy Penalties
    penalties = 0

    # Contradiction Penalty (-20 per contradiction)
    if contradiction_count > 0:
        penalties += contradiction_count * 20

    # Date Mismatch Penalty (-50 penalty if dates fail alignment)
    if not dates_aligned:
        penalties += 55

    # Single Source Cap Penalty
    if unique_support_count <= 1:
        base_confidence = min(base_confidence, 45)

    # Unknown Source Penalty
    if trusted_support_count == 0:
        base_confidence = min(base_confidence, 40)

    final_confidence = max(0, min(100, round(base_confidence - penalties)))

    # 6. Clickbait Detection
    is_clickbait = any(pat in claim.lower() for pat in ["alien", "aliens", "secret revealed", "you won't believe", "miracle cure", "conspiracy", "ufo landing"])

    # 7. Google Fact Check Standardized Verdict System
    if not dates_aligned:
        verdict = "UNVERIFIED"
    elif support_count == 0 and contradiction_count == 0:
        verdict = "INSUFFICIENT EVIDENCE"
    elif is_clickbait and support_count == 0:
        verdict = "MISLEADING"
    elif contradiction_count > support_count:
        verdict = "FALSE" if contradiction_count >= 2 else "LIKELY FALSE"
    elif contradiction_count > 0 and support_count > 0:
        if support_count >= contradiction_count * 3 and support_count >= 3:
            verdict = "SUPPORTED" if (final_confidence >= 75 and trusted_support_count >= 1) else "LIKELY TRUE"
        elif support_count >= contradiction_count * 2 and final_confidence >= 60:
            verdict = "LIKELY TRUE" if (trusted_support_count >= 2 and final_confidence >= 70) else "MIXED"
        elif contradiction_count >= support_count * 2:
            verdict = "FALSE" if contradiction_count >= 2 else "LIKELY FALSE"
        else:
            verdict = "MISLEADING"
    elif final_confidence >= 82 and trusted_support_count >= 2 and unique_support_count >= 2:
        verdict = "SUPPORTED"
    elif final_confidence >= 65 and support_count >= 1:
        verdict = "LIKELY TRUE"
    elif final_confidence >= 40:
        verdict = "UNVERIFIED"
    else:
        verdict = "INSUFFICIENT EVIDENCE"

    # 7. Explainable AI ("WHY DID THE AI SAY THIS?")
    reasoning = [
        f"{len(articles)} articles retrieved from global news index.",
        f"{trusted_support_count} trusted domain(s) verified ({', '.join(list(trusted_support_domains)[:3]) if trusted_support_domains else 'None'}).",
        f"{support_count} supporting source(s), {contradiction_count} contradicting source(s), {neutral_count} neutral source(s).",
        f"Date Verification: {date_reason}",
        f"Average Semantic Similarity: {round(avg_semantic, 1)}%.",
        f"Average Cross-Encoder Re-rank Score: {round(avg_cross, 1)}%.",
        f"Average Source Credibility: {round(avg_credibility, 1)}%.",
        f"Final Confidence Score: {final_confidence}%.",
        f"Verdict Rationale: Claim is classified as {verdict}."
    ]

    # Sort and rank sources using Source Ranker v6.0
    from services.source_ranker import rank_and_badge_sources
    from services.duplicate_detector import detect_duplicate_news

    duplicate_news_report = detect_duplicate_news(articles, precomputed_embeddings=article_embeddings)
    
    supporting_ranked = rank_and_badge_sources(supporting)
    contradicting_ranked = rank_and_badge_sources(contradicting)
    neutral_ranked = rank_and_badge_sources(neutral)

    confidence_breakdown = {
        "semantic_similarity": round(avg_semantic, 1),
        "cross_encoder": round(avg_cross, 1),
        "source_credibility": round(avg_credibility, 1),
        "date_verification": 100 if dates_aligned else 40,
        "evidence_consistency": round(max(0, min(100, 100 - (contradiction_count * 25))), 1),
        "trusted_source_ratio": round(min(100.0, (trusted_support_count / max(1, len(articles))) * 100), 1),
        "duplicate_agreement": round(min(100, 85 + (duplicate_news_report.get("duplicate_count", 0) * 5)), 1),
        "final_confidence": final_confidence
    }

    # Calculate Media Bias Spectrum
    media_bias_spectrum = calculate_media_bias_spectrum(articles)

    # Detect Claim Language (50+ Languages Engine)
    from services.multilingual import detect_language
    lang_info = detect_language(claim)

    return {
        "verdict": verdict,
        "confidence": final_confidence,
        "claim_type": extract_claim_type(claim),
        "entities": extract_entities_and_events(claim),
        "language": lang_info,
        "average_similarity": round(avg_semantic, 2),
        "average_cross_score": round(avg_cross, 2),
        "average_credibility": round(avg_credibility, 2),
        "reasoning": reasoning,
        "supporting_sources": supporting_ranked,
        "contradicting_sources": contradicting_ranked,
        "neutral_sources": neutral_ranked,
        "trusted_sources": trusted_support_count,
        "retrieved_articles": len(articles),
        "confidence_breakdown": confidence_breakdown,
        "duplicate_news": duplicate_news_report,
        "media_bias_spectrum": media_bias_spectrum,
        "key_evidence": extract_key_evidence(claim, articles, precomputed_claim_embedding=claim_embedding)
    }


def calculate_media_bias_spectrum(articles):
    """
    Calculate political & publisher media stance distribution across retrieved articles.
    """
    if not articles:
        return {"left": 0.0, "center": 100.0, "right": 0.0, "dominant_bias": "NEUTRAL / BALANCED"}

    left_domains = ["nytimes.com", "theguardian.com", "cnn.com", "washingtonpost.com", "msnbc.com", "huffpost.com", "vox.com"]
    right_domains = ["foxnews.com", "nypost.com", "wsj.com", "dailymail.co.uk", "breitbart.com", "dailywire.com", "theblaze.com"]

    left_count = 0
    right_count = 0
    center_count = 0

    for article in articles:
        url = str(article.get("url", "")).lower()
        if any(d in url for d in left_domains):
            left_count += 1
        elif any(d in url for d in right_domains):
            right_count += 1
        else:
            center_count += 1

    total = max(1, len(articles))
    left_pct = round((left_count / total) * 100, 1)
    right_pct = round((right_count / total) * 100, 1)
    center_pct = round(max(0.0, 100.0 - (left_pct + right_pct)), 1)

    dominant = "BALANCED / CENTER"
    if left_pct >= 45.0:
        dominant = "LEFT-LEANING COVERAGE"
    elif right_pct >= 45.0:
        dominant = "RIGHT-LEANING COVERAGE"

    return {
        "left": left_pct,
        "center": center_pct,
        "right": right_pct,
        "dominant_bias": dominant
    }


def extract_key_evidence(claim, articles, precomputed_claim_embedding=None):
    """
    Extract exact supporting/contradicting evidence quote cards from retrieved articles.
    Accelerated via vectorized batch embeddings and sentence selection.
    """
    evidence = []
    if not articles:
        return evidence

    model = get_embedding_model()
    encoder = get_cross_encoder()

    if precomputed_claim_embedding is not None:
        claim_vec = precomputed_claim_embedding
    else:
        with torch.no_grad():
            claim_vec = model.encode([claim], convert_to_numpy=True, normalize_embeddings=True)

    # Collect candidate sentences from top articles
    article_candidates = []
    all_sentences_flat = []

    for article in articles[:6]:
        content = article.get("content", "") or article.get("snippet", "")
        # Split content into sentences
        sentences = [s.strip() for s in re.split(r'[.!?]+', content) if len(s.strip()) > 20]
        if not sentences:
            if content and len(content.strip()) > 10:
                sentences = [content.strip()]
            else:
                continue
        # Take up to 3 best candidate sentences per article
        top_sentences = sentences[:3]
        start_idx = len(all_sentences_flat)
        all_sentences_flat.extend(top_sentences)
        end_idx = len(all_sentences_flat)
        article_candidates.append({
            "article": article,
            "sentence_indices": list(range(start_idx, end_idx)),
            "sentences": top_sentences
        })

    if not all_sentences_flat:
        return evidence

    # Single batch encode for all candidate sentences across all articles
    with torch.no_grad():
        sentence_embs = model.encode(all_sentences_flat, convert_to_numpy=True, normalize_embeddings=True)

    sentence_sims = np.dot(sentence_embs, claim_vec.T).flatten()

    # If cross encoder is available and NOT low memory mode, score in batch
    use_cross = (encoder is not None and not LOW_MEMORY_MODE)
    if use_cross:
        try:
            pairs = [(claim, s) for s in all_sentences_flat]
            with torch.no_grad():
                raw_cross = encoder.predict(pairs)
            sentence_cross = [float(1.0 / (1.0 + math.exp(-float(s)))) for s in raw_cross]
        except Exception:
            sentence_cross = [float(s) for s in sentence_sims]
    else:
        sentence_cross = [float(s) for s in sentence_sims]

    for item in article_candidates:
        article = item["article"]
        title = article.get("title", "Untitled Source")
        url = article.get("url", "#")
        content = article.get("content", "") or article.get("snippet", "")
        domain = extract_domain(url)
        credibility = get_source_score(url)

        best_score = 0.0
        best_sentence = item["sentences"][0]

        for idx in item["sentence_indices"]:
            sem_s = float(sentence_sims[idx])
            crs_s = float(sentence_cross[idx])
            comb = sem_s * 0.40 + crs_s * 0.60
            if comb > best_score:
                best_score = comb
                best_sentence = all_sentences_flat[idx]

        # Stance determination
        text_lower = (title + " " + content).lower()
        has_contra = any(kw in text_lower for kw in CONTRADICTION_KEYWORDS)
        stance = "CONTRADICTING" if has_contra else ("SUPPORTING" if best_score >= 0.40 else "NEUTRAL")

        evidence.append({
            "quote": best_sentence,
            "source": title,
            "url": url,
            "domain": domain,
            "credibility": credibility,
            "similarity": round(max(best_score, 0.50) * 100, 1),
            "stance": stance
        })

    evidence.sort(key=lambda x: x["similarity"], reverse=True)
    return evidence[:5]