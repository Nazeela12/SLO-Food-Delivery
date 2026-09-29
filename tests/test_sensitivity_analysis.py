from src.sensitivity_analysis import (
    BASELINE_WEIGHTS,
    SENSITIVITY_SCENARIOS,
    calculate_weighted_score,
    run_sensitivity_analysis,
    calculate_priority_stability
)


def test_weights_sum_to_one():

    for scenario, weights in SENSITIVITY_SCENARIOS.items():

        total = sum(weights.values())

        assert round(total, 2) == 1.00


def test_baseline_weights():

    assert BASELINE_WEIGHTS["slo_risk"] == 0.40
    assert BASELINE_WEIGHTS["user_impact"] == 0.35
    assert BASELINE_WEIGHTS["error_budget"] == 0.15
    assert BASELINE_WEIGHTS["weather"] == 0.10


def test_weighted_score():

    score = calculate_weighted_score(
        sli=90.0,
        error_budget=0.0,
        user_impact=50.0,
        rainfall_mm=30.0,
        weights=BASELINE_WEIGHTS
    )

    assert score == 44.61


def test_sensitivity_analysis():

    service_row = {
        "total_orders": 100,
        "on_time_orders": 90,
        "failed_orders": 10
    }

    support_row = {
        "customer_complaints": 20
    }

    weather_row = {
        "rainfall_mm": 30
    }

    results = run_sensitivity_analysis(
        service_row,
        support_row,
        weather_row
    )

    assert len(results) == 5
    assert "priority_score" in results.columns
    assert "priority" in results.columns


def test_priority_stability():

    results = run_sensitivity_analysis(
        {
            "total_orders": 100,
            "on_time_orders": 90,
            "failed_orders": 10
        },
        {
            "customer_complaints": 20
        },
        {
            "rainfall_mm": 30
        }
    )

    stability = calculate_priority_stability(results)

    assert 0 <= stability <= 100