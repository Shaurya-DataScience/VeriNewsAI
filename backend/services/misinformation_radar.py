import time
from typing import Dict, Any, List
import database

SEED_MISINFORMATION_ALERTS = [
    {
        "id": "radar_101",
        "headline": "Viral claim alleging 5G cell towers cause viral respiratory illness debunked",
        "category": "Technology & Health",
        "verdict": "FALSE",
        "confidence": 98,
        "velocity": "VIRAL BREAKING",
        "source": "WHO & IEEE Spectrum",
        "timestamp": "Just now",
        "query_text": "5G towers cause viral respiratory illness"
    },
    {
        "id": "radar_102",
        "headline": "Social media rumors claiming NASA confirmed 3 days of darkness in December",
        "category": "Viral Hoax",
        "verdict": "FALSE",
        "confidence": 99,
        "velocity": "HIGH SPIKE",
        "source": "NASA Planetary Science",
        "timestamp": "12 mins ago",
        "query_text": "NASA confirmed three days of complete darkness"
    },
    {
        "id": "radar_103",
        "headline": "Post claiming drinking raw salt water cures human viral infection disproven",
        "category": "Medical & Health",
        "verdict": "FALSE",
        "confidence": 97,
        "velocity": "TRENDING",
        "source": "CDC & Mayo Clinic",
        "timestamp": "35 mins ago",
        "query_text": "Drinking salt water cures viral infection"
    },
    {
        "id": "radar_104",
        "headline": "Claim that electric cars produce higher total lifecycle emissions than diesel",
        "category": "Energy & Climate",
        "verdict": "MISLEADING",
        "confidence": 88,
        "velocity": "ACTIVE DISCUSSIONS",
        "source": "Reuters Fact Check & EPA",
        "timestamp": "1 hour ago",
        "query_text": "Electric cars produce more lifecycle carbon emissions than diesel"
    },
    {
        "id": "radar_105",
        "headline": "Deepfake audio of major political leader declaring immediate bank holiday",
        "category": "AI Forensics",
        "verdict": "FABRICATED",
        "confidence": 96,
        "velocity": "VIRAL BREAKING",
        "source": "AP Fact Check & DARPA SemaFor",
        "timestamp": "2 hours ago",
        "query_text": "Audio recording of president declaring bank holiday"
    },
    {
        "id": "radar_106",
        "headline": "Reports that CRISPR Casgevy therapy was approved for sickle cell disease",
        "category": "Science & Medicine",
        "verdict": "TRUE",
        "confidence": 98,
        "velocity": "VERIFIED CONFIRMATION",
        "source": "FDA & Nature Medicine",
        "timestamp": "3 hours ago",
        "query_text": "FDA approved CRISPR Casgevy gene therapy for sickle cell"
    }
]

def init_radar_table():
    """Ensure radar table exists in SQLite."""
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS radar_alerts (
                id TEXT PRIMARY KEY,
                headline TEXT,
                category TEXT,
                verdict TEXT,
                confidence INTEGER,
                velocity TEXT,
                source TEXT,
                timestamp TEXT,
                query_text TEXT
            )
        """)
        
        # Seed if empty
        cursor.execute("SELECT COUNT(*) FROM radar_alerts")
        if cursor.fetchone()[0] == 0:
            for item in SEED_MISINFORMATION_ALERTS:
                cursor.execute("""
                    INSERT OR IGNORE INTO radar_alerts (id, headline, category, verdict, confidence, velocity, source, timestamp, query_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (item["id"], item["headline"], item["category"], item["verdict"], item["confidence"], item["velocity"], item["source"], item["timestamp"], item["query_text"]))
            conn.commit()
            
        conn.close()
    except Exception as e:
        print(f"[Radar] Init error: {e}")

def get_trending_misinformation_alerts() -> List[Dict[str, Any]]:
    """Retrieve active trending misinformation radar items."""
    init_radar_table()
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, headline, category, verdict, confidence, velocity, source, timestamp, query_text FROM radar_alerts ORDER BY rowid DESC LIMIT 10")
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            return [{
                "id": r[0],
                "headline": r[1],
                "category": r[2],
                "verdict": r[3],
                "confidence": r[4],
                "velocity": r[5],
                "source": r[6],
                "timestamp": r[7],
                "query_text": r[8]
            } for r in rows]
    except Exception as e:
        print(f"[Radar] Fetch error: {e}")
        
    return SEED_MISINFORMATION_ALERTS
