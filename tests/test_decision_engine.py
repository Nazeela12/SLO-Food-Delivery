from src.decision_engine import (
    calculate_sli,
    calculate_error_budget,
    calculate_user_impact,
    calculate_priority_score,
)


def test_sli():

    sli = calculate_sli(180, 135)

    assert round(sli, 2) == 75.00


def test_error_budget():

    budget = calculate_error_budget(75)

    assert budget == 0.0


def test_user_impact():

    impact = calculate_user_impact(
        complaints=25,
        failed_orders=45,
        total_orders=180
    )

    assert impact > 50


def test_priority_score():

    score = calculate_priority_score(
        sli=75,
        error_budget=0,
        user_impact=80,
        rainfall_mm=42
    )

    assert score > 60