import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
import database

client = TestClient(app)

def test_admin_stats():
    res = client.get('/api/admin/stats')
    assert res.status_code == 200
    data = res.json()
    assert 'db_size_mb' in data
    assert 'embedding_count' in data
    assert 'cache_hit_ratio_pct' in data

def test_admin_telemetry():
    res = client.get('/api/admin/telemetry')
    assert res.status_code == 200
    data = res.json()
    assert 'total_claims_verified' in data
    assert 'latency' in data
    assert 'avg_ms' in data['latency']
    assert 'error_rate' in data
    assert 'verdict_distribution' in data

def test_system_health():
    res = client.get('/api/admin/system/health')
    assert res.status_code == 200
    data = res.json()
    assert data['status'] == 'HEALTHY'
    assert 'cpu_percent' in data
    assert 'memory' in data
    assert 'disk' in data
    assert 'uptime_str' in data
    assert 'services' in data
    assert 'database_sqlite' in data['services']

def test_cache_management():
    # Save a dummy query
    test_query = 'test_cache_query_for_admin_telemetry_unit_test'
    database.save_to_cache(test_query, {'verdict': 'TRUE', 'confidence': 95, 'summary': 'Test cached item'})
    
    # List cache entries
    res = client.get(f'/api/admin/cache?limit=50&search={test_query}')
    assert res.status_code == 200
    entries = res.json()['entries']
    assert any(e['query'] == test_query for e in entries)
    
    # Evict entry
    del_res = client.delete(f'/api/admin/cache/entry?query={test_query}')
    assert del_res.status_code == 200
    
    # Verify evicted
    res_after = client.get(f'/api/admin/cache?limit=50&search={test_query}')
    assert not any(e['query'] == test_query for e in res_after.json()['entries'])

    # Test vacuum
    vac_res = client.post('/api/admin/cache/vacuum')
    assert vac_res.status_code == 200

def test_security_blacklist_lifecycle():
    flag_pattern = 'test_malicious_exploit_attack_vector'
    
    # 1. Add pattern to blacklist
    f_res = client.post('/api/admin/security/flag', json={
        'pattern': flag_pattern,
        'reason': 'Automated injection unit test'
    })
    assert f_res.status_code == 200
    
    # 2. Verify in flagged list
    list_res = client.get('/api/admin/security/flagged')
    assert list_res.status_code == 200
    flagged = list_res.json()['flagged']
    assert any(f['query_pattern'] == flag_pattern for f in flagged)
    
    # 3. Verify that claim with pattern is intercepted and blocked
    v_res = client.post('/api/verify', json={
        'claim': f'Warning this contains {flag_pattern} payload'
    })
    assert v_res.status_code == 200
    v_data = v_res.json()
    assert v_data['verdict'] == 'FLAGGED / BLOCKED'
    assert v_data['confidence'] == 99
    assert 'Security Alert' in v_data['summary']
    
    # 4. Check security audit log
    e_res = client.get('/api/admin/security/events?limit=10')
    assert e_res.status_code == 200
    events = e_res.json()['events']
    assert any(flag_pattern in e.get('matched_pattern', '') for e in events)
    
    # 5. Unflag
    unflag_res = client.delete(f'/api/admin/security/unflag?pattern={flag_pattern}')
    assert unflag_res.status_code == 200
