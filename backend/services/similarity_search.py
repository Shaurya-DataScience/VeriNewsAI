# ============================================================
# VeriNews AI - Claim Vector Similarity Search v6.0
# High-Performance Neural Vector Search over Past Claims
# ============================================================

import os
import json
import numpy as np
from datetime import datetime
from services.verifier import embedding_model
import database

DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "verified_dataset.json")

class ClaimSimilarityStore:
    def __init__(self):
        self.claims_db = []
        self.dataset_claims = []
        self.load_dataset_seed()
        self.reload_from_db()

    def load_dataset_seed(self):
        """Load curated pre-verified offline dataset and pre-compute embeddings."""
        try:
            if os.path.exists(DATASET_PATH):
                with open(DATASET_PATH, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)

                for item in raw_data:
                    emb = self.get_embedding(item["claim"])
                    item_copy = item.copy()
                    item_copy["embedding"] = emb
                    self.dataset_claims.append(item_copy)
                print(f"Loaded {len(self.dataset_claims)} pre-verified claims from offline dataset.")
        except Exception as e:
            print(f"Error loading offline dataset seed: {e}")
            self.dataset_claims = []

    def find_dataset_match(self, query: str, threshold: float = 0.82) -> dict:
        """
        Check query against pre-indexed offline dataset.
        Returns matching dataset payload if similarity >= threshold (0 API calls!).
        """
        if not self.dataset_claims or not query or not query.strip():
            return None

        try:
            query_vec = self.get_embedding(query)
            best_match = None
            best_score = 0.0

            for item in self.dataset_claims:
                score = float(np.dot(item["embedding"], query_vec))
                if score > best_score:
                    best_score = score
                    best_match = item

            if best_match and best_score >= threshold:
                result = best_match.copy()
                if "embedding" in result:
                    del result["embedding"]
                result["dataset_similarity"] = round(best_score * 100, 1)
                return result
        except Exception as e:
            print(f"Dataset match error: {e}")

        return None

    def reload_from_db(self):
        """Reload stored claims and pre-computed embeddings from DB."""
        try:
            stored = database.get_all_stored_claims()
            self.claims_db = stored
        except Exception as e:
            print(f"Error loading claim embeddings: {e}")
            self.claims_db = []

    def get_embedding(self, text: str) -> np.ndarray:
        """Generate 384-d normalized vector embedding using shared SentenceTransformer."""
        vec = embedding_model.encode([text])[0]
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def add_claim(self, claim_id: str, claim: str, verdict: str, confidence: int, summary: str = "", timestamp: str = None):
        """Add a new verified claim to the vector store and DB."""
        if not timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Check for duplicates
        for item in self.claims_db:
            if item["claim"].lower().strip() == claim.lower().strip():
                return

        emb = self.get_embedding(claim).tolist()
        database.save_claim_embedding(claim_id, claim, emb, verdict, confidence, summary, timestamp)

        self.claims_db.append({
            "claim_id": claim_id,
            "claim": claim,
            "embedding": emb,
            "verdict": verdict,
            "confidence": confidence,
            "summary": summary,
            "timestamp": timestamp
        })

    def search_similar(self, query: str, top_k: int = 5) -> list:
        """
        Fast vector similarity search (<15ms). Returns top_k similar claims.
        """
        if not self.claims_db or not query or not query.strip():
            return []

        try:
            query_vec = self.get_embedding(query)
            valid_items = [item for item in self.claims_db if item.get("embedding") and len(item["embedding"]) == len(query_vec)]
            if not valid_items:
                return []

            db_vecs = np.array([item["embedding"] for item in valid_items])
            similarities = np.dot(db_vecs, query_vec)

            # Ensure similarities is 1D array
            if np.ndim(similarities) == 0:
                similarities = np.array([similarities])

            results = []
            for idx, score in enumerate(similarities):
                sim_pct = float(round(float(score) * 100, 1))
                # Filter out non-relevant claims (< 45% similarity)
                if sim_pct >= 45.0:
                    item = valid_items[idx].copy()
                    item["similarity"] = sim_pct
                    if "embedding" in item:
                        del item["embedding"]
                    results.append(item)

            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:top_k]
        except Exception as e:
            print(f"Similarity search error: {e}")
            return []


def rerank_candidates_with_cross_encoder(query: str, candidates: list) -> list:
    """
    Rerank top-k vector candidates using CrossEncoder neural model predictions.
    """
    if not candidates or not query:
        return candidates

    try:
        from services.verifier import cross_encoder
        pairs = [(query, c.get("claim", "")) for c in candidates]
        raw_scores = cross_encoder.predict(pairs)

        for candidate, raw_s in zip(candidates, raw_scores):
            # Sigmoid normalization of logits to 0-100% scale
            norm_score = float(1.0 / (1.0 + np.exp(-float(raw_s)))) * 100.0
            candidate["cross_score"] = round(norm_score, 1)

        # Sort descending by real CrossEncoder score
        candidates.sort(key=lambda x: x.get("cross_score", 0.0), reverse=True)
    except Exception as e:
        print(f"CrossEncoder reranking error: {e}")
        for c in candidates:
            c["cross_score"] = c.get("similarity", 75.0)

    return candidates


# Singleton instance
vector_store = ClaimSimilarityStore()

def get_similar_claims(claim: str, top_k: int = 5) -> list:
    return vector_store.search_similar(claim, top_k=top_k)

def register_verified_claim(claim_id: str, claim: str, verdict: str, confidence: int, summary: str = "", timestamp: str = None):
    vector_store.add_claim(claim_id, claim, verdict, confidence, summary, timestamp)

def find_dataset_match(query: str, threshold: float = 0.82) -> dict:
    return vector_store.find_dataset_match(query, threshold=threshold)
