# ============================================================
# VeriNews AI - Public Developer API Key Management Service
# Rate Limiting: 50 requests / day per key
# ============================================================

import secrets
import time
from datetime import datetime
import database

PREFIX = "vn_live_"
DAILY_LIMIT = 50

def generate_api_key(name: str = "Enterprise App Key"):
    """
    Generate a new secure Enterprise API Key (format: vn_live_...)
    """
    random_part = secrets.token_hex(16)
    full_key = f"{PREFIX}{random_part}"
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today_date = datetime.now().strftime("%Y-%m-%d")

    conn = database.get_connection()
    cursor = conn.cursor()

    # Ensure table exists with daily rate limit tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            key_id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            usage_count INTEGER DEFAULT 0,
            daily_usage INTEGER DEFAULT 0,
            last_reset_date TEXT NOT NULL,
            active INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        INSERT INTO api_keys (api_key, name, created_at, usage_count, daily_usage, last_reset_date, active)
        VALUES (?, ?, ?, 0, 0, ?, 1)
    """, (full_key, name, created_at, today_date))

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "api_key": full_key,
        "name": name,
        "created_at": created_at,
        "daily_limit": DAILY_LIMIT,
        "message": f"API key generated successfully. Rate limit: {DAILY_LIMIT} requests/day."
    }


def validate_api_key(api_key: str):
    """
    Validate an API key and enforce 50 requests/day rate limit.
    """
    if not api_key:
        return False, "API key is required."

    today_date = datetime.now().strftime("%Y-%m-%d")

    conn = database.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            key_id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            usage_count INTEGER DEFAULT 0,
            daily_usage INTEGER DEFAULT 0,
            last_reset_date TEXT NOT NULL,
            active INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        SELECT key_id, name, usage_count, daily_usage, last_reset_date, active
        FROM api_keys WHERE api_key = ?
    """, (api_key,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return False, "Invalid API Key."

    key_id, name, usage_count, daily_usage, last_reset_date, active = row

    if active != 1:
        conn.close()
        return False, "API Key is revoked or inactive."

    # Reset daily quota if new day
    if last_reset_date != today_date:
        daily_usage = 0
        last_reset_date = today_date

    # Enforce Daily Rate Limit
    if daily_usage >= DAILY_LIMIT:
        conn.close()
        return False, f"Rate limit exceeded: Maximum {DAILY_LIMIT} requests/day allowed. Resets tomorrow."

    # Increment Counters
    new_daily = daily_usage + 1
    new_total = usage_count + 1

    cursor.execute("""
        UPDATE api_keys
        SET usage_count = ?, daily_usage = ?, last_reset_date = ?
        WHERE key_id = ?
    """, (new_total, new_daily, last_reset_date, key_id))

    conn.commit()
    conn.close()

    return True, {
        "key_id": key_id,
        "name": name,
        "usage_count": new_total,
        "daily_usage": new_daily,
        "daily_limit": DAILY_LIMIT,
        "remaining_today": DAILY_LIMIT - new_daily
    }


def get_all_api_keys():
    """
    Retrieve list of generated API keys with daily rate limit metrics.
    """
    today_date = datetime.now().strftime("%Y-%m-%d")
    conn = database.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            key_id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            usage_count INTEGER DEFAULT 0,
            daily_usage INTEGER DEFAULT 0,
            last_reset_date TEXT NOT NULL,
            active INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        SELECT key_id, api_key, name, created_at, usage_count, daily_usage, last_reset_date, active
        FROM api_keys ORDER BY key_id DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    keys = []
    for r in rows:
        masked_key = r[1][:10] + "..." + r[1][-4:]
        # Calculate active daily usage based on reset date
        cur_daily = r[5] if r[6] == today_date else 0
        keys.append({
            "key_id": r[0],
            "api_key_masked": masked_key,
            "name": r[2],
            "created_at": r[3],
            "usage_count": r[4],
            "daily_usage": cur_daily,
            "daily_limit": DAILY_LIMIT,
            "active": bool(r[7])
        })

    return keys
