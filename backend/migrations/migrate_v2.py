import sqlite3
import os
import sys

# Add parent dir to path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database import DB_PATH

def run_migrations():
    """Migrate SQLite schema to Phase 2 v2.0 without data loss."""
    print(f"[VeriNews AI] Running v2.0 Database Migrations on {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Add Phase 2 columns to claims table if missing
    cursor.execute("PRAGMA table_info(claims)")
    columns = [row[1] for row in cursor.fetchall()]

    new_claims_cols = {
        "classifier_label": "TEXT DEFAULT 'UNVERIFIED'",
        "classifier_confidence": "REAL DEFAULT 0.0",
        "dataset_source": "TEXT DEFAULT 'CUSTOM'",
        "search_latency_ms": "INTEGER DEFAULT 0",
        "cross_encoder_score": "REAL DEFAULT 0.0",
        "similarity_score": "REAL DEFAULT 0.0"
    }

    for col_name, col_type in new_claims_cols.items():
        if col_name not in columns:
            print(f"  + Adding column '{col_name}' to 'claims' table")
            cursor.execute(f"ALTER TABLE claims ADD COLUMN {col_name} {col_type}")

    # 2. Add Phase 2 columns to cache table if missing
    cursor.execute("PRAGMA table_info(cache)")
    cache_columns = [row[1] for row in cursor.fetchall()]

    if "created_at" not in cache_columns:
        print("  + Adding column 'created_at' to 'cache' table")
        cursor.execute("ALTER TABLE cache ADD COLUMN created_at TEXT DEFAULT ''")
    if "hit_count" not in cache_columns:
        print("  + Adding column 'hit_count' to 'cache' table")
        cursor.execute("ALTER TABLE cache ADD COLUMN hit_count INTEGER DEFAULT 1")

    # 3. Create analytics_events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            verdict TEXT,
            confidence INTEGER,
            cache_hit INTEGER DEFAULT 0,
            from_dataset INTEGER DEFAULT 0,
            search_latency_ms INTEGER DEFAULT 0,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 4. Create system_config table for dynamic weight & threshold configuration
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_config (
            key TEXT PRIMARY KEY,
            value_json TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insert default config weights if not present
    default_config = {
        "weights": {
            "dataset_prediction": 0.35,
            "cross_encoder": 0.30,
            "source_credibility": 0.20,
            "semantic_similarity": 0.15
        },
        "similarity_threshold": 0.90
    }
    
    import json
    cursor.execute("""
        INSERT OR IGNORE INTO system_config (key, value_json)
        VALUES ('verification_config', ?)
    """, (json.dumps(default_config),))

    conn.commit()
    conn.close()
    print("[VeriNews AI] Database migration complete!")

if __name__ == "__main__":
    run_migrations()
