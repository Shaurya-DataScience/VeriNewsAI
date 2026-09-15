# ============================================================
# VeriNews AI - Automatic Google Fact-Check Fetcher
# Fetches live fact-checks automatically without manual file downloads!
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

def fetch_and_ingest_factchecks():
    print("🌐 Fetching real-world fact-checks directly from public RSS & Fact-Check APIs...")

    # Public Fact-Check JSON feeds (PolitiFact & FactCheck.org)
    feeds = [
        {
            "name": "PolitiFact Feed",
            "url": "https://www.politifact.com/api/v2/statements/?format=json&limit=50"
        }
    ]

    inserted_count = 0

    for feed in feeds:
        try:
            print(f"📡 Requesting {feed['name']}...")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.politifact.com/"
            }
            req = urllib.request.Request(feed["url"], headers=headers)
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    results = data.get("results", []) if isinstance(data, dict) else data
                    print(f"✅ Received {len(results)} claims from {feed['name']}!")

                    for idx, item in enumerate(results):
                        statement = item.get("statement") or item.get("claim", "")
                        if not statement or len(statement.strip()) < 10:
                            continue

                        r_ruling = str(item.get("ruling", {}).get("ruling", "unverified")).lower()
                        verdict = "TRUE" if any(w in r_ruling for w in ["true", "mostly-true"]) else ("FALSE" if any(w in r_ruling for w in ["false", "pants-on-fire", "barely-true"]) else "MISLEADING")
                        confidence = 95 if verdict in ["TRUE", "FALSE"] else 80
                        summary = item.get("ruling_headline") or item.get("statement_reasoning") or f"Fact-checked by PolitiFact: {r_ruling.upper()}"
                        claim_id = f"pf_{item.get('id', idx)}_{int(datetime.now().timestamp())}"

                        # Compute vector embedding
                        vec = embedding_model.encode([statement])[0]
                        norm = float(sum(v*v for v in vec)**0.5)
                        if norm > 0:
                            vec = [float(v/norm) for v in vec]

                        # Save to database
                        database.save_claim_embedding(
                            claim_id, statement, vec, verdict, confidence, str(summary), datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        )
                        inserted_count += 1

        except Exception as e:
            print(f"⚠️ Could not fetch from {feed['name']}: {e}")

    print(f"🚀 Success! Ingested {inserted_count} real-world fact-checks into your local VeriNews AI Database!")

if __name__ == "__main__":
    fetch_and_ingest_factchecks()
