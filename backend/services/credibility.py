"""
============================================================
VeriNews AI
Source Credibility Scoring
============================================================
"""
UNKNOWN_SOURCE_SCORE = 50

SOURCE_SCORES = {

    # =====================================================
    # Government
    # =====================================================

    ".gov": 100,

    "usa.gov": 100,

    "gov.uk": 100,

    "europa.eu": 100,

    "data.gov": 100,

    "india.gov.in": 100,

    "nasa.gov": 100,

    "cdc.gov": 100,

    "nih.gov": 100,

    "fda.gov": 100,

    # =====================================================
    # International Organizations
    # =====================================================

    "who.int": 100,

    "un.org": 99,

    "unesco.org": 99,

    "worldbank.org": 98,

    "imf.org": 98,

    # =====================================================
    # Scientific Journals
    # =====================================================

    "nature.com": 99,

    "science.org": 99,

    "sciencedirect.com": 98,

    "thelancet.com": 99,

    "nejm.org": 99,

    "springer.com": 97,

    "cell.com": 98,

    # =====================================================
    # Universities
    # =====================================================

    ".edu": 95,

    "mit.edu": 99,

    "stanford.edu": 99,

    "harvard.edu": 99,

    "ox.ac.uk": 99,

    "cam.ac.uk": 99,

   # =====================================================
# Global News
# =====================================================

"reuters.com": 98,

"apnews.com": 97,

"bbc.com": 96,

"bbc.co.uk": 96,

"nytimes.com": 95,

"washingtonpost.com": 94,

"theguardian.com": 94,

"economist.com": 95,

"wsj.com": 95,

"bloomberg.com": 96,

"abcnews.go.com": 93,

"npr.org": 94,

"aljazeera.com": 92,

"dw.com": 93,

"cbc.ca": 92,

"cnn.com": 90,

"foxnews.com": 88,

"nbcnews.com": 91,

"cbsnews.com": 91,


# =====================================================
# Indian News
# =====================================================

"thehindu.com": 94,

"indianexpress.com": 93,

"hindustantimes.com": 91,

"timesofindia.indiatimes.com": 90,

"ndtv.com": 91,

"livemint.com": 92,

"business-standard.com": 91,

"deccanherald.com": 90,

"news18.com": 88,

"theprint.in": 89,


# =====================================================
# Fact Checking
# =====================================================

"snopes.com": 97,

"factcheck.org": 98,

"politifact.com": 97,

"fullfact.org": 97,

"boomlive.in":95,

"altnews.in":96,

"factly.in":95,

    # =====================================================
    # Technology
    # =====================================================

    "techcrunch.com": 90,

    "theverge.com": 90,

    "wired.com": 91,

    "arstechnica.com": 92,

# =====================================================
# AI Research
# =====================================================

"openai.com": 95,

"deepmind.google": 95,

"research.google": 95,

"microsoft.com": 94,

"huggingface.co": 92,

"arxiv.org": 93,

"anthropic.com":94,

"x.ai":92,

"meta.com":93,

"research.ibm.com":94,


# =====================================================
# Space
# =====================================================

"esa.int": 99,

"space.com": 90,


    # =====================================================
    # Reference
    # =====================================================

    "britannica.com": 92,

    "wikipedia.org": 85,

    # =====================================================
    # Default Unknown
    # =====================================================

    "medium.com": 65,

    "blogspot.com": 50,

    "wordpress.com": 50,

    "substack.com": 60,

}
def get_source_score(url: str) -> int:
    """
    Returns credibility score.
    """

    if not url:
        return UNKNOWN_SOURCE_SCORE

    url = url.lower().strip()

    for domain, score in SOURCE_SCORES.items():

        if domain in url:

            return score

    # Unknown website
    return UNKNOWN_SOURCE_SCORE

def is_highly_trusted(url: str) -> bool:
    """
    True if credibility >= 95
    """

    return get_source_score(url) >= 95


def get_trust_label(score):

    if score >= 98:
        return "★★★★★ Very Highly Trusted"

    elif score >= 95:
        return "★★★★★ Highly Trusted"

    elif score >= 90:
        return "★★★★ Reliable"

    elif score >= 75:
        return "★★★ Moderate"

    elif score >= 60:
        return "★★ Low"

    return "★ Unknown"

def is_medium_trust(url):

    return get_source_score(url) >= 75


def is_reliable(url):

    return get_source_score(url) >= 90

def get_trust_color(score):

    if score>=95:

        return "success"

    elif score>=90:

        return "primary"

    elif score>=75:

        return "warning"

    return "danger"
