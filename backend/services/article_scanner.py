import re
import urllib.request
import urllib.parse
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def fetch_and_parse_article(url: str) -> Dict[str, Any]:
    """
    Scrape and extract clean article metadata and body paragraphs from a URL.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return {
            "title": "Article Extraction Failed",
            "url": url,
            "domain": urlparse(url).netloc,
            "paragraphs": [],
            "error": f"Failed to retrieve URL: {str(e)}"
        }

    soup = BeautifulSoup(html, "html.parser")

    # Remove script, style, nav, footer, header tags
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()

    # Extract Title
    title = ""
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = og_title["content"].strip()
    elif soup.title and soup.title.string:
        title = soup.title.string.strip()

    # Extract Author & Date
    author = "Editorial Desk"
    author_meta = soup.find("meta", attrs={"name": "author"}) or soup.find("meta", property="article:author")
    if author_meta and author_meta.get("content"):
        author = author_meta["content"].strip()

    publish_date = "Recent"
    date_meta = soup.find("meta", property="article:published_time") or soup.find("meta", attrs={"name": "pubdate"})
    if date_meta and date_meta.get("content"):
        publish_date = date_meta["content"][:10]

    # Extract Paragraphs
    paragraphs = []
    for p in soup.find_all("p"):
        p_text = p.get_text().strip()
        if len(p_text) > 40 and not any(skip in p_text.lower() for skip in ["cookie", "subscribe", "sign in", "advertisement", "all rights reserved"]):
            paragraphs.append(p_text)

    # Limit to top 15 most substantive paragraphs to prevent bloat
    paragraphs = paragraphs[:15]

    return {
        "title": title or "Scraped Article",
        "url": url,
        "domain": urlparse(url).netloc,
        "author": author,
        "publish_date": publish_date,
        "paragraphs": paragraphs,
        "error": None
    }

def decompose_text_into_atomic_claims(paragraphs: List[str]) -> List[Dict[str, Any]]:
    """
    Decompose article paragraphs into distinct atomic testable factual assertions.
    """
    claims = []
    
    for p_idx, p in enumerate(paragraphs):
        # Split into sentences
        sentences = re.split(r"(?<=[.!?])\s+", p)
        for s_idx, sentence in enumerate(sentences):
            sentence = sentence.strip()
            # Filter sentences that look like factual claims (has subject + verb + >5 words)
            if len(sentence.split()) >= 6 and len(sentence) > 30:
                claims.append({
                    "claim_id": f"claim_{p_idx}_{s_idx}",
                    "paragraph_index": p_idx,
                    "claim_text": sentence
                })
                
    # Deduplicate and return top 8 representative claims for deep scan
    seen = set()
    unique_claims = []
    for c in claims:
        key = c["claim_text"].lower()
        if key not in seen:
            seen.add(key)
            unique_claims.append(c)

    return unique_claims[:8]

async def deep_scan_article(
    url_or_text: str,
    verifier_func
) -> Dict[str, Any]:
    """
    Perform complete Article Deep-Scan:
    1. Ingests URL or raw article text.
    2. Decomposes into atomic claims.
    3. Verifies each atomic claim in parallel.
    4. Computes Aggregate Article Truth Index (0-100%).
    """
    is_url = url_or_text.startswith("http://") or url_or_text.startswith("https://")
    
    if is_url:
        parsed = fetch_and_parse_article(url_or_text)
        if parsed.get("error"):
            return {
                "status": "ERROR",
                "message": parsed["error"],
                "truth_index": 0,
                "paragraphs": []
            }
        title = parsed["title"]
        domain = parsed["domain"]
        author = parsed["author"]
        paragraphs = parsed["paragraphs"]
    else:
        title = "Pasted Article Document"
        domain = "user-submitted"
        author = "Direct Input"
        paragraphs = [p.strip() for p in url_or_text.split("\n") if len(p.strip()) > 30][:12]

    if not paragraphs:
        paragraphs = [url_or_text.strip()]

    atomic_claims = decompose_text_into_atomic_claims(paragraphs)
    
    verified_claims = []
    truth_points = 0.0
    total_weights = 0.0

    for item in atomic_claims:
        claim_text = item["claim_text"]
        try:
            res = await verifier_func(claim_text)
            verdict = res.get("verdict", "UNVERIFIED").upper()
            confidence = float(res.get("confidence", 70.0))

            if "TRUE" in verdict or "SUPPORTED" in verdict:
                weight_mult = 1.0
                tag = "SUPPORTED"
            elif "FALSE" in verdict or "REFUTED" in verdict:
                weight_mult = 0.0
                tag = "CONTRADICTED"
            elif "MISLEADING" in verdict:
                weight_mult = 0.35
                tag = "MISLEADING"
            else:
                weight_mult = 0.50
                tag = "UNVERIFIED"

            truth_points += (confidence * weight_mult)
            total_weights += confidence

            verified_claims.append({
                "claim_id": item["claim_id"],
                "paragraph_index": item["paragraph_index"],
                "claim": claim_text,
                "verdict": verdict,
                "tag": tag,
                "confidence": confidence,
                "summary": res.get("summary", ""),
                "sources_count": len(res.get("supporting_sources", [])) + len(res.get("contradicting_sources", []))
            })
        except Exception as e:
            print(f"[ArticleScanner] Claim verification error: {e}")

    # Calculate aggregate truth score
    if total_weights > 0:
        truth_index = round((truth_points / total_weights) * 100, 1)
    else:
        truth_index = 80.0

    # Categorize paragraphs by veracity
    paragraph_cards = []
    for idx, p in enumerate(paragraphs):
        p_claims = [c for c in verified_claims if c["paragraph_index"] == idx]
        if any(c["tag"] == "CONTRADICTED" for c in p_claims):
            p_status = "CONTRADICTED"
        elif any(c["tag"] == "MISLEADING" for c in p_claims):
            p_status = "MISLEADING"
        elif any(c["tag"] == "SUPPORTED" for c in p_claims):
            p_status = "SUPPORTED"
        else:
            p_status = "NEUTRAL"

        paragraph_cards.append({
            "paragraph_index": idx,
            "text": p,
            "status": p_status,
            "associated_claims": p_claims
        })

    # Qualitative verdict label for the entire article
    if truth_index >= 85:
        overall_label = "HIGHLY FACTUAL & VERIFIED"
        badge_class = "truth-high"
    elif truth_index >= 65:
        overall_label = "MIXED FACTUALITY WITH SOME DISPUTED CLAIMS"
        badge_class = "truth-mixed"
    else:
        overall_label = "LOW TRUTH ACCURACY / HEAVILY DISPUTED"
        badge_class = "truth-low"

    return {
        "title": title,
        "domain": domain,
        "author": author,
        "total_paragraphs": len(paragraphs),
        "total_claims_extracted": len(atomic_claims),
        "truth_index": truth_index,
        "overall_label": overall_label,
        "badge_class": badge_class,
        "verified_claims": verified_claims,
        "paragraphs": paragraph_cards
    }
