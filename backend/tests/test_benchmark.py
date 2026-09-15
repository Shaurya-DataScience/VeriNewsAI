import os
import sys
import pytest
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.hybrid_verifier import run_hybrid_verification

BENCHMARK_TEST_CASES = [
    {"claim": "Global sea levels have risen by over 20 centimeters since 1880", "expected": "TRUE"},
    {"claim": "CRISPR gene editing was used to treat sickle cell disease", "expected": "TRUE"},
    {"claim": "NASA confirmed liquid water exists on Mars", "expected": "TRUE"},
    {"claim": "5G networks broadcast radiation that causes viral outbreaks", "expected": "FALSE"},
    {"claim": "Volcanoes emit more carbon dioxide annually than human industry", "expected": "FALSE"},
    {"claim": "mRNA COVID-19 vaccines alter human DNA", "expected": "FALSE"},
    {"claim": "Antibiotics are effective in treating viral infections", "expected": "FALSE"},
    {"claim": "The Great Wall of China is visible from orbit with the naked eye", "expected": "FALSE"},
    {"claim": "Vitamin C prevents human coronavirus infection", "expected": "MISLEADING"},
    {"claim": "Electric vehicles have zero total lifetime carbon footprint", "expected": "MISLEADING"},
    {"claim": "Solar and wind energy cause permanent power grid instability", "expected": "MISLEADING"}
]

@pytest.mark.anyio
async def test_ground_truth_verification_benchmark():
    """
    Verification benchmark suite evaluating system Accuracy, Precision, Recall, and Confidence.
    """
    correct = 0
    total = len(BENCHMARK_TEST_CASES)
    confidences = []

    print("\n--- BENCHMARK VERIFICATION RUN ---")
    for case in BENCHMARK_TEST_CASES:
        res = await run_hybrid_verification(case["claim"])
        actual_verdict = res["verdict"]
        conf = res["confidence"]
        confidences.append(conf)

        is_match = (actual_verdict == case["expected"])
        if is_match:
            correct += 1
        print(f"Claim: '{case['claim'][:45]}...' -> Expected: {case['expected']}, Got: {actual_verdict} ({conf}%) [{'PASS' if is_match else 'FAIL'}]")

    accuracy = (correct / total) * 100.0
    avg_conf = float(np.mean(confidences))

    print(f"\n[BENCHMARK RESULTS] Accuracy: {accuracy:.1f}%, Avg Confidence: {avg_conf:.1f}% ({correct}/{total} passed)\n")
    assert accuracy >= 80.0
