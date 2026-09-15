# VeriNews AI — Intelligent Hybrid Fact Verification Engine (Phase 2)

**VeriNews AI** is an enterprise-grade AI fact verification platform that combines local vector similarity search, fine-tuned DistilBERT claim classification (LIAR + FEVER), neural Cross-Encoder re-ranking, domain credibility scoring, and live Tavily web retrieval into an explainable, weighted ensemble engine.

---

## 🚀 Architecture & Verification Pipeline

```
                              +------------------------+
                              |   User Input Claim     |
                              +-----------+------------+
                                          |
                                          v
                            +-------------+------------+
                            |  SentenceTransformer     |
                            | (all-MiniLM-L6-v2 Embed) |
                            +-------------+------------+
                                          |
                                          v
                            +-------------+------------+
                            |  Local Vector DB Search  |
                            |   (SQLite Cosine Sim)    |
                            +-------------+------------+
                                          |
                               Top-5 Similar Claims & 
                               Cross-Encoder Rerank
                                          |
                  +-----------------------+-----------------------+
                  |                                               |
         Similarity > 90%?                                 Similarity <= 90%
                  |                                               |
                  v                                               v
      +-----------+-----------+                       +-----------+-----------+
      | Return Local Match    |                       | Live Tavily Web Search   |
      | (0 API Cost, <15ms)   |                       | + Evidence Extraction     |
      +-----------+-----------+                       +-----------+-----------+
                  |                                               |
                  +-----------------------+-----------------------+
                                          |
                                          v
                            +-------------+------------+
                            | DistilBERT Classification|
                            | (TRUE, FALSE,           |
                            |  MISLEADING, UNVERIFIED) |
                            +-------------+------------+
                                          |
                                          v
                            +-------------+------------+
                            | Configurable Weighted    |
                            |     Confidence Engine    |
                            | 35% DistilBERT           |
                            | 30% Cross-Encoder        |
                            | 20% Source Credibility   |
                            | 15% Vector Similarity    |
                            +-------------+------------+
                                          |
                                          v
                            +-------------+------------+
                            | Explainable AI Payload   |
                            | + Admin & Analytics DB   |
                            +--------------------------+
```

---

## 🛠️ Key Features

1. **Local Vector Search & Short-Circuit**: Pre-indexed claim search using `SentenceTransformer` embeddings and cosine similarity. Queries matching existing verified claims at $>90\%$ confidence short-circuit in $<15\text{ms}$ with zero Tavily API consumption.
2. **Fine-Tuned Claim Classifier**: Classifies claims into `TRUE`, `FALSE`, `MISLEADING`, and `UNVERIFIED` using DistilBERT / PyTorch trained on FEVER & LIAR datasets.
3. **Weighted Confidence Engine**:
   - **Dataset Prediction**: 35%
   - **Cross-Encoder Neural Rerank**: 30%
   - **Source Credibility Index**: 20%
   - **Semantic Similarity**: 15%
   *(Weights are dynamically configurable via Admin Panel)*
4. **Explainable AI (XAI)**: Returns complete audit trails including top historical similar claims, sentence-level evidence quotes, publisher stance spectrum, and confidence breakdown.
5. **Admin System Dashboard**: Real-time DB disk size tracking, vector embedding counts, cache hit ratios, search latency metrics, and ensemble weight controls.
6. **Public Analytics**: System telemetry, total verified claims, True vs False breakdown, and trending misinformation feeds.

---

## 📁 Repository Structure

```
VeriNewsAI/
├── backend/
│   ├── api/                  # FastAPI Modular Routers
│   │   ├── admin.py          # Admin Stats & Config Endpoints
│   │   ├── analytics.py      # Telemetry & Analytics Endpoints
│   │   └── verification.py   # Hybrid Verification & Search Endpoints
│   ├── data/                 # Ingested Datasets (LIAR, FEVER, Seed)
│   ├── migrations/           # Schema Migrations
│   │   └── migrate_v2.py     # SQLite Phase 2 Migration Script
│   ├── models/               # Pydantic Schemas & ML Checkpoints
│   │   ├── schemas.py
│   │   └── distilbert_factchecker/
│   ├── services/             # Core Verification Services
│   │   ├── classifier.py     # DistilBERT & Centroid Inference
│   │   ├── confidence_engine.py # Weighted Scoring Engine
│   │   ├── hybrid_verifier.py# Phase 2 Intelligent Hybrid Pipeline
│   │   ├── search.py         # Tavily Search Engine
│   │   ├── similarity_search.py # Vector Matcher
│   │   └── verifier.py       # Cross-Encoder & Bias Spectrum
│   ├── training/             # Machine Learning Training Pipeline
│   │   ├── dataset_preprocessor.py # LIAR + FEVER Preprocessing
│   │   └── train_classifier.py     # DistilBERT PyTorch Trainer
│   ├── database.py           # SQLite Core & Analytics Logger
│   ├── main.py               # FastAPI Main Application
│   └── verinews_cache.db     # SQLite Database
└── frontend/
    ├── index.html            # Main HTML UI & Dashboards
    ├── style.css             # Design Tokens & Stylesheet
    └── script.js             # Antigravity Dashboard Controller
```

---

## ⚡ Quick Start

### 1. Run Database Migrations
```bash
python backend/migrations/migrate_v2.py
```

### 2. Train the DistilBERT Classifier (Optional)
```bash
python backend/training/train_classifier.py --epochs 2 --max_samples 500
```

### 3. Start Backend Server
```bash
cd backend
.\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Launch Frontend
Open `frontend/index.html` in your web browser or serve via live server.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/verify` | Hybrid verification pipeline execution |
| `GET` | `/api/search?query=...` | Query claim search & verification |
| `GET` | `/api/admin/stats` | Database size, embeddings, latency, and hit ratio |
| `POST` | `/api/admin/config` | Update dynamic ensemble weights |
| `GET` | `/api/analytics/summary` | Telemetry, verdict counts, and trending misinformation |
| `GET` | `/stream_summary/{search_id}` | Real-time SSE summary streaming |
| `GET` | `/health` | System health check |
