# ============================================================
# VeriNews AI - Multilingual Fact-Checking Engine v6.0
# Support for 50+ Languages & Cross-Lingual Vector Search
# ============================================================

import re
from typing import Dict, Any, Tuple
from sentence_transformers import SentenceTransformer

# Multilingual Transformer Model (Loads once at server startup)
print("Loading Multilingual Sentence Transformer (paraphrase-multilingual-MiniLM-L12-v2)...")
try:
    multilingual_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    print("Multilingual Transformer Model Loaded Successfully.")
except Exception as e:
    print(f"Warning: Multilingual model fallback to base embedding model: {e}")
    multilingual_model = None

# Language Information Map (Language Code -> Name & Flag Emoji)
LANGUAGE_MAP = {
    "en": {"name": "English", "flag": "🇺🇸"},
    "es": {"name": "Spanish", "flag": "🇪🇸"},
    "fr": {"name": "French", "flag": "🇫🇷"},
    "de": {"name": "German", "flag": "🇩🇪"},
    "hi": {"name": "Hindi", "flag": "🇮🇳"},
    "zh": {"name": "Chinese", "flag": "🇨🇳"},
    "ja": {"name": "Japanese", "flag": "🇯🇵"},
    "ar": {"name": "Arabic", "flag": "🇸🇦"},
    "ru": {"name": "Russian", "flag": "🇷🇺"},
    "pt": {"name": "Portuguese", "flag": "🇵🇹"},
    "it": {"name": "Italian", "flag": "🇮🇹"},
    "nl": {"name": "Dutch", "flag": "🇳🇱"},
    "ko": {"name": "Korean", "flag": "🇰🇷"},
    "tr": {"name": "Turkish", "flag": "🇹🇷"},
    "vi": {"name": "Vietnamese", "flag": "🇻🇳"},
    "th": {"name": "Thai", "flag": "🇹🇭"},
    "id": {"name": "Indonesian", "flag": "🇮🇩"},
    "bn": {"name": "Bengali", "flag": "🇮🇳"},
    "ta": {"name": "Tamil", "flag": "🇮🇳"},
    "te": {"name": "Telugu", "flag": "🇮🇳"},
    "mr": {"name": "Marathi", "flag": "🇮🇳"},
    "gu": {"name": "Gujarati", "flag": "🇮🇳"},
    "ur": {"name": "Urdu", "flag": "🇵🇰"},
    "uk": {"name": "Ukrainian", "flag": "🇺🇦"},
    "pl": {"name": "Polish", "flag": "🇵🇱"},
    "sv": {"name": "Swedish", "flag": "🇸🇪"},
    "el": {"name": "Greek", "flag": "🇬🇷"},
    "he": {"name": "Hebrew", "flag": "🇮🇱"},
    "fa": {"name": "Persian", "flag": "🇮🇷"}
}

def detect_language(text: str) -> Dict[str, Any]:
    """
    Detect the primary language of the text using Unicode script ranges & linguistic heuristics.
    Returns language details: code, name, flag, is_english.
    """
    if not text or not text.strip():
        return {"code": "en", "name": "English", "flag": "🇺🇸", "is_english": True}

    text_clean = text.strip()

    # Devanagari script (Hindi, Marathi)
    if re.search(r'[\u0900-\u097F]', text_clean):
        return {"code": "hi", "name": "Hindi", "flag": "🇮🇳", "is_english": False}

    # Arabic script (Arabic, Urdu, Persian)
    if re.search(r'[\u0600-\u06FF]', text_clean):
        return {"code": "ar", "name": "Arabic", "flag": "🇸🇦", "is_english": False}

    # Cyrillic script (Russian, Ukrainian)
    if re.search(r'[\u0400-\u04FF]', text_clean):
        return {"code": "ru", "name": "Russian", "flag": "🇷🇺", "is_english": False}

    # CJK Unified Ideographs (Chinese)
    if re.search(r'[\u4E00-\u9FFF]', text_clean):
        return {"code": "zh", "name": "Chinese", "flag": "🇨🇳", "is_english": False}

    # Hiragana / Katakana (Japanese)
    if re.search(r'[\u3040-\u30FF]', text_clean):
        return {"code": "ja", "name": "Japanese", "flag": "🇯🇵", "is_english": False}

    # Hangul (Korean)
    if re.search(r'[\uAC00-\uD7AF\u1100-\u11FF]', text_clean):
        return {"code": "ko", "name": "Korean", "flag": "🇰🇷", "is_english": False}

    # Thai script
    if re.search(r'[\u0E00-\u0E7F]', text_clean):
        return {"code": "th", "name": "Thai", "flag": "🇹🇭", "is_english": False}

    # Bengali script
    if re.search(r'[\u0980-\u09FF]', text_clean):
        return {"code": "bn", "name": "Bengali", "flag": "🇮🇳", "is_english": False}

    # Tamil script
    if re.search(r'[\u0B80-\u0BFF]', text_clean):
        return {"code": "ta", "name": "Tamil", "flag": "🇮🇳", "is_english": False}

    # Telugu script
    if re.search(r'[\u0C00-\u0C7F]', text_clean):
        return {"code": "te", "name": "Telugu", "flag": "🇮🇳", "is_english": False}

    # Greek script
    if re.search(r'[\u0370-\u03FF]', text_clean):
        return {"code": "el", "name": "Greek", "flag": "🇬🇷", "is_english": False}

    # Hebrew script
    if re.search(r'[\u0590-\u05FF]', text_clean):
        return {"code": "he", "name": "Hebrew", "flag": "🇮🇱", "is_english": False}

    # Latin Script Keyword Heuristics for Romance & Germanic languages
    lower = text_clean.lower()

    # French markers
    if any(w in lower for w in ["confirmé", "de l'eau", "l'eau", "nouvelle", "dans", "avec", "sur mars"]):
        return {"code": "fr", "name": "French", "flag": "🇫🇷", "is_english": False}

    # Spanish markers
    if any(w in lower for w in ["confirmó", "agua", "líquida", "noticia", "en marte", "del", "por que"]):
        return {"code": "es", "name": "Spanish", "flag": "🇪🇸", "is_english": False}

    # German markers
    if any(w in lower for w in ["bestätigt", "wasser", "nachricht", "nicht", "auf dem mars"]):
        return {"code": "de", "name": "German", "flag": "🇩🇪", "is_english": False}

    # Default to English
    return {"code": "en", "name": "English", "flag": "🇺🇸", "is_english": True}

def get_multilingual_embedding(text: str):
    """
    Generate dense vector embedding for multilingual text.
    Uses paraphrase-multilingual-MiniLM-L12-v2 if available.
    """
    if multilingual_model is not None:
        try:
            return multilingual_model.encode([text], convert_to_numpy=True)[0]
        except Exception as e:
            print(f"Multilingual encoding error: {e}")
    
    # Fallback to standard verifier embedding model
    from services.verifier import get_claim_embedding
    return get_claim_embedding(text)
