import os
import sys
import json
import sqlite3
import hashlib
from typing import List, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import get_connection, init_db
from training.dataset_preprocessor import (
    load_fever, load_liar, load_multifc, load_climate_fever,
    load_scifact, load_healthver, load_snopes, load_politifact, load_pubhealth, load_averitec, normalize_label
)

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
except Exception as e:
    print(f"[Ingester] Warning: SentenceTransformer failed to load: {e}")
    EMBEDDER = None

MULTI_DOMAIN_SEED_CLAIMS = [
    # SciFact & HealthVer & PubHealth
    {"claim": "mRNA COVID-19 vaccines alter human DNA", "verdict": "FALSE", "dataset": "healthver", "domain": "medical-health", "summary": "CDC and WHO confirm mRNA vaccines do not enter the cell nucleus and cannot alter human DNA."},
    {"claim": "Antibiotics are effective in treating viral infections", "verdict": "FALSE", "dataset": "scifact", "domain": "science", "summary": "Antibiotics target bacteria, not viruses like influenza or SARS-CoV-2."},
    {"claim": "Vitamin C prevents human coronavirus infection", "verdict": "MISLEADING", "dataset": "healthver", "domain": "medical-health", "summary": "Vitamin C supports immune health but has no proven preventive efficacy against COVID-19."},
    {"claim": "CRISPR gene editing was used to treat sickle cell disease", "verdict": "TRUE", "dataset": "scifact", "domain": "science", "summary": "FDA approved Casgevy, a landmark CRISPR-based gene therapy for sickle cell disease in 2023."},
    {"claim": "Drinking bleach cures viral and bacterial infections", "verdict": "FALSE", "dataset": "pubhealth", "domain": "public-health", "summary": "FDA and CDC warn that consuming industrial bleach causes severe chemical burns and organ failure."},

    # Climate-FEVER
    {"claim": "Global sea levels have risen by over 20 centimeters since 1880", "verdict": "TRUE", "dataset": "climate_fever", "domain": "climate", "summary": "NASA and NOAA satellite data confirm global mean sea level has risen ~21-24 cm since 1880."},
    {"claim": "Volcanoes emit more carbon dioxide annually than human industry", "verdict": "FALSE", "dataset": "climate_fever", "domain": "climate", "summary": "Human activities release ~35 billion metric tons of CO2 yearly, 100x more than all volcanoes combined."},
    {"claim": "Solar and wind energy cause permanent power grid instability", "verdict": "MISLEADING", "dataset": "climate_fever", "domain": "climate", "summary": "Variable renewables require battery storage and grid management but do not cause inherent failure."},
    
    # MultiFC & LIAR & FEVER & PolitiFact & Snopes
    {"claim": "5G networks broadcast radiation that causes viral outbreaks", "verdict": "FALSE", "dataset": "multifc", "domain": "tech-factcheck", "summary": "Radiofrequency waves from 5G cell towers are non-ionizing and biologically incapable of transmitting viruses."},
    {"claim": "The Great Wall of China is visible from orbit with the naked eye", "verdict": "FALSE", "dataset": "fever", "domain": "wikipedia", "summary": "Astronauts and NASA confirm the Great Wall is not visible to the naked human eye from low Earth orbit."},
    {"claim": "Electric vehicles have zero total lifetime carbon footprint", "verdict": "MISLEADING", "dataset": "liar", "domain": "politics", "summary": "EVs produce zero tailpipe emissions but battery manufacturing and electricity grid sources create upstream carbon."},
    {"claim": "NASA faked the 1969 Apollo moon landing in a Hollywood studio", "verdict": "FALSE", "dataset": "snopes", "domain": "viral-myths", "summary": "Overwhelming scientific proof, laser retroreflectors, and 382 kg of returned lunar samples verify Apollo landings."},
    {"claim": "US President Abraham Lincoln signed the Emancipation Proclamation in 1863", "verdict": "TRUE", "dataset": "politifact", "domain": "politics", "summary": "Official historical record confirms Lincoln issued the final Emancipation Proclamation on Jan 1, 1863."}
]

def ingest_claims_into_db(claims_data: List[Dict[str, Any]]) -> Dict[str, int]:
    """Ingest dataset claim dictionaries into SQLite DB claims table with deduplication."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    inserted_count = 0
    skipped_count = 0

    for item in claims_data:
        claim = item.get("claim", "").strip()
        if not claim:
            continue

        raw_verdict = item.get("verdict", "UNVERIFIED")
        verdict = normalize_label(raw_verdict)
        dataset_name = item.get("dataset", "general")
        domain_name = item.get("domain", "general")
        summary_text = item.get("summary", "")

        claim_hash = hashlib.md5(claim.lower().encode("utf-8")).hexdigest()

        cursor.execute("SELECT claim_id FROM claims WHERE claim_id = ? OR claim = ?", (claim_hash, claim))
        if cursor.fetchone():
            skipped_count += 1
            continue

        if EMBEDDER:
            emb = EMBEDDER.encode(claim).tolist()
            emb_json = json.dumps(emb)
        else:
            emb_json = json.dumps([])

        try:
            cursor.execute("""
                INSERT OR IGNORE INTO claims (claim_id, claim, embedding_json, verdict, confidence, summary, dataset, domain)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (claim_hash, claim, emb_json, verdict, 90.0, summary_text, dataset_name, domain_name))
            inserted_count += 1
        except Exception:
            skipped_count += 1

    conn.commit()
    conn.close()

    result_summary = {
        "total_processed": len(claims_data),
        "inserted": inserted_count,
        "skipped_duplicates": skipped_count
    }
    print(f"[Ingester] Done: {inserted_count} new claims inserted, {skipped_count} duplicates skipped.")
    return result_summary

def ingest_all_datasets(data_dir: str):
    """Load and ingest claims across FEVER, LIAR, MultiFC, Climate-FEVER, SciFact, HealthVer, Snopes, PolitiFact, PubHealth, and AVeriTeC."""
    print(f"[Ingester] Loading all 10 datasets from {data_dir}...")
    records: List[Dict[str, Any]] = []

    records.extend(load_fever(data_dir))
    records.extend(load_liar(data_dir))
    records.extend(load_multifc(data_dir))
    records.extend(load_climate_fever(data_dir))
    records.extend(load_scifact(data_dir))
    records.extend(load_healthver(data_dir))
    records.extend(load_snopes(data_dir))
    records.extend(load_politifact(data_dir))
    records.extend(load_pubhealth(data_dir))
    records.extend(load_averitec(data_dir))

    if not records:
        print("[Ingester] No external dataset files found. Ingesting multi-domain seed dataset...")
        records = MULTI_DOMAIN_SEED_CLAIMS

    return ingest_claims_into_db(records)

if __name__ == "__main__":
    data_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    ingest_all_datasets(data_directory)
