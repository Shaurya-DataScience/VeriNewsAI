import re
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

# ==============================================================================
# Comprehensive Media Bias & Factuality Database (AllSides, MBFC & Ad Fontes Mapped)
# ==============================================================================
# Bias: "FAR-LEFT", "LEFT", "CENTER-LEFT", "CENTER", "CENTER-RIGHT", "RIGHT", "FAR-RIGHT"
# Factuality: "VERY HIGH", "HIGH", "MOSTLY FACTUAL", "MIXED", "LOW", "VERY LOW"
# Reliability Score: 0 - 100

MEDIA_BIAS_DATABASE: Dict[str, Dict[str, Any]] = {
    # Wire Services & High-Factuality Center
    "reuters.com": {"name": "Reuters", "bias": "CENTER", "factuality": "VERY HIGH", "score": 98, "country": "Global/UK", "type": "News Agency"},
    "apnews.com": {"name": "Associated Press", "bias": "CENTER", "factuality": "VERY HIGH", "score": 98, "country": "USA", "type": "News Agency"},
    "afp.com": {"name": "Agence France-Presse", "bias": "CENTER", "factuality": "VERY HIGH", "score": 96, "country": "France", "type": "News Agency"},
    "bloomberg.com": {"name": "Bloomberg", "bias": "CENTER", "factuality": "HIGH", "score": 94, "country": "USA", "type": "Financial News"},
    "wsj.com": {"name": "Wall Street Journal (News)", "bias": "CENTER-RIGHT", "factuality": "HIGH", "score": 92, "country": "USA", "type": "Newspaper"},
    "ft.com": {"name": "Financial Times", "bias": "CENTER", "factuality": "HIGH", "score": 93, "country": "UK", "type": "Financial News"},
    "bbc.com": {"name": "BBC News", "bias": "CENTER", "factuality": "HIGH", "score": 94, "country": "UK", "type": "Public Broadcaster"},
    "bbc.co.uk": {"name": "BBC UK", "bias": "CENTER", "factuality": "HIGH", "score": 94, "country": "UK", "type": "Public Broadcaster"},
    "npr.org": {"name": "NPR", "bias": "CENTER-LEFT", "factuality": "HIGH", "score": 92, "country": "USA", "type": "Public Radio"},
    "pbs.org": {"name": "PBS NewsHour", "bias": "CENTER", "factuality": "VERY HIGH", "score": 96, "country": "USA", "type": "Public TV"},
    "c-span.org": {"name": "C-SPAN", "bias": "CENTER", "factuality": "VERY HIGH", "score": 98, "country": "USA", "type": "Government Coverage"},
    "thehill.com": {"name": "The Hill", "bias": "CENTER", "factuality": "HIGH", "score": 90, "country": "USA", "type": "Political News"},
    "usatoday.com": {"name": "USA Today", "bias": "CENTER", "factuality": "HIGH", "score": 90, "country": "USA", "type": "National Newspaper"},
    "csmonitor.com": {"name": "Christian Science Monitor", "bias": "CENTER", "factuality": "HIGH", "score": 92, "country": "USA", "type": "News Magazine"},
    "economist.com": {"name": "The Economist", "bias": "CENTER", "factuality": "HIGH", "score": 92, "country": "UK", "type": "News Magazine"},
    "axios.com": {"name": "Axios", "bias": "CENTER", "factuality": "HIGH", "score": 91, "country": "USA", "type": "Digital Media"},
    "politico.com": {"name": "Politico", "bias": "CENTER-LEFT", "factuality": "HIGH", "score": 90, "country": "USA", "type": "Political News"},
    "semafor.com": {"name": "Semafor", "bias": "CENTER", "factuality": "HIGH", "score": 90, "country": "USA", "type": "Digital Media"},
    "time.com": {"name": "TIME Magazine", "bias": "CENTER-LEFT", "factuality": "HIGH", "score": 89, "country": "USA", "type": "Magazine"},

    # Institutional & Scientific Authorities
    "who.int": {"name": "World Health Organization", "bias": "CENTER", "factuality": "VERY HIGH", "score": 99, "country": "International", "type": "Institutional"},
    "cdc.gov": {"name": "Centers for Disease Control", "bias": "CENTER", "factuality": "VERY HIGH", "score": 99, "country": "USA", "type": "Government"},
    "nih.gov": {"name": "National Institutes of Health", "bias": "CENTER", "factuality": "VERY HIGH", "score": 99, "country": "USA", "type": "Government"},
    "nasa.gov": {"name": "NASA", "bias": "CENTER", "factuality": "VERY HIGH", "score": 99, "country": "USA", "type": "Government"},
    "nature.com": {"name": "Nature Journal", "bias": "CENTER", "factuality": "VERY HIGH", "score": 99, "country": "UK", "type": "Scientific Journal"},
    "science.org": {"name": "Science Magazine", "bias": "CENTER", "factuality": "VERY HIGH", "score": 99, "country": "USA", "type": "Scientific Journal"},
    "thelancet.com": {"name": "The Lancet", "bias": "CENTER", "factuality": "VERY HIGH", "score": 98, "country": "UK", "type": "Medical Journal"},
    "nejm.org": {"name": "New England Journal of Medicine", "bias": "CENTER", "factuality": "VERY HIGH", "score": 98, "country": "USA", "type": "Medical Journal"},
    "scientificamerican.com": {"name": "Scientific American", "bias": "CENTER-LEFT", "factuality": "HIGH", "score": 93, "country": "USA", "type": "Science Magazine"},
    "noaa.gov": {"name": "NOAA Climate & Weather", "bias": "CENTER", "factuality": "VERY HIGH", "score": 99, "country": "USA", "type": "Government"},
    "fda.gov": {"name": "U.S. Food & Drug Administration", "bias": "CENTER", "factuality": "VERY HIGH", "score": 98, "country": "USA", "type": "Government"},
    "un.org": {"name": "United Nations", "bias": "CENTER", "factuality": "VERY HIGH", "score": 97, "country": "International", "type": "Institutional"},

    # Fact-Checking Organizations
    "snopes.com": {"name": "Snopes", "bias": "CENTER", "factuality": "VERY HIGH", "score": 96, "country": "USA", "type": "Fact Checker"},
    "politifact.com": {"name": "PolitiFact", "bias": "CENTER-LEFT", "factuality": "VERY HIGH", "score": 95, "country": "USA", "type": "Fact Checker"},
    "factcheck.org": {"name": "FactCheck.org", "bias": "CENTER", "factuality": "VERY HIGH", "score": 97, "country": "USA", "type": "Fact Checker"},
    "leadstories.com": {"name": "Lead Stories", "bias": "CENTER", "factuality": "VERY HIGH", "score": 96, "country": "USA", "type": "Fact Checker"},
    "fullfact.org": {"name": "Full Fact", "bias": "CENTER", "factuality": "VERY HIGH", "score": 97, "country": "UK", "type": "Fact Checker"},
    "checkyourfact.com": {"name": "Check Your Fact", "bias": "CENTER-RIGHT", "factuality": "HIGH", "score": 91, "country": "USA", "type": "Fact Checker"},
    "altnews.in": {"name": "Alt News", "bias": "CENTER-LEFT", "factuality": "HIGH", "score": 92, "country": "India", "type": "Fact Checker"},
    "boomlive.in": {"name": "BOOM Live", "bias": "CENTER", "factuality": "HIGH", "score": 93, "country": "India", "type": "Fact Checker"},
    "verinews-archive": {"name": "VeriNews Verified Archive", "bias": "CENTER", "factuality": "VERY HIGH", "score": 98, "country": "Global", "type": "Verified Benchmark"},

    # Center-Left & Mainstream Left
    "nytimes.com": {"name": "The New York Times", "bias": "CENTER-LEFT", "factuality": "HIGH", "score": 90, "country": "USA", "type": "Newspaper"},
    "washingtonpost.com": {"name": "The Washington Post", "bias": "CENTER-LEFT", "factuality": "HIGH", "score": 89, "country": "USA", "type": "Newspaper"},
    "theguardian.com": {"name": "The Guardian", "bias": "LEFT", "factuality": "HIGH", "score": 88, "country": "UK", "type": "Newspaper"},
    "cnn.com": {"name": "CNN", "bias": "LEFT", "factuality": "MOSTLY FACTUAL", "score": 82, "country": "USA", "type": "Broadcast TV"},
    "nbcnews.com": {"name": "NBC News", "bias": "CENTER-LEFT", "factuality": "HIGH", "score": 88, "country": "USA", "type": "Broadcast TV"},
    "cbsnews.com": {"name": "CBS News", "bias": "CENTER-LEFT", "factuality": "HIGH", "score": 89, "country": "USA", "type": "Broadcast TV"},
    "abcnews.go.com": {"name": "ABC News", "bias": "CENTER-LEFT", "factuality": "HIGH", "score": 89, "country": "USA", "type": "Broadcast TV"},
    "theatlantic.com": {"name": "The Atlantic", "bias": "CENTER-LEFT", "factuality": "HIGH", "score": 89, "country": "USA", "type": "Magazine"},
    "vox.com": {"name": "Vox", "bias": "LEFT", "factuality": "HIGH", "score": 86, "country": "USA", "type": "Digital Media"},
    "slate.com": {"name": "Slate", "bias": "LEFT", "factuality": "MOSTLY FACTUAL", "score": 83, "country": "USA", "type": "Online Magazine"},
    "msnbc.com": {"name": "MSNBC", "bias": "LEFT", "factuality": "MIXED", "score": 75, "country": "USA", "type": "Cable News"},
    "huffpost.com": {"name": "HuffPost", "bias": "LEFT", "factuality": "MOSTLY FACTUAL", "score": 80, "country": "USA", "type": "Digital Media"},
    "motherjones.com": {"name": "Mother Jones", "bias": "LEFT", "factuality": "HIGH", "score": 85, "country": "USA", "type": "Investigative Magazine"},
    "jacobin.com": {"name": "Jacobin", "bias": "FAR-LEFT", "factuality": "MOSTLY FACTUAL", "score": 78, "country": "USA", "type": "Political Magazine"},
    "democracynow.org": {"name": "Democracy Now!", "bias": "LEFT", "factuality": "HIGH", "score": 87, "country": "USA", "type": "Independent News"},
    "propublica.org": {"name": "ProPublica", "bias": "CENTER-LEFT", "factuality": "VERY HIGH", "score": 97, "country": "USA", "type": "Investigative Journalism"},

    # Center-Right & Mainstream Right
    "foxnews.com": {"name": "Fox News (Newsroom)", "bias": "RIGHT", "factuality": "MIXED", "score": 73, "country": "USA", "type": "Cable News"},
    "nationalreview.com": {"name": "National Review", "bias": "RIGHT", "factuality": "MOSTLY FACTUAL", "score": 82, "country": "USA", "type": "Conservative Magazine"},
    "theamericanconservative.com": {"name": "The American Conservative", "bias": "RIGHT", "factuality": "MOSTLY FACTUAL", "score": 81, "country": "USA", "type": "Magazine"},
    "nypost.com": {"name": "New York Post", "bias": "RIGHT", "factuality": "MIXED", "score": 74, "country": "USA", "type": "Tabloid Newspaper"},
    "washingtontimes.com": {"name": "The Washington Times", "bias": "RIGHT", "factuality": "MIXED", "score": 72, "country": "USA", "type": "Daily Newspaper"},
    "dailywire.com": {"name": "The Daily Wire", "bias": "RIGHT", "factuality": "MIXED", "score": 70, "country": "USA", "type": "Digital Media"},
    "theepochtimes.com": {"name": "The Epoch Times", "bias": "FAR-RIGHT", "factuality": "LOW", "score": 45, "country": "USA", "type": "Partisan Media"},
    "breitbart.com": {"name": "Breitbart News", "bias": "FAR-RIGHT", "factuality": "LOW", "score": 42, "country": "USA", "type": "Partisan Media"},
    "newsmax.com": {"name": "Newsmax", "bias": "FAR-RIGHT", "factuality": "LOW", "score": 48, "country": "USA", "type": "Cable News"},
    "oann.com": {"name": "One America News (OAN)", "bias": "FAR-RIGHT", "factuality": "VERY LOW", "score": 38, "country": "USA", "type": "Cable News"},
    "infowars.com": {"name": "InfoWars", "bias": "FAR-RIGHT", "factuality": "VERY LOW", "score": 15, "country": "USA", "type": "Conspiracy Site"},
    "naturalnews.com": {"name": "Natural News", "bias": "FAR-RIGHT", "factuality": "VERY LOW", "score": 18, "country": "USA", "type": "Pseudoscience / Conspiracy"},
    "thegatewaypundit.com": {"name": "The Gateway Pundit", "bias": "FAR-RIGHT", "factuality": "VERY LOW", "score": 22, "country": "USA", "type": "Partisan Blog"},

    # International Broadcasters & Regional Leaders
    "aljazeera.com": {"name": "Al Jazeera English", "bias": "CENTER-LEFT", "factuality": "HIGH", "score": 88, "country": "Qatar/Global", "type": "Broadcaster"},
    "dw.com": {"name": "Deutsche Welle", "bias": "CENTER", "factuality": "VERY HIGH", "score": 95, "country": "Germany", "type": "Public Broadcaster"},
    "france24.com": {"name": "France 24", "bias": "CENTER", "factuality": "HIGH", "score": 93, "country": "France", "type": "Public Broadcaster"},
    "thehindu.com": {"name": "The Hindu", "bias": "CENTER-LEFT", "factuality": "HIGH", "score": 91, "country": "India", "type": "National Newspaper"},
    "indianexpress.com": {"name": "The Indian Express", "bias": "CENTER", "factuality": "HIGH", "score": 91, "country": "India", "type": "National Newspaper"},
    "ndtv.com": {"name": "NDTV", "bias": "CENTER", "factuality": "HIGH", "score": 88, "country": "India", "type": "News Broadcaster"},
    "timesofindia.indiatimes.com": {"name": "Times of India", "bias": "CENTER", "factuality": "MOSTLY FACTUAL", "score": 84, "country": "India", "type": "National Newspaper"},
    "japantimes.co.jp": {"name": "The Japan Times", "bias": "CENTER", "factuality": "HIGH", "score": 92, "country": "Japan", "type": "Newspaper"},
    "scmp.com": {"name": "South China Morning Post", "bias": "CENTER", "factuality": "HIGH", "score": 89, "country": "Hong Kong", "type": "Newspaper"},
    "smh.com.au": {"name": "Sydney Morning Herald", "bias": "CENTER-LEFT", "factuality": "HIGH", "score": 90, "country": "Australia", "type": "Newspaper"},
    "abc.net.au": {"name": "ABC News Australia", "bias": "CENTER", "factuality": "VERY HIGH", "score": 95, "country": "Australia", "type": "Public Broadcaster"},
    "cbc.ca": {"name": "CBC News Canada", "bias": "CENTER-LEFT", "factuality": "HIGH", "score": 92, "country": "Canada", "type": "Public Broadcaster"},
    "theglobeandmail.com": {"name": "The Globe and Mail", "bias": "CENTER", "factuality": "HIGH", "score": 91, "country": "Canada", "type": "Newspaper"},
}

DEFAULT_DOMAIN_RATING = {
    "name": "General Web Source",
    "bias": "CENTER",
    "factuality": "MOSTLY FACTUAL",
    "score": 75,
    "country": "Unknown",
    "type": "Online Media"
}

def clean_domain(url_or_domain: str) -> str:
    """Extract clean domain name without subdomains or protocols."""
    if not url_or_domain:
        return "unknown"
    d = url_or_domain.strip().lower()
    if "://" in d:
        try:
            d = urlparse(d).netloc
        except Exception:
            pass
    d = re.sub(r"^www\.", "", d)
    d = d.split(":")[0]
    return d

def get_domain_bias_info(domain_or_url: str) -> Dict[str, Any]:
    """Look up domain in Media Bias & Factuality Index with fallback matching."""
    domain = clean_domain(domain_or_url)

    # Exact Match
    if domain in MEDIA_BIAS_DATABASE:
        info = dict(MEDIA_BIAS_DATABASE[domain])
        info["domain"] = domain
        return info

    # Suffix / Root Domain Match (e.g., news.bbc.co.uk -> bbc.co.uk)
    for known_domain, data in MEDIA_BIAS_DATABASE.items():
        if domain.endswith("." + known_domain) or domain == known_domain:
            info = dict(data)
            info["domain"] = domain
            return info

    # Heuristic Fallback
    fallback = dict(DEFAULT_DOMAIN_RATING)
    fallback["name"] = domain.capitalize() if domain != "unknown" else "General Source"
    fallback["domain"] = domain

    # Government / Educational TLD bonus
    if domain.endswith(".gov") or domain.endswith(".edu") or domain.endswith(".mil"):
        fallback["factuality"] = "VERY HIGH"
        fallback["score"] = 96
        fallback["type"] = "Government / Academic"
    elif domain.endswith(".org"):
        fallback["factuality"] = "HIGH"
        fallback["score"] = 86
        fallback["type"] = "Organization"

    return fallback

def analyze_sources_bias(articles_or_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze the full citations pool for a fact check:
    - Calculates Media Bias Spectrum distribution (Left, Center, Right)
    - Calculates Average Factuality score (0-100)
    - Returns detailed per-source bias badges and coordinates for 2D radar mapping.
    """
    if not articles_or_sources:
        return {
            "average_factuality_score": 85.0,
            "overall_factuality_rating": "HIGH",
            "bias_distribution": {"left": 0, "center_left": 0, "center": 100, "center_right": 0, "right": 0},
            "dominant_bias": "CENTER",
            "sources_analyzed": 0,
            "source_nodes": []
        }

    bias_counts = {
        "FAR-LEFT": 0, "LEFT": 0, "CENTER-LEFT": 0,
        "CENTER": 0, "CENTER-RIGHT": 0, "RIGHT": 0, "FAR-RIGHT": 0
    }
    factuality_scores = []
    source_nodes = []

    for src in articles_or_sources:
        url = src.get("url") or src.get("source_url") or ""
        domain = src.get("domain") or src.get("source") or clean_domain(url)
        bias_info = get_domain_bias_info(domain)

        raw_bias = bias_info["bias"].upper()
        if raw_bias in bias_counts:
            bias_counts[raw_bias] += 1
        else:
            bias_counts["CENTER"] += 1

        factuality_scores.append(bias_info["score"])

        # Coordinates for 2D Radar (-100 Left to +100 Right, 0 to 100 Factuality)
        bias_x_map = {
            "FAR-LEFT": -85, "LEFT": -50, "CENTER-LEFT": -25,
            "CENTER": 0, "CENTER-RIGHT": 25, "RIGHT": 50, "FAR-RIGHT": 85
        }
        x_coord = bias_x_map.get(raw_bias, 0)
        y_coord = bias_info["score"]

        source_nodes.append({
            "name": bias_info["name"],
            "domain": bias_info["domain"],
            "url": url,
            "bias": bias_info["bias"],
            "factuality": bias_info["factuality"],
            "reliability_score": bias_info["score"],
            "type": bias_info.get("type", "Media"),
            "x_bias_coord": x_coord,
            "y_factuality_coord": y_coord
        })

    total = len(factuality_scores) or 1
    avg_score = round(sum(factuality_scores) / total, 1)

    # Simplified 5-bucket distribution percentage
    left_pct = round(((bias_counts["FAR-LEFT"] + bias_counts["LEFT"]) / total) * 100, 1)
    center_left_pct = round((bias_counts["CENTER-LEFT"] / total) * 100, 1)
    center_pct = round((bias_counts["CENTER"] / total) * 100, 1)
    center_right_pct = round((bias_counts["CENTER-RIGHT"] / total) * 100, 1)
    right_pct = round(((bias_counts["RIGHT"] + bias_counts["FAR-RIGHT"]) / total) * 100, 1)

    pct_map = {
        "LEFT": left_pct,
        "CENTER-LEFT": center_left_pct,
        "CENTER": center_pct,
        "CENTER-RIGHT": center_right_pct,
        "RIGHT": right_pct
    }
    dominant_bias = max(pct_map.items(), key=lambda k: k[1])[0]

    if avg_score >= 93:
        qual_factuality = "VERY HIGH"
    elif avg_score >= 85:
        qual_factuality = "HIGH"
    elif avg_score >= 75:
        qual_factuality = "MOSTLY FACTUAL"
    elif avg_score >= 60:
        qual_factuality = "MIXED"
    else:
        qual_factuality = "LOW"

    return {
        "average_factuality_score": avg_score,
        "overall_factuality_rating": qual_factuality,
        "bias_distribution": {
            "left": left_pct,
            "center_left": center_left_pct,
            "center": center_pct,
            "center_right": center_right_pct,
            "right": right_pct
        },
        "dominant_bias": dominant_bias,
        "sources_analyzed": len(source_nodes),
        "source_nodes": source_nodes
    }
