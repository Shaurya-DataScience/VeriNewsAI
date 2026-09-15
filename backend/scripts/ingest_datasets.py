# ============================================================
# VeriNews AI - Universal Dataset Ingestion Engine v2.0
# High-Speed Batch Import for FEVER (.jsonl) & LIAR (.tsv/.csv)
# ============================================================

import os
import sys
import json
import csv
import argparse
from datetime import datetime

# Adjust Python path to load backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database
from services.verifier import embedding_model

def normalize_verdict(label: str) -> str:
    """Normalize dataset verdict labels into standard VeriNews AI verdicts."""
    l_lower = str(label).lower().strip()
    if any(w in l_lower for w in ["true", "supports", "supported", "mostly-true"]):
        return "TRUE"
    elif any(w in l_lower for w in ["false", "refutes", "refuted", "pants-fire", "pants-on-fire", "barely-true"]):
        return "FALSE"
    elif any(w in l_lower for w in ["mixture", "half-true", "misleading", "unproven"]):
        return "MISLEADING"
    else:
        return "UNVERIFIED"

def ingest_file(file_path: str, limit: int = 1000):
    """Ingest dataset from JSON, JSONL, TSV, or CSV file into SQLite DB."""
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at {file_path}")
        return

    print(f"📥 Loading dataset file from {file_path}...")
    claims_to_insert = []

    # Parse TSV / CSV (LIAR Dataset format)
    if file_path.endswith(".tsv") or file_path.endswith(".csv"):
        delimiter = "\t" if file_path.endswith(".tsv") else ","
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f, delimiter=delimiter)
            for row in reader:
                if len(row) >= 3:
                    # LIAR TSV format: col 0 = ID, col 1 = label, col 2 = statement
                    claims_to_insert.append({
                        "id": row[0],
                        "label": row[1],
                        "claim": row[2],
                        "subject": row[3] if len(row) > 3 else "General"
                    })
    # Parse JSONL / JSON (FEVER format)
    elif file_path.endswith(".jsonl"):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.strip():
                    claims_to_insert.append(json.loads(line))
    else:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            claims_to_insert = json.load(f)

    if limit and limit > 0:
        claims_to_insert = claims_to_insert[:limit]

    print(f"⚙️ Ingesting {len(claims_to_insert)} claims into VeriNews AI Vector Database...")
    inserted_count = 0

    for idx, item in enumerate(claims_to_insert):
        claim_text = item.get("claim") or item.get("statement") or item.get("text", "")
        if not claim_text or len(str(claim_text).strip()) < 10:
            continue

        # Skip existing claims to prevent duplicates
        if database.claim_exists(str(claim_text)):
            continue

        raw_label = item.get("verdict") or item.get("label") or item.get("label_text", "UNVERIFIED")
        verdict = normalize_verdict(raw_label)
        confidence = item.get("confidence", 95 if verdict in ["TRUE", "FALSE"] else 80)
        summary = item.get("summary") or item.get("evidence") or f"Verified via dataset record ({raw_label})."
        
        if isinstance(summary, list):
            summary = " ".join([str(s) for s in summary[:3]])

        claim_id = item.get("id") or f"ingest_{idx}_{int(datetime.now().timestamp())}"

        # Generate vector embedding
        vec = embedding_model.encode([claim_text])[0]
        norm = float(sum(v*v for v in vec)**0.5)
        if norm > 0:
            vec = [float(v/norm) for v in vec]
        else:
            vec = [float(v) for v in vec]

        # Save to database
        database.save_claim_embedding(
            str(claim_id), str(claim_text), vec, verdict, confidence, str(summary), datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        inserted_count += 1

        if (idx + 1) % 100 == 0 or (idx + 1) == len(claims_to_insert):
            print(f"  ➜ Progress: {idx + 1} / {len(claims_to_insert)} claims processed...")

    print(f"✅ Ingestion Complete! Successfully indexed {inserted_count} claims into VeriNews AI Database.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VeriNews AI Universal Dataset Ingestion Engine")
    parser.add_argument("--file", type=str, help="Path to JSON, JSONL, TSV, or CSV dataset file", required=False)
    parser.add_argument("--limit", type=int, default=1000, help="Maximum number of claims to ingest")
    args = parser.parse_args()

    if args.file:
        ingest_file(args.file, args.limit)
    else:
        default_seed = os.path.join(os.path.dirname(__file__), "..", "data", "verified_dataset.json")
        ingest_file(default_seed, limit=0)
