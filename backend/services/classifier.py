import os
import sys
import torch
import numpy as np
from typing import Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from training.dataset_preprocessor import REVERSE_NUMERIC_LABEL_MAP

MODEL_SAVE_DIR = os.path.join(os.path.dirname(__file__), "..", "models", "distilbert_factchecker")

_classifier_model = None
_classifier_tokenizer = None
_fallback_joblib = None
_sentence_embedder = None

def get_classifier():
    """Lazy load fine-tuned DistilBERT model or fallback embedding classifier."""
    global _classifier_model, _classifier_tokenizer, _fallback_joblib, _sentence_embedder

    if _classifier_model is not None or _fallback_joblib is not None:
        return

    print("[Classifier] Initializing Claim Classifier Inference Engine...")

    # 1. Try loading DistilBERT PyTorch HuggingFace checkpoint
    if os.path.exists(MODEL_SAVE_DIR) and os.path.exists(os.path.join(MODEL_SAVE_DIR, "config.json")):
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            _classifier_tokenizer = AutoTokenizer.from_pretrained(MODEL_SAVE_DIR)
            _classifier_model = AutoModelForSequenceClassification.from_pretrained(MODEL_SAVE_DIR)
            _classifier_model.eval()
            print("[Classifier] Successfully loaded fine-tuned DistilBERT model!")
            return
        except Exception as e:
            print(f"[Classifier] Could not load DistilBERT checkpoint: {e}")

    # 2. Try loading scikit-learn fallback checkpoint
    fallback_path = os.path.join(MODEL_SAVE_DIR, "classifier_fallback.joblib")
    if os.path.exists(fallback_path):
        try:
            import joblib
            from sentence_transformers import SentenceTransformer
            _fallback_joblib = joblib.load(fallback_path)
            _sentence_embedder = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
            print("[Classifier] Successfully loaded fallback joblib classifier!")
            return
        except Exception as e:
            print(f"[Classifier] Fallback joblib load error: {e}")

    # 3. Default Heuristic / Centroid Classifier
    print("[Classifier] Initializing heuristic semantic classifier...")

def classify_claim(claim: str) -> Dict[str, Any]:
    """
    Classify a news claim into one of 4 categories:
    TRUE, FALSE, MISLEADING, UNVERIFIED
    Returns predicted label, confidence, and full probability distribution.
    """
    get_classifier()

    # 1. DistilBERT Inference
    if _classifier_model is not None and _classifier_tokenizer is not None:
        try:
            inputs = _classifier_tokenizer(claim, return_tensors="pt", truncation=True, padding=True, max_length=128)
            with torch.no_grad():
                outputs = _classifier_model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=1).squeeze(0).cpu().numpy()

            pred_idx = int(np.argmax(probs))
            pred_label = REVERSE_NUMERIC_LABEL_MAP.get(pred_idx, "UNVERIFIED")

            prob_dict = {REVERSE_NUMERIC_LABEL_MAP.get(i, f"CLASS_{i}"): float(probs[i]) for i in range(len(probs))}
            confidence_pct = round(float(probs[pred_idx]) * 100, 1)

            return {
                "label": pred_label,
                "confidence": confidence_pct,
                "probabilities": prob_dict,
                "model_type": "DistilBERT Fine-Tuned"
            }
        except Exception as e:
            print(f"[Classifier] DistilBERT prediction error: {e}")

    # 2. Scikit-Learn Joblib Fallback
    if _fallback_joblib is not None and _sentence_embedder is not None:
        try:
            emb = _sentence_embedder.encode([claim])
            probs = _fallback_joblib.predict_proba(emb)[0]
            classes = _fallback_joblib.classes_

            pred_idx = int(np.argmax(probs))
            num_label = classes[pred_idx]
            pred_label = REVERSE_NUMERIC_LABEL_MAP.get(num_label, "UNVERIFIED")

            prob_dict = {REVERSE_NUMERIC_LABEL_MAP.get(c, f"CLASS_{c}"): float(p) for c, p in zip(classes, probs)}
            confidence_pct = round(float(probs[pred_idx]) * 100, 1)

            return {
                "label": pred_label,
                "confidence": confidence_pct,
                "probabilities": prob_dict,
                "model_type": "SentenceTransformer + LogisticRegression"
            }
        except Exception as e:
            print(f"[Classifier] Fallback prediction error: {e}")

    # 3. Rule-Based Heuristic Semantic Classifier
    claim_lower = claim.lower()
    if any(k in claim_lower for k in ["fake", "debunked", "hoax", "false", "never happened"]):
        label = "FALSE"
        prob = 0.88
    elif any(k in claim_lower for k in ["confirmed", "discovered", "official", "proven", "true"]):
        label = "TRUE"
        prob = 0.85
    elif any(k in claim_lower for k in ["misleading", "exaggerated", "out of context", "partially"]):
        label = "MISLEADING"
        prob = 0.78
    else:
        label = "UNVERIFIED"
        prob = 0.60

    return {
        "label": label,
        "confidence": round(prob * 100, 1),
        "probabilities": {
            "TRUE": 0.85 if label == "TRUE" else 0.05,
            "FALSE": 0.88 if label == "FALSE" else 0.05,
            "MISLEADING": 0.78 if label == "MISLEADING" else 0.05,
            "UNVERIFIED": 0.60 if label == "UNVERIFIED" else 0.05
        },
        "model_type": "Heuristic Rule-Based"
    }
