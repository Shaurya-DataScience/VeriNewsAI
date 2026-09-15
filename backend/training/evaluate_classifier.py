import os
import sys
import numpy as np
from typing import Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from training.dataset_preprocessor import (
    load_and_preprocess_datasets, NUMERIC_LABEL_MAP, REVERSE_NUMERIC_LABEL_MAP
)
from services.classifier import classify_claim

try:
    from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_recall_fscore_support
except ImportError:
    print("[Evaluator] sklearn not available, using basic evaluation.")
    classification_report = None

def evaluate_model_on_test_data(data_dir: str = None, max_eval_samples: int = 100) -> Dict[str, Any]:
    """
    Evaluate trained claim classifier against test dataset split.
    Calculates Accuracy, Precision, Recall, F1-Score, and Confusion Matrix.
    """
    if data_dir is None:
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

    texts, labels = load_and_preprocess_datasets(data_dir)
    if not texts:
        print("[Evaluator] Error: No evaluation samples available.")
        return {}

    # Deterministic Train / Validation / Test split (80% train, 10% val, 10% test)
    num_samples = len(texts)
    indices = list(range(num_samples))
    np.random.seed(42)
    np.random.shuffle(indices)

    test_size = max(1, int(num_samples * 0.1))
    test_indices = indices[-test_size:]

    if max_eval_samples and max_eval_samples < len(test_indices):
        test_indices = test_indices[:max_eval_samples]

    test_texts = [texts[i] for i in test_indices]
    y_true = [labels[i] for i in test_indices]
    y_pred = []

    print(f"\n[Evaluator] Running model inference on {len(test_texts)} test set samples...")

    for claim in test_texts:
        res = classify_claim(claim)
        predicted_label_name = res["label"]
        predicted_idx = NUMERIC_LABEL_MAP.get(predicted_label_name, 3)
        y_pred.append(predicted_idx)

    accuracy = float(np.mean(np.array(y_true) == np.array(y_pred))) * 100.0

    target_names = ["TRUE", "FALSE", "MISLEADING", "UNVERIFIED"]

    report_str = ""
    conf_mat = None

    if classification_report:
        report_str = classification_report(
            y_true, y_pred,
            labels=[0, 1, 2, 3],
            target_names=target_names,
            zero_division=0
        )
        conf_mat = confusion_matrix(y_true, y_pred, labels=[0, 1, 2, 3]).tolist()
        prec, rec, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="weighted", zero_division=0)
    else:
        prec, rec, f1 = accuracy / 100.0, accuracy / 100.0, accuracy / 100.0

    metrics_summary = {
        "accuracy": round(accuracy, 2),
        "precision": round(float(prec) * 100.0, 2),
        "recall": round(float(rec) * 100.0, 2),
        "f1": round(float(f1) * 100.0, 2),
        "test_samples": len(test_texts),
        "confusion_matrix": conf_mat
    }

    print("\n================== MODEL EVALUATION REPORT ==================")
    print(f"  Accuracy  : {metrics_summary['accuracy']}%")
    print(f"  Precision : {metrics_summary['precision']}%")
    print(f"  Recall    : {metrics_summary['recall']}%")
    print(f"  F1-Score  : {metrics_summary['f1']}%")
    print(f"  Test Set  : {metrics_summary['test_samples']} samples")
    if report_str:
        print("\n--- Detailed Per-Class Classification Report ---")
        print(report_str)
    if conf_mat:
        print("--- 4-Class Confusion Matrix ---")
        print("Columns: [TRUE, FALSE, MISLEADING, UNVERIFIED]")
        for row, name in zip(conf_mat, target_names):
            print(f"  {name:<12}: {row}")
    print("=============================================================\n")

    return metrics_summary

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate DistilBERT Claim Classifier for VeriNews AI")
    parser.add_argument("--max_samples", type=int, default=100, help="Max test samples to evaluate (0 for full test set)")
    args = parser.parse_args()

    max_samples = None if args.max_samples == 0 else args.max_samples
    evaluate_model_on_test_data(max_eval_samples=max_samples)
