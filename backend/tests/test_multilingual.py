# ============================================================
# VeriNews AI - Multilingual & Automated Streaming Tests
# ============================================================

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.multilingual import detect_language, get_multilingual_embedding

def test_language_detection_multilingual():
    """Verify language detection across multiple international scripts & languages."""
    # English
    en_res = detect_language("NASA confirmed liquid water on Mars")
    assert en_res["code"] == "en"
    assert en_res["flag"] == "🇺🇸"
    assert en_res["is_english"] is True

    # Spanish
    es_res = detect_language("La NASA confirmó agua líquida en Marte")
    assert es_res["code"] == "es"
    assert es_res["flag"] == "🇪🇸"

    # French
    fr_res = detect_language("La NASA a confirmé de l'eau liquide sur Mars")
    assert fr_res["code"] == "fr"
    assert fr_res["flag"] == "🇫🇷"

    # Hindi (Devanagari script)
    hi_res = detect_language("नासा ने मंगल ग्रह पर तरल पानी की पुष्टि की।")
    assert hi_res["code"] == "hi"
    assert hi_res["flag"] == "🇮🇳"

    # Arabic script
    ar_res = detect_language("أكدت وكالة ناسا اكتشاف المياه السائلة على كوكب المريخ")
    assert ar_res["code"] == "ar"
    assert ar_res["flag"] == "🇸🇦"

    # Chinese
    zh_res = detect_language("美国宇航局确认火星上存在液态水")
    assert zh_res["code"] == "zh"
    assert zh_res["flag"] == "🇨🇳"

    # Russian
    ru_res = detect_language("НАСА подтвердило наличие жидкой воды на Марсе")
    assert ru_res["code"] == "ru"
    assert ru_res["flag"] == "🇷🇺"

def test_multilingual_embedding_vector():
    """Verify dense vector embedding shape for multilingual claims."""
    vec_en = get_multilingual_embedding("NASA confirmed liquid water on Mars")
    assert vec_en is not None
    assert len(vec_en) in [384, 768]
