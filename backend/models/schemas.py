from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ClaimVerifyRequest(BaseModel):
    claim: str = Field(..., description="News claim text or URL to verify", json_schema_extra={"example": "NASA confirmed liquid water on Mars"})

class WeightConfig(BaseModel):
    dataset_prediction: float = Field(0.35, ge=0.0, le=1.0)
    cross_encoder: float = Field(0.30, ge=0.0, le=1.0)
    source_credibility: float = Field(0.20, ge=0.0, le=1.0)
    semantic_similarity: float = Field(0.15, ge=0.0, le=1.0)

class ConfigUpdateRequest(BaseModel):
    weights: Optional[WeightConfig] = None
    similarity_threshold: Optional[float] = Field(0.90, ge=0.5, le=1.0)

class SourceItem(BaseModel):
    title: Optional[str] = "Verified Article"
    domain: Optional[str] = ""
    url: Optional[str] = "#"
    credibility: float = 80.0
    final_score: float = 0.0
    stars: str = "★★★★☆"
    badges: List[Dict[str, str]] = []

class EvidenceItem(BaseModel):
    quote: str
    source: str
    url: str
    domain: str
    credibility: float
    similarity: float
    stance: str

class ConfidenceBreakdown(BaseModel):
    dataset_prediction: float
    cross_encoder: float
    source_credibility: float
    semantic_similarity: float
    date_verification: float = 100.0
    evidence_consistency: float = 85.0
    trusted_source_ratio: float = 90.0

class HybridVerificationResponse(BaseModel):
    search_id: str
    claim: str
    verdict: str
    confidence: int
    summary: str
    reasoning: List[str]
    entities: Dict[str, str]
    average_similarity: float
    average_credibility: float
    average_cross_score: float
    retrieved_articles: int
    trusted_sources: int
    processing_time: float
    supporting_sources: List[SourceItem] = []
    contradicting_sources: List[SourceItem] = []
    neutral_sources: List[SourceItem] = []
    key_evidence: List[EvidenceItem] = []
    similar_claims: List[Dict[str, Any]] = []
    confidence_breakdown: ConfidenceBreakdown
    classifier_prediction: Dict[str, Any]
    media_bias_spectrum: Dict[str, Any]
    from_dataset: bool = False
    generated_at: str

class AdminStatsResponse(BaseModel):
    db_size_mb: float
    embedding_count: int
    cache_entries: int
    total_searches: int
    avg_latency_ms: float
    cache_hit_ratio_pct: float
    imported_datasets: List[Dict[str, Any]]
    system_status: str
    active_services: List[str]

class AnalyticsSummaryResponse(BaseModel):
    total_verified_claims: int
    verdict_counts: Dict[str, int]
    confidence_distribution: Dict[str, int]
    trending_misinformation: List[Dict[str, Any]]
    recent_claims: List[Dict[str, Any]]
