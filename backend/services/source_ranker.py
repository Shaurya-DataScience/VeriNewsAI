# ============================================================
# VeriNews AI - Source Ranker & Badge Engine v6.0
# Multi-Factor Source Credibility & Authority Classification
# ============================================================

from services.verifier import extract_domain

GOVT_DOMAINS = [".gov", "gov.in", "gov.uk", "whitehouse.gov", "pib.gov.in"]
SCI_DOMAINS = ["nature.com", "science.org", "nasa.gov", "who.int", "cdc.gov", "nih.gov", "thelancet.com", "nejm.org", ".edu"]
FACTCHECK_DOMAINS = ["snopes.com", "factcheck.org", "politifact.com", "altnews.in", "boomlive.in", "fullfact.org"]
INTL_DOMAINS = ["reuters.com", "apnews.com", "bbc.com", "nytimes.com", "theguardian.com", "bloomberg.com", "afp.com"]

def assign_source_badges(domain: str, credibility: int) -> list:
    """Assign authoritative badges based on domain registry and credibility."""
    badges = []
    dom_lower = domain.lower()

    if any(g in dom_lower for g in GOVT_DOMAINS):
        badges.append({"label": "Government", "type": "gov"})
    if any(s in dom_lower for s in SCI_DOMAINS):
        badges.append({"label": "Scientific", "type": "sci"})
    if any(f in dom_lower for f in FACTCHECK_DOMAINS):
        badges.append({"label": "Fact Check", "type": "factcheck"})
    if any(i in dom_lower for i in INTL_DOMAINS):
        badges.append({"label": "International Wire", "type": "intl"})
    if credibility >= 85:
        badges.append({"label": "Trusted Index", "type": "trusted"})

    if not badges:
        if credibility >= 70:
            badges.append({"label": "Verified News", "type": "verified"})
        else:
            badges.append({"label": "Independent Blog", "type": "blog"})

    return badges

def calculate_star_rating(composite_score: float) -> str:
    """Convert composite score (0-100) into 5-star rating scale."""
    if composite_score >= 88:
        return "★★★★★"
    elif composite_score >= 75:
        return "★★★★☆"
    elif composite_score >= 60:
        return "★★★☆☆"
    elif composite_score >= 45:
        return "★★☆☆☆"
    else:
        return "★☆☆☆☆"

def rank_and_badge_sources(sources_list: list) -> list:
    """
    Rank sources by composite authority score:
    Score = Credibility (40%) + Cross-Score (30%) + Similarity (20%) + Trusted Bonus (10%)
    """
    if not sources_list:
        return []

    ranked = []
    for item in sources_list:
        card = item.copy()
        cred = card.get("credibility", 50)
        cross = card.get("cross_score", 50)
        sim = card.get("semantic_similarity", 50)
        trusted = card.get("trusted", False)

        bonus = 10 if trusted else 0
        composite = min(100.0, round(cred * 0.40 + cross * 0.30 + sim * 0.20 + bonus, 1))

        domain = card.get("domain") or extract_domain(card.get("url", ""))
        badges = assign_source_badges(domain, cred)
        stars = calculate_star_rating(composite)

        card["rank_score"] = composite
        card["stars"] = stars
        card["badges"] = badges
        card["evidence_strength"] = "Strong Evidence" if composite >= 75 else ("Moderate Evidence" if composite >= 50 else "Weak Alignment")
        ranked.append(card)

    ranked.sort(key=lambda x: x["rank_score"], reverse=True)
    return ranked
