from src.audit_store import AuditStore


def test_save_and_read_decision(tmp_path):

    database_path = tmp_path / "test_audit.db"

    store = AuditStore(database_path)

    record = {
        "decision_id": "TEST001",
        "timestamp": "2026-09-28T10:00:00",
        "locality": "RS Puram",
        "recommended_priority": "P1 - Critical",
        "recommended_action": "Prioritize reliability work for RS Puram.",
        "decision": "Approved",
        "override_reason": "",
        "priority_score": 75.5,
        "sli": 82.5,
        "slo": 95.0,
        "user_impact": 65.0,
        "rainfall_mm": 30.0
    }

    store.save_decision(record)

    results = store.get_all_decisions()

    assert len(results) == 1
    assert results.iloc[0]["decision_id"] == "TEST001"
    assert results.iloc[0]["locality"] == "RS Puram"
    assert results.iloc[0]["decision"] == "Approved"