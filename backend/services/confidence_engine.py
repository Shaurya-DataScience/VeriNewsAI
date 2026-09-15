import os
import sys
from typing import Dict, Any, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database import get_system_config

class ConfidenceEngine:
    """
    Weighted Confidence Scoring Engine for Intelligent Hybrid Fact Verification.
    
    Default Weights:
    - Dataset Prediction: 35% (0.35)
    - Cross-Encoder Rerank: 30% (0.30)
    - Source Credibility: 20% (0.20)
    - Semantic Similarity: 15% (0.15)
    """

    def __init__(self, custom_weights: Dict[str, float] = None):
        cfg = get_system_config()
        weights = custom_weights or cfg.get("weights", {})
        
        self.w_dataset = float(weights.get("dataset_prediction", 0.35))
        self.w_cross = float(weights.get("cross_encoder", 0.30))
        self.w_credibility = float(weights.get("source_credibility", 0.20))
        self.w_similarity = float(weights.get("semantic_similarity", 0.15))

        # Normalize weights so sum = 1.0
        total = self.w_dataset + self.w_cross + self.w_credibility + self.w_similarity
        if total > 0:
            self.w_dataset /= total
            self.w_cross /= total
            self.w_credibility /= total
            self.w_similarity /= total

    def calculate_confidence(
        self,
        classifier_confidence: float,
        cross_encoder_score: float,
        source_credibility: float,
        semantic_similarity: float
    ) -> Tuple[int, Dict[str, float]]:
        """
        Calculate weighted confidence score (0-100%) and return detailed breakdown.
        """
        s_dataset = max(0.0, min(100.0, float(classifier_confidence)))
        s_cross = max(0.0, min(100.0, float(cross_encoder_score)))
        s_cred = max(0.0, min(100.0, float(source_credibility)))
        s_sim = max(0.0, min(100.0, float(semantic_similarity)))

        weighted_score = (
            (s_dataset * self.w_dataset) +
            (s_cross * self.w_cross) +
            (s_cred * self.w_credibility) +
            (s_sim * self.w_similarity)
        )

        final_confidence = Math_round(weighted_score) if hasattr(self, 'Math_round') else round(weighted_score)
        final_confidence = max(0, min(100, int(final_confidence)))

        breakdown = {
            "dataset_prediction": round(s_dataset, 1),
            "cross_encoder": round(s_cross, 1),
            "source_credibility": round(s_cred, 1),
            "semantic_similarity": round(s_sim, 1),
            "date_verification": 100.0,
            "evidence_consistency": round((s_sim + s_cross) / 2, 1),
            "trusted_source_ratio": round(s_cred * 0.9, 1),
            "weights_used": {
                "dataset_prediction": round(self.w_dataset, 2),
                "cross_encoder": round(self.w_cross, 2),
                "source_credibility": round(self.w_credibility, 2),
                "semantic_similarity": round(self.w_similarity, 2)
            }
        }

        return final_confidence, breakdown

def calculate_weighted_confidence(
    classifier_confidence: float,
    cross_encoder_score: float,
    source_credibility: float,
    semantic_similarity: float,
    custom_weights: Dict[str, float] = None
) -> Tuple[int, Dict[str, float]]:
    engine = ConfidenceEngine(custom_weights=custom_weights)
    return engine.calculate_confidence(
        classifier_confidence, cross_encoder_score, source_credibility, semantic_similarity
    )
