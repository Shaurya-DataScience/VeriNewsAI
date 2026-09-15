import os
import json
import csv
from typing import Tuple, List, Dict, Any

LABEL_MAP = {
    # LIAR Dataset labels
    "true": "TRUE",
    "mostly-true": "TRUE",
    "half-true": "MISLEADING",
    "barely-true": "MISLEADING",
    "false": "FALSE",
    "pants-fire": "FALSE",
    "pants on fire": "FALSE",
    
    # FEVER & SciFact & HealthVer Dataset labels
    "SUPPORTS": "TRUE",
    "SUPPORT": "TRUE",
    "REFUTES": "FALSE",
    "REFUTE": "FALSE",
    "CONTRADICT": "FALSE",
    "NOT ENOUGH INFO": "UNVERIFIED",
    "NOT_ENOUGH_INFO": "UNVERIFIED",
    "NEI": "UNVERIFIED",

    # MultiFC & Fact-Checking Portals (Snopes, PolitiFact, Washington Post, FullFact)
    "correct": "TRUE",
    "accurate": "TRUE",
    "inaccurate": "FALSE",
    "incorrect": "FALSE",
    "mixture": "MISLEADING",
    "half true": "MISLEADING",
    "mostly false": "MISLEADING",
    "mostly true": "TRUE",
    "unverified": "UNVERIFIED",
    "disputed": "MISLEADING",
    "legend": "MISLEADING",
    "fact": "TRUE",
    "fake": "FALSE",
    "blatant lie": "FALSE",
    "misleading": "MISLEADING",

    # Climate-FEVER & AVeriTeC labels
    "SUPPORTED": "TRUE",
    "REFUTED": "FALSE",
    "DISPUTED": "MISLEADING",
    "Supported": "TRUE",
    "Refuted": "FALSE",
    "Conflicting Evidence/Cherrypicking": "MISLEADING",
    "Conflicting Evidence/Cherry-picking": "MISLEADING",
    "Conflicting Evidence / Cherry-picking": "MISLEADING",
    "Not Enough Evidence": "UNVERIFIED",
    "Not Enough Info": "UNVERIFIED",
    "NEE": "UNVERIFIED",

    # Generic defaults
    "CONTRADICTING": "FALSE"
}

NUMERIC_LABEL_MAP = {
    "TRUE": 0,
    "FALSE": 1,
    "MISLEADING": 2,
    "UNVERIFIED": 3
}

REVERSE_NUMERIC_LABEL_MAP = {v: k for k, v in NUMERIC_LABEL_MAP.items()}

def normalize_label(label: str) -> str:
    """Normalize heterogeneous claim dataset labels into 4 standard categories."""
    if not label:
        return "UNVERIFIED"
    clean = str(label).strip().lower()
    for raw, normalized in LABEL_MAP.items():
        if raw.lower() == clean:
            return normalized
    if "true" in clean or "support" in clean:
        return "TRUE"
    if "false" in clean or "refut" in clean or "fire" in clean:
        return "FALSE"
    if "half" in clean or "barely" in clean or "mislead" in clean:
        return "MISLEADING"
    print(f"[Preprocessor] Unmapped label '{label}' default to UNVERIFIED")
    return "UNVERIFIED"

def load_fever(data_dir: str) -> List[Dict[str, Any]]:
    """Load FEVER jsonl dataset."""
    records = []
    fever_paths = [
        os.path.join(data_dir, "fever", "train.jsonl"),
        os.path.join(data_dir, "train.jsonl")
    ]
    for fpath in fever_paths:
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                        claim = obj.get("claim", "").strip()
                        raw_label = obj.get("label", "NOT ENOUGH INFO")
                        if claim:
                            records.append({
                                "claim": claim,
                                "verdict": normalize_label(raw_label),
                                "dataset": "fever",
                                "domain": "wikipedia",
                                "summary": f"FEVER Wikipedia fact-check record."
                            })
                    except Exception:
                        continue
            break
    return records

def load_liar(data_dir: str) -> List[Dict[str, Any]]:
    """Load LIAR tsv dataset."""
    records = []
    liar_dir = os.path.join(data_dir, "liar") if os.path.exists(os.path.join(data_dir, "liar")) else os.path.join(data_dir, "liar_dataset")
    if os.path.exists(liar_dir):
        for fname in ["train.tsv", "valid.tsv", "test.tsv"]:
            fpath = os.path.join(liar_dir, fname)
            if os.path.exists(fpath):
                try:
                    with open(fpath, "r", encoding="utf-8") as tsv_f:
                        reader = csv.reader(tsv_f, delimiter="\t")
                        for row in reader:
                            if len(row) >= 3:
                                raw_label = str(row[1])
                                statement = str(row[2]).strip()
                                if statement:
                                    records.append({
                                        "claim": statement,
                                        "verdict": normalize_label(raw_label),
                                        "dataset": "liar",
                                        "domain": "politics",
                                        "summary": f"LIAR political claim record."
                                    })
                except Exception:
                    continue
    return records

def load_multifc(data_dir: str) -> List[Dict[str, Any]]:
    """Load MultiFC dataset."""
    records = []
    multifc_dir = os.path.join(data_dir, "multifc")
    if os.path.exists(multifc_dir):
        for fname in os.listdir(multifc_dir):
            if fname.endswith(".tsv") or fname.endswith(".csv"):
                fpath = os.path.join(multifc_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        reader = csv.reader(f, delimiter="\t")
                        for row in reader:
                            if len(row) >= 2:
                                claim = row[0].strip()
                                label = row[1].strip()
                                if claim:
                                    records.append({
                                        "claim": claim,
                                        "verdict": normalize_label(label),
                                        "dataset": "multifc",
                                        "domain": "news-portals",
                                        "summary": "MultiFC portal claim record."
                                    })
                except Exception:
                    continue
    return records

def load_climate_fever(data_dir: str) -> List[Dict[str, Any]]:
    """Load Climate-FEVER dataset."""
    records = []
    cf_paths = [
        os.path.join(data_dir, "climate_fever", "climate_fever.jsonl"),
        os.path.join(data_dir, "climate_fever.jsonl")
    ]
    for fpath in cf_paths:
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                        claim = obj.get("claim", "").strip()
                        raw_label = obj.get("claim_label", "NOT_ENOUGH_INFO")
                        if claim:
                            records.append({
                                "claim": claim,
                                "verdict": normalize_label(raw_label),
                                "dataset": "climate_fever",
                                "domain": "climate",
                                "summary": "Climate-FEVER environmental claim record."
                            })
                    except Exception:
                        continue
            break
    return records

def load_scifact(data_dir: str) -> List[Dict[str, Any]]:
    """Load SciFact dataset."""
    records = []
    scifact_paths = [
        os.path.join(data_dir, "scifact", "claims_train.jsonl"),
        os.path.join(data_dir, "scifact", "claims_dev.jsonl"),
        os.path.join(data_dir, "scifact.jsonl")
    ]
    for fpath in scifact_paths:
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                        claim = obj.get("claim", "").strip()
                        # SciFact format uses evidence dictionary keys for verdicts or top-level verdict
                        raw_verdict = obj.get("verdict")
                        if not raw_verdict and "evidence" in obj:
                            ev = obj["evidence"]
                            if ev:
                                first_key = list(ev.keys())[0] if isinstance(ev, dict) else None
                                if first_key and isinstance(ev[first_key], list) and len(ev[first_key]) > 0:
                                    raw_verdict = ev[first_key][0].get("label", "NOT_ENOUGH_INFO")
                        if claim:
                            records.append({
                                "claim": claim,
                                "verdict": normalize_label(raw_verdict or "NOT_ENOUGH_INFO"),
                                "dataset": "scifact",
                                "domain": "science",
                                "summary": "SciFact scientific paper claim record."
                            })
                    except Exception:
                        continue
    return records

def load_healthver(data_dir: str) -> List[Dict[str, Any]]:
    """Load HealthVer dataset."""
    records = []
    hv_paths = [
        os.path.join(data_dir, "healthver", "healthver.jsonl"),
        os.path.join(data_dir, "healthver", "healthver.csv"),
        os.path.join(data_dir, "healthver.jsonl")
    ]
    for fpath in hv_paths:
        if os.path.exists(fpath):
            if fpath.endswith(".csv"):
                try:
                    with open(fpath, "r", encoding="utf-8") as csv_f:
                        reader = csv.DictReader(csv_f)
                        for row in reader:
                            claim = row.get("claim", "").strip()
                            label = row.get("label", "NOT ENOUGH INFO")
                            if claim:
                                records.append({
                                    "claim": claim,
                                    "verdict": normalize_label(label),
                                    "dataset": "healthver",
                                    "domain": "medical-health",
                                    "summary": "HealthVer public health evidence claim record."
                                })
                except Exception:
                    continue
            else:
                with open(fpath, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            obj = json.loads(line)
                            claim = obj.get("claim", "").strip()
                            label = obj.get("label", "NOT ENOUGH INFO")
                            if claim:
                                records.append({
                                    "claim": claim,
                                    "verdict": normalize_label(label),
                                    "dataset": "healthver",
                                    "domain": "medical-health",
                                    "summary": "HealthVer medical claim record."
                                })
                        except Exception:
                            continue
    return records

def load_snopes(data_dir: str) -> List[Dict[str, Any]]:
    """Load Snopes urban myths and viral rumors dataset."""
    records = []
    paths = [
        os.path.join(data_dir, "snopes", "snopes.jsonl"),
        os.path.join(data_dir, "snopes", "snopes.csv"),
        os.path.join(data_dir, "snopes.jsonl")
    ]
    for fpath in paths:
        if os.path.exists(fpath):
            if fpath.endswith(".csv"):
                try:
                    with open(fpath, "r", encoding="utf-8") as csv_f:
                        reader = csv.DictReader(csv_f)
                        for row in reader:
                            claim = row.get("claim", row.get("fact_check_claim", "")).strip()
                            label = row.get("rating", row.get("label", "UNVERIFIED"))
                            if claim:
                                records.append({
                                    "claim": claim,
                                    "verdict": normalize_label(label),
                                    "dataset": "snopes",
                                    "domain": "viral-myths",
                                    "summary": row.get("summary", "Snopes myth fact check record.")
                                })
                except Exception:
                    continue
            else:
                with open(fpath, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            obj = json.loads(line)
                            claim = obj.get("claim", obj.get("claim_text", "")).strip()
                            label = obj.get("rating", obj.get("label", "UNVERIFIED"))
                            if claim:
                                records.append({
                                    "claim": claim,
                                    "verdict": normalize_label(label),
                                    "dataset": "snopes",
                                    "domain": "viral-myths",
                                    "summary": obj.get("summary", "Snopes urban legend record.")
                                })
                        except Exception:
                            continue
    return records

def load_politifact(data_dir: str) -> List[Dict[str, Any]]:
    """Load PolitiFact political claims dataset."""
    records = []
    paths = [
        os.path.join(data_dir, "politifact", "politifact.jsonl"),
        os.path.join(data_dir, "politifact", "politifact.csv"),
        os.path.join(data_dir, "politifact.jsonl")
    ]
    for fpath in paths:
        if os.path.exists(fpath):
            if fpath.endswith(".csv"):
                try:
                    with open(fpath, "r", encoding="utf-8") as csv_f:
                        reader = csv.DictReader(csv_f)
                        for row in reader:
                            claim = row.get("statement", row.get("claim", "")).strip()
                            label = row.get("verdict", row.get("label", "UNVERIFIED"))
                            if claim:
                                records.append({
                                    "claim": claim,
                                    "verdict": normalize_label(label),
                                    "dataset": "politifact",
                                    "domain": "politics",
                                    "summary": row.get("statement_originator", "PolitiFact political claim record.")
                                })
                except Exception:
                    continue
            else:
                with open(fpath, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            obj = json.loads(line)
                            claim = obj.get("statement", obj.get("claim", "")).strip()
                            label = obj.get("verdict", obj.get("label", "UNVERIFIED"))
                            if claim:
                                records.append({
                                    "claim": claim,
                                    "verdict": normalize_label(label),
                                    "dataset": "politifact",
                                    "domain": "politics",
                                    "summary": "PolitiFact political statement record."
                                })
                        except Exception:
                            continue
    return records

def load_pubhealth(data_dir: str) -> List[Dict[str, Any]]:
    """Load PubHealth public health research dataset."""
    records = []
    paths = [
        os.path.join(data_dir, "pubhealth", "train.tsv"),
        os.path.join(data_dir, "pubhealth", "pubhealth.jsonl"),
        os.path.join(data_dir, "pubhealth.jsonl")
    ]
    for fpath in paths:
        if os.path.exists(fpath):
            if fpath.endswith(".tsv"):
                try:
                    with open(fpath, "r", encoding="utf-8") as tsv_f:
                        reader = csv.DictReader(tsv_f, delimiter="\t")
                        for row in reader:
                            claim = row.get("claim", "").strip()
                            label = row.get("label", "UNVERIFIED")
                            if claim:
                                records.append({
                                    "claim": claim,
                                    "verdict": normalize_label(label),
                                    "dataset": "pubhealth",
                                    "domain": "public-health",
                                    "summary": row.get("explanation", "PubHealth scientific claim record.")
                                })
                except Exception:
                    continue
            else:
                with open(fpath, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            obj = json.loads(line)
                            claim = obj.get("claim", "").strip()
                            label = obj.get("label", "UNVERIFIED")
                            if claim:
                                records.append({
                                    "claim": claim,
                                    "verdict": normalize_label(label),
                                    "dataset": "pubhealth",
                                    "domain": "public-health",
                                    "summary": obj.get("explanation", "PubHealth public health record.")
                                })
                        except Exception:
                            continue
    return records

def load_averitec(data_dir: str) -> List[Dict[str, Any]]:
    """
    Load AVeriTeC (Automated Verification of Textual Claims) dataset.
    Converts AVeriTeC train.json, dev.json, test.json into common normalized schema.
    Preserves question-answer evidence pairs, source URLs, justification summaries, and speaker metadata.
    """
    records = []
    averitec_dir = os.path.join(data_dir, "averitec")
    candidate_files = []

    if os.path.exists(averitec_dir):
        for fname in ["train.json", "dev.json", "test.json", "averitec.json", "averitec.jsonl"]:
            fpath = os.path.join(averitec_dir, fname)
            if os.path.exists(fpath):
                candidate_files.append(fpath)

    for fallback_name in ["averitec.json", "averitec.jsonl"]:
        root_fpath = os.path.join(data_dir, fallback_name)
        if os.path.exists(root_fpath) and root_fpath not in candidate_files:
            candidate_files.append(root_fpath)

    for fpath in candidate_files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                if fpath.endswith(".jsonl"):
                    items = [json.loads(line) for line in f if line.strip()]
                else:
                    items = json.load(f)
                    if isinstance(items, dict):
                        items = [items]

                for item in items:
                    claim = item.get("claim", "").strip()
                    if not claim:
                        continue

                    raw_label = item.get("label", item.get("pred_label", "UNVERIFIED"))
                    norm_label = normalize_label(raw_label)

                    # Extract all evidence items from QA pairs & justification
                    evidence_list = []
                    justification = item.get("justification", "").strip()
                    if justification:
                        evidence_list.append(justification)

                    questions = item.get("questions", [])
                    source_urls = []
                    if item.get("fact_checking_article"):
                        source_urls.append(item["fact_checking_article"])
                    if item.get("original_claim_url"):
                        source_urls.append(item["original_claim_url"])

                    for q_obj in questions:
                        q_text = q_obj.get("question", "").strip()
                        for a_obj in q_obj.get("answers", []):
                            ans = a_obj.get("answer", "").strip()
                            s_url = a_obj.get("source_url") or a_obj.get("url")
                            snippet = a_obj.get("text") or a_obj.get("scraped_text") or ""
                            if s_url and s_url not in source_urls:
                                source_urls.append(s_url)
                            if ans:
                                evidence_list.append(f"Q: {q_text} | A: {ans}")
                            elif snippet:
                                evidence_list.append(str(snippet)[:300])

                    primary_url = source_urls[0] if source_urls else ""
                    speaker = item.get("speaker") or item.get("reporting_source") or "AVeriTeC"
                    summary_text = justification or (f"AVeriTeC verified claim: {raw_label}." if raw_label else "AVeriTeC evidence claim.")

                    records.append({
                        "claim": claim,
                        "label": norm_label,
                        "verdict": norm_label,
                        "evidence": evidence_list,
                        "source": speaker,
                        "source_url": primary_url,
                        "summary": summary_text,
                        "dataset": "averitec",
                        "domain": "general",
                        "metadata": {
                            "claim_date": item.get("claim_date"),
                            "speaker": item.get("speaker"),
                            "claim_types": item.get("claim_types", []),
                            "fact_checking_strategies": item.get("fact_checking_strategies", []),
                            "source_urls": source_urls
                        }
                    })
        except Exception as e:
            print(f"[Preprocessor] Error loading AVeriTeC file {fpath}: {e}")

    return records

def load_and_preprocess_datasets(data_dir: str) -> Tuple[List[str], List[int]]:
    """
    Unified dataset loader across FEVER, LIAR, MultiFC, Climate-FEVER, SciFact, HealthVer, Snopes, PolitiFact, PubHealth, and AVeriTeC.
    Returns (texts, labels).
    """
    all_records: List[Dict[str, Any]] = []

    all_records.extend(load_fever(data_dir))
    all_records.extend(load_liar(data_dir))
    all_records.extend(load_multifc(data_dir))
    all_records.extend(load_climate_fever(data_dir))
    all_records.extend(load_scifact(data_dir))
    all_records.extend(load_healthver(data_dir))
    all_records.extend(load_snopes(data_dir))
    all_records.extend(load_politifact(data_dir))
    all_records.extend(load_pubhealth(data_dir))
    all_records.extend(load_averitec(data_dir))

    # Fallback seed claims if external datasets not present
    if not all_records:
        print("[Preprocessor] No external datasets found. Loading seed verified dataset...")
        seed_path = os.path.join(data_dir, "verified_dataset.json")
        if os.path.exists(seed_path):
            with open(seed_path, "r", encoding="utf-8") as f:
                seed_data = json.load(f)
                for item in seed_data:
                    all_records.append({
                        "claim": item["claim"],
                        "verdict": normalize_label(item["verdict"]),
                        "dataset": "verified_seed",
                        "domain": "general",
                        "summary": item.get("summary", "Seed claim.")
                    })

    # Cross-dataset Deduplication via Exact & Normalized Text Matching
    seen_claims = set()
    dedup_records = []
    for r in all_records:
        norm_key = r["claim"].strip().lower()
        if norm_key not in seen_claims:
            seen_claims.add(norm_key)
            dedup_records.append(r)

    texts = [r["claim"] for r in dedup_records]
    labels = [NUMERIC_LABEL_MAP[r["verdict"]] for r in dedup_records]

    # Print summary reports per dataset and label distribution
    dataset_counts: Dict[str, int] = {}
    label_counts: Dict[str, int] = {"TRUE": 0, "FALSE": 0, "MISLEADING": 0, "UNVERIFIED": 0}

    for r in dedup_records:
        ds = r["dataset"]
        dataset_counts[ds] = dataset_counts.get(ds, 0) + 1
        label_counts[r["verdict"]] = label_counts.get(r["verdict"], 0) + 1

    print("\n--- DATASET SUMMARY REPORT ---")
    for ds_name, count in dataset_counts.items():
        print(f"  {ds_name.upper()}: {count} claims")
    print("\n--- CLASS DISTRIBUTION ---")
    for lbl, count in label_counts.items():
        print(f"  {lbl}: {count}")
    print(f"TOTAL UNIQUE CLAIMS: {len(texts)}\n")

    return texts, labels
