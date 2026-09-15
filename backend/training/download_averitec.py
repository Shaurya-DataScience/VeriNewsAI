"""
AVeriTeC Dataset Downloader & Preparer for VeriNews AI
Downloads train.json, dev.json, and test.json into backend/data/averitec/
"""

import os
import sys
import json
import urllib.request
from pathlib import Path

# Base URLs for AVeriTeC raw data mirrors
MIRROR_URLS = [
    "https://raw.githubusercontent.com/MichSchli/AVeriTeC/master/data",
    "https://raw.githubusercontent.com/MichSchli/AVeriTeC/main/data"
]

SPLIT_FILES = ["train.json", "dev.json", "test.json"]

def download_averitec(target_dir: Path = None) -> dict:
    """Download AVeriTeC splits and save to target directory."""
    if target_dir is None:
        target_dir = Path(__file__).resolve().parent.parent / "data" / "averitec"

    target_dir.mkdir(parents=True, exist_ok=True)
    results = {}

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    print(f"[AVeriTeC Downloader] Destination folder: {target_dir}")

    for filename in SPLIT_FILES:
        dest_path = target_dir / filename
        if dest_path.exists() and dest_path.stat().st_size > 1024:
            try:
                with open(dest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    print(f"  + {filename} already exists ({len(data)} records, {dest_path.stat().st_size / 1024:.1f} KB). Skipping download.")
                    results[filename] = len(data)
                    continue
            except Exception:
                print(f"  ! {filename} corrupted locally, redownloading...")

        downloaded = False
        for base_url in MIRROR_URLS:
            url = f"{base_url}/{filename}"
            print(f"  -> Downloading {filename} from {url}...")
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=30) as resp:
                    if resp.status == 200:
                        content = resp.read()
                        with open(dest_path, "wb") as f:
                            f.write(content)
                        
                        # Validate JSON
                        with open(dest_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            print(f"  [SUCCESS] {filename}: {len(data)} records saved ({len(content) / 1024:.1f} KB).")
                            results[filename] = len(data)
                        downloaded = True
                        break
            except Exception as e:
                print(f"  [MIRROR ERROR] Failed fetching from {url}: {e}")

        if not downloaded:
            print(f"  [WARNING] Could not download {filename} from remote mirrors. Creating empty template if needed.")

    return results

if __name__ == "__main__":
    download_averitec()
