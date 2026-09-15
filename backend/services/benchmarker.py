# backend/services/benchmarker.py
# VeriNews AI - A/B Testing & Accuracy Benchmarking Engine

import time
import json
import random
from typing import Callable
from datetime import datetime

LIAR_SAMPLES = [
    {"claim": "The United States has the highest corporate tax rate in the world.", "label": "FALSE", "speaker": "Political figure", "subject": "taxes"},
    {"claim": "Under President Obama, the national debt increased by $9 trillion.", "label": "TRUE", "speaker": "Politician", "subject": "debt"},
    {"claim": "Scientists have found no link between cellphone use and cancer.", "label": "MISLEADING", "speaker": "Media", "subject": "health"},
    {"claim": "China is responsible for 30% of global carbon emissions.", "label": "TRUE", "speaker": "Researcher", "subject": "environment"},
    {"claim": "Vaccines cause autism in children.", "label": "FALSE", "speaker": "Misinformation source", "subject": "health"},
    {"claim": "The US economy added 225,000 jobs in January 2020.", "label": "TRUE", "speaker": "Government", "subject": "economy"},
    {"claim": "Mexico pays for 100% of its own border security costs.", "label": "FALSE", "speaker": "Politician", "subject": "immigration"},
    {"claim": "Global sea levels have risen 8 inches since 1880.", "label": "TRUE", "speaker": "Scientist", "subject": "climate"},
    {"claim": "5G towers are causing COVID-19 symptoms.", "label": "FALSE", "speaker": "Conspiracy source", "subject": "health"},
    {"claim": "The moon landing was faked by NASA in 1969.", "label": "FALSE", "speaker": "Conspiracy source", "subject": "space"},
    {"claim": "The Amazon rainforest produces 20% of Earth's oxygen.", "label": "MISLEADING", "speaker": "Media", "subject": "environment"},
    {"claim": "Wind turbines cause cancer.", "label": "FALSE", "speaker": "Politician", "subject": "energy"},
    {"claim": "The US has the highest gun death rate in the developed world.", "label": "TRUE", "speaker": "Researcher", "subject": "guns"},
    {"claim": "COVID-19 vaccines contain microchips for tracking.", "label": "FALSE", "speaker": "Conspiracy source", "subject": "health"},
    {"claim": "Electric vehicles have a larger carbon footprint than gasoline cars.", "label": "MISLEADING", "speaker": "Media", "subject": "environment"},
    {"claim": "The FDA approved remdesivir for COVID-19 treatment.", "label": "TRUE", "speaker": "Government", "subject": "health"},
    {"claim": "Drinking bleach can cure COVID-19.", "label": "FALSE", "speaker": "Misinformation source", "subject": "health"},
    {"claim": "Solar power is now cheaper than coal in most of the world.", "label": "TRUE", "speaker": "Researcher", "subject": "energy"},
    {"claim": "All immigrants commit more crime than native citizens.", "label": "FALSE", "speaker": "Politician", "subject": "immigration"},
    {"claim": "NASA confirmed the discovery of phosphine gas in Venus atmosphere in 2020.", "label": "TRUE", "speaker": "Scientist", "subject": "space"},
]

FEVER_SAMPLES = [
    {"claim": "Nikola Tesla was born in Serbia.", "label": "TRUE", "evidence": "Nikola Tesla was born in Smiljan, Austrian Empire."},
    {"claim": "The Great Wall of China is visible from space with the naked eye.", "label": "FALSE", "evidence": "NASA astronauts confirmed the wall is too narrow."},
    {"claim": "Albert Einstein failed mathematics in school.", "label": "FALSE", "evidence": "Einstein excelled in mathematics throughout his education."},
    {"claim": "Humans and chimpanzees share approximately 98% of their DNA.", "label": "TRUE", "evidence": "Studies show ~98.7% genetic overlap."},
    {"claim": "The Pacific Ocean is larger than all Earth's landmasses combined.", "label": "TRUE", "evidence": "Pacific Ocean covers ~165 million km²."},
    {"claim": "Carrots improve human night vision.", "label": "FALSE", "evidence": "Carrots provide Vitamin A but do not give night vision."},
    {"claim": "The Eiffel Tower was built in 1889.", "label": "TRUE", "evidence": "Completed March 31, 1889 for the World's Fair."},
    {"claim": "Lightning never strikes the same place twice.", "label": "FALSE", "evidence": "Tall structures are hit dozens of times per year."},
    {"claim": "Water boils at 100°C at sea level.", "label": "TRUE", "evidence": "Standard boiling point at 1 atm is 100°C."},
    {"claim": "The human body has 206 bones.", "label": "TRUE", "evidence": "Adult humans have 206 bones."},
    {"claim": "Mount Everest is the mountain closest to the moon.", "label": "FALSE", "evidence": "Mount Chimborazo is furthest from Earth's center."},
    {"claim": "Antibiotics are effective against viral infections.", "label": "FALSE", "evidence": "Antibiotics only kill bacteria, not viruses."},
    {"claim": "The speed of light in vacuum is approximately 299,792 km/s.", "label": "TRUE", "evidence": "Speed of light c = 299,792,458 m/s."},
    {"claim": "DNA was first described by Watson and Crick in 1953.", "label": "TRUE", "evidence": "Published in Nature in 1953."},
    {"claim": "The Earth is approximately 6,000 years old.", "label": "FALSE", "evidence": "Scientific consensus places Earth's age at 4.54 billion years."},
    {"claim": "Pluto was reclassified as a dwarf planet in 2006.", "label": "TRUE", "evidence": "IAU reclassified Pluto in August 2006."},
    {"claim": "The human brain uses only 10% of its capacity.", "label": "FALSE", "evidence": "Neuroscience shows all brain areas have active functions."},
    {"claim": "Charles Darwin coined the phrase 'survival of the fittest'.", "label": "FALSE", "evidence": "Herbert Spencer coined the phrase."},
    {"claim": "The Sahara Desert is the largest desert on Earth.", "label": "FALSE", "evidence": "Antarctica is the largest desert on Earth."},
    {"claim": "Shakespeare was born in Stratford-upon-Avon in 1564.", "label": "TRUE", "evidence": "Baptized 26 April 1564 in Stratford-upon-Avon."},
]

POLITIFACT_SAMPLES = [
    {"claim": "The US unemployment rate reached a 50-year low in 2019.", "label": "TRUE"},
    {"claim": "The Affordable Care Act created a government takeover of health care.", "label": "FALSE"},
    {"claim": "Illegal immigration costs the US taxpayer $113 billion a year.", "label": "MISLEADING"},
    {"claim": "The US has the best healthcare system in the world.", "label": "FALSE"},
    {"claim": "Infrastructure spending creates good-paying jobs.", "label": "TRUE"},
    {"claim": "Climate change is a hoax invented by foreign governments.", "label": "FALSE"},
    {"claim": "Renewable energy now employs more workers than fossil fuels.", "label": "TRUE"},
    {"claim": "The US military budget exceeds the next 10 countries combined.", "label": "MISLEADING"},
    {"claim": "Universal background checks would stop all gun violence.", "label": "FALSE"},
    {"claim": "Medicare for All would eliminate private health insurance entirely.", "label": "MISLEADING"},
    {"claim": "The US is the world's largest oil producer.", "label": "TRUE"},
    {"claim": "Tax cuts always pay for themselves through economic growth.", "label": "FALSE"},
    {"claim": "Social Security will run out of money in 2034.", "label": "MISLEADING"},
    {"claim": "The US has the most prisoners per capita in the world.", "label": "TRUE"},
    {"claim": "Voter fraud is rampant in modern elections.", "label": "FALSE"},
]

DATASET_MAP = {
    "liar": LIAR_SAMPLES,
    "fever": FEVER_SAMPLES,
    "politifact": POLITIFACT_SAMPLES
}

def normalize_verdict(verdict: str) -> str:
    v = str(verdict).upper().strip()
    if any(k in v for k in ["TRUE", "SUPPORT", "VERIFIED", "FACTUAL", "CORRECT", "ACCURATE"]):
        return "TRUE"
    elif any(k in v for k in ["FALSE", "REFUT", "CONTRADICT", "DEBUNK", "HOAX", "INCORRECT"]):
        return "FALSE"
    else:
        return "MISLEADING"

def run_benchmark(dataset_name: str, n_samples: int, verifier_fn: Callable[[str], dict], run_id: str = None) -> dict:
    dataset = DATASET_MAP.get(dataset_name, LIAR_SAMPLES)
    samples = [random.choice(dataset) for _ in range(n_samples)] if n_samples > len(dataset) else random.sample(dataset, n_samples)
    
    labels = ["TRUE", "MISLEADING", "FALSE"]
    label_to_idx = {"TRUE": 0, "MISLEADING": 1, "FALSE": 2}
    
    confusion = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    latencies = []
    results = []
    
    for sample in samples:
        claim = sample["claim"]
        true_label = normalize_verdict(sample["label"])
        
        t0 = time.time()
        try:
            res = verifier_fn(claim)
            pred_raw = res.get("verdict", res.get("label", "UNVERIFIED"))
            pred_label = normalize_verdict(pred_raw)
            confidence = res.get("confidence", 70)
        except Exception:
            pred_label = "MISLEADING"
            confidence = 50
        latency = (time.time() - t0) * 1000
        latencies.append(latency)
        
        true_idx = label_to_idx[true_label]
        pred_idx = label_to_idx[pred_label]
        confusion[true_idx][pred_idx] += 1
        
        results.append({
            "claim": claim[:80],
            "true": true_label,
            "predicted": pred_label,
            "correct": true_label == pred_label,
            "confidence": confidence,
            "latency_ms": round(latency, 1)
        })
    
    total = len(samples)
    correct = sum(1 for r in results if r["correct"])
    accuracy = round(correct / total * 100, 1) if total > 0 else 0
    
    class_metrics = {}
    for i, label in enumerate(labels):
        tp = confusion[i][i]
        fp = sum(confusion[j][i] for j in range(3) if j != i)
        fn = sum(confusion[i][j] for j in range(3) if j != i)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        class_metrics[label] = {
            "precision": round(precision * 100, 1),
            "recall": round(recall * 100, 1),
            "f1": round(f1 * 100, 1),
            "support": sum(confusion[i])
        }
    
    macro_f1 = round(sum(m["f1"] for m in class_metrics.values()) / 3, 1)
    sorted_latencies = sorted(latencies)
    avg_latency = round(sum(latencies) / len(latencies), 1) if latencies else 0
    p95_idx = max(0, int(len(sorted_latencies) * 0.95) - 1)
    p99_idx = max(0, int(len(sorted_latencies) * 0.99) - 1)
    
    return {
        "run_id": run_id or f"bench_{int(time.time())}",
        "dataset": dataset_name,
        "n_samples": total,
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "class_metrics": class_metrics,
        "confusion_matrix": confusion,
        "confusion_labels": labels,
        "latency": {
            "avg_ms": avg_latency,
            "p95_ms": round(sorted_latencies[p95_idx], 1) if latencies else 0,
            "p99_ms": round(sorted_latencies[p99_idx], 1) if latencies else 0
        },
        "sample_results": results[:20],
        "timestamp": datetime.utcnow().isoformat()
    }

def compare_ab(result_a: dict, result_b: dict) -> dict:
    return {
        "winner": "A" if result_a["accuracy"] >= result_b["accuracy"] else "B",
        "accuracy_delta": round(result_a["accuracy"] - result_b["accuracy"], 1),
        "f1_delta": round(result_a["macro_f1"] - result_b["macro_f1"], 1),
        "latency_delta": round(result_a["latency"]["avg_ms"] - result_b["latency"]["avg_ms"], 1),
        "run_a": result_a,
        "run_b": result_b
    }

def get_dataset_info() -> dict:
    return {
        "liar": {
            "name": "LIAR Dataset (Political Statements)",
            "description": "12K political fact-check statements from PolitiFact with 6-class labels.",
            "sample_count": len(LIAR_SAMPLES),
            "labels": ["TRUE", "MISLEADING", "FALSE"],
            "source": "Wang, 2017 (EMNLP)"
        },
        "fever": {
            "name": "FEVER (Fact Extraction and VERification)",
            "description": "185K claims verified against Wikipedia evidence corpus.",
            "sample_count": len(FEVER_SAMPLES),
            "labels": ["TRUE", "FALSE"],
            "source": "Thorne et al., 2018 (NAACL)"
        },
        "politifact": {
            "name": "PolitiFact Rulings",
            "description": "Political speech claims rated by professional journalists.",
            "sample_count": len(POLITIFACT_SAMPLES),
            "labels": ["TRUE", "MISLEADING", "FALSE"],
            "source": "PolitiFact.com archive"
        }
    }
