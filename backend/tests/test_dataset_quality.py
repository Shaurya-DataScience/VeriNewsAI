import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from training.dataset_preprocessor import (
    normalize_label, load_fever, load_liar, load_multifc,
    load_climate_fever, load_scifact, load_healthver,
    load_and_preprocess_datasets, NUMERIC_LABEL_MAP
)

def test_label_normalization_quality():
    assert normalize_label("true") == "TRUE"
    assert normalize_label("SUPPORTS") == "TRUE"
    assert normalize_label("SUPPORT") == "TRUE"
    assert normalize_label("false") == "FALSE"
    assert normalize_label("pants on fire") == "FALSE"
    assert normalize_label("mixture") == "MISLEADING"
    assert normalize_label("disputed") == "MISLEADING"
    assert normalize_label("unknown_gibberish_label_xyz") == "UNVERIFIED"

def test_loader_functions():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    fever_res = load_fever(data_dir)
    liar_res = load_liar(data_dir)
    scifact_res = load_scifact(data_dir)
    healthver_res = load_healthver(data_dir)

    assert isinstance(fever_res, list)
    assert isinstance(liar_res, list)
    assert isinstance(scifact_res, list)
    assert isinstance(healthver_res, list)

def test_unified_dataset_preprocessing_and_dedup():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    texts, labels = load_and_preprocess_datasets(data_dir)

    assert len(texts) == len(labels)
    assert len(texts) > 0
    # Verify no duplicate claim strings exist in unified preprocessed output
    assert len(texts) == len(set([t.strip().lower() for t in texts]))
    # Verify labels are restricted to standard 0, 1, 2, 3 indices
    assert set(labels).issubset({0, 1, 2, 3})
