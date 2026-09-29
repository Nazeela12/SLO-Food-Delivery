import pandas as pd

from src.decision_engine import (
    SLO_TARGET,
    calculate_sli,
    calculate_error_budget,
    calculate_user_impact,
    get_weather_factor,
    classify_priority
)


# Current production weights
BASELINE_WEIGHTS = {
    "slo_risk": 0.40,
    "user_impact": 0.35,
    "error_budget": 0.15,
    "weather": 0.10
}


# Alternative weighting scenarios
SENSITIVITY_SCENARIOS = {
    "Baseline": {
        "slo_risk": 0.40,
        "user_impact": 0.35,
        "error_budget": 0.15,
        "weather": 0.10
    },

    "Higher SLO Risk": {
        "slo_risk": 0.50,
        "user_impact": 0.25,
        "error_budget": 0.15,
        "weather": 0.10
    },

    "Higher User Impact": {
        "slo_risk": 0.30,
        "user_impact": 0.45,
        "error_budget": 0.15,
        "weather": 0.10
    },

    "Higher Error Budget": {
        "slo_risk": 0.40,
        "user_impact": 0.30,
        "error_budget": 0.20,
        "weather": 0.10
    },

    "Higher Weather": {
        "slo_risk": 0.40,
        "user_impact": 0.30,
        "error_budget": 0.15,
        "weather": 0.15
    }
}


def calculate_weighted_score(
    sli,
    error_budget,
    user_impact,
    rainfall_mm,
    weights
):
    """
    Calculate priority score using a supplied set of weights.
    """

    slo_risk = max(0, SLO_TARGET - sli) / SLO_TARGET * 100

    budget_risk = 100 - error_budget

    weather_risk = get_weather_factor(rainfall_mm) * 100

    score = (
        weights["slo_risk"] * slo_risk
        + weights["user_impact"] * user_impact
        + weights["error_budget"] * budget_risk
        + weights["weather"] * weather_risk
    )

    return round(score, 2)


def evaluate_scenario(
    service_row,
    support_row,
    weather_row,
    scenario_name,
    weights
):
    """
    Evaluate one locality under one weighting scenario.
    """

    sli = calculate_sli(
        service_row["total_orders"],
        service_row["on_time_orders"]
    )

    error_budget = calculate_error_budget(sli)

    user_impact = calculate_user_impact(
        support_row["customer_complaints"],
        service_row["failed_orders"],
        service_row["total_orders"]
    )

    score = calculate_weighted_score(
        sli,
        error_budget,
        user_impact,
        weather_row["rainfall_mm"],
        weights
    )

    priority = classify_priority(score)

    return {
        "scenario": scenario_name,
        "slo_weight": weights["slo_risk"],
        "user_impact_weight": weights["user_impact"],
        "error_budget_weight": weights["error_budget"],
        "weather_weight": weights["weather"],
        "priority_score": score,
        "priority": priority
    }


def run_sensitivity_analysis(
    service_row,
    support_row,
    weather_row
):
    """
    Run all sensitivity scenarios for one locality.
    """

    results = []

    for scenario_name, weights in SENSITIVITY_SCENARIOS.items():

        result = evaluate_scenario(
            service_row,
            support_row,
            weather_row,
            scenario_name,
            weights
        )

        results.append(result)

    return pd.DataFrame(results)


def calculate_priority_stability(results_df):
    """
    Calculate how many scenarios produce the same
    priority classification as the baseline.
    """

    if len(results_df) == 0:
        return 0.0

    baseline_priority = results_df.iloc[0]["priority"]

    matching = (
        results_df["priority"] == baseline_priority
    ).sum()

    stability = (
        matching / len(results_df)
    ) * 100

    return round(stability, 2)