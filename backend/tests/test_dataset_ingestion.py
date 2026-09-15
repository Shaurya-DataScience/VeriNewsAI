import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from training.dataset_preprocessor import normalize_label
from training.ingest_multi_datasets import ingest_claims_into_db
from database import get_connection, init_db

def test_multifc_label_normalization():
    assert normalize_label("mixture") == "MISLEADING"
    assert normalize_label("pants on fire") == "FALSE"
    assert normalize_label("correct") == "TRUE"
    assert normalize_label("legend") == "MISLEADING"
    assert normalize_label("unverified") == "UNVERIFIED"

def test_dataset_ingestion_and_deduplication():
    init_db()
    
    # Pre-clean any leftover test records
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM claims WHERE claim LIKE 'Unique test claim%'")
    conn.commit()
    conn.close()

    test_claims = [
        {"claim": "Unique test claim for dataset ingestion 101", "verdict": "TRUE", "domain": "test"},
        {"claim": "Unique test claim for dataset ingestion 102", "verdict": "FALSE", "domain": "test"}
    ]

    # First run: should insert
    res1 = ingest_claims_into_db(test_claims)
    assert res1["inserted"] == 2
    assert res1["skipped_duplicates"] == 0

    # Second run with exact same dataset: should skip duplicates
    res2 = ingest_claims_into_db(test_claims)
    assert res2["inserted"] == 0
    assert res2["skipped_duplicates"] == 2

    # Clean up test records
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM claims WHERE claim LIKE 'Unique test claim%'")
    conn.commit()
    conn.close()
