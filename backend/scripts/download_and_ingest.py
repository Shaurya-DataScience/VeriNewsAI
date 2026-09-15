# ============================================================
# VeriNews AI - Automated Dataset Downloader & Ingestion Engine
# Direct HTTPS Stream Ingestion for HuggingFace & GitHub Repos
# ============================================================

import os
import sys
import json
import urllib.request
from datetime import datetime

# Adjust Python path to load backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database
from services.verifier import embedding_model

DATASETS = [
    {
        "name": "Climate & Environment Science Claims (Climate-FEVER)",
        "url": "https://huggingface.co/datasets/climate_fever/resolve/main/climate_fever.jsonl",
        "format": "jsonl",
        "limit": 1000
    },
    {
        "name": "Health & Medical Misinformation Corpus",
        "url": "https://raw.githubusercontent.com/diptamath/covid_fake_news/main/Constraint_Train.csv",
        "format": "csv",
        "limit": 1000
    }
]

def download_and_ingest():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(data_dir, exist_ok=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    total_ingested = 0

    for ds in DATASETS:
        print(f"\n📥 Downloading dataset: {ds['name']}...")
        dest_filename = os.path.basename(ds['url'])
        dest_path = os.path.join(data_dir, dest_filename)

        try:
            req = urllib.request.Request(ds["url"], headers=headers)
            with urllib.request.urlopen(req) as response, open(dest_path, "wb") as out_file:
                out_file.write(response.read())
            print(f"✅ Saved to {dest_path}")

            # Process & Ingest
            claims = []
            if ds["format"] == "jsonl":
                with open(dest_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if line.strip():
                            claims.append(json.loads(line))
            elif ds["format"] == "csv":
                import csv
                with open(dest_path, "r", encoding="utf-8", errors="ignore") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        claims.append({
                            "claim": row.get("tweet") or row.get("claim") or row.get("text", ""),
                            "label": row.get("label", "fake")
                        })

            limit = ds["limit"]
            claims = claims[:limit]
            print(f"⚙️ Ingesting {len(claims)} claims into VeriNews AI Vector Database...")

            for idx, item in enumerate(claims):
                claim_text = item.get("claim") or item.get("statement") or item.get("text", "")
                if not claim_text or len(str(claim_text).strip()) < 10:
                    continue

                if database.claim_exists(str(claim_text)):
                    continue

                raw_label = item.get("verdict") or item.get("label") or "fake"
                verdict = "FALSE" if any(w in str(raw_label).lower() for w in ["fake", "false", "refutes"]) else "TRUE"
                confidence = 95 if verdict in ["TRUE", "FALSE"] else 80
                summary = f"Verified dataset record ({raw_label})."
                claim_id = f"auto_{idx}_{int(datetime.now().timestamp())}"

                vec = embedding_model.encode([claim_text])[0]
                norm = float(sum(v*v for v in vec)**0.5)
                if norm > 0:
                    vec = [float(v/norm) for v in vec]

                database.save_claim_embedding(
                    str(claim_id), str(claim_text), vec, verdict, confidence, str(summary), datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                total_ingested += 1

                if (idx + 1) % 200 == 0 or (idx + 1) == len(claims):
                    print(f"  ➜ Progress: {idx + 1} / {len(claims)} claims processed...")

        except Exception as e:
            print(f"⚠️ Failed to download/ingest {ds['name']}: {e}")

    print(f"\n🎉 ALL DONE! Total new claims indexed offline: {total_ingested}")

if __name__ == "__main__":
    download_and_ingest()
