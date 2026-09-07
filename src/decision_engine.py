import pandas as pd


SLO_TARGET = 95.0


def calculate_sli(total_orders, on_time_orders):
    """Calculate delivery SLI as percentage of on-time orders."""
    if total_orders == 0:
        return 100.0

    return (on_time_orders / total_orders) * 100


def calculate_error_budget(sli, slo_target=SLO_TARGET):
    """Calculate remaining error budget percentage."""
    allowed_failure = 100 - slo_target
    actual_failure = 100 - sli

    if actual_failure <= allowed_failure:
        return 100.0

    budget_used = (actual_failure / allowed_failure) * 100
    return max(0.0, 100 - budget_used)


def calculate_user_impact(complaints, failed_orders, total_orders):
    """Calculate a simple 0-100 user impact score."""

    complaint_score = min(complaints / 25, 1.0) * 50

    if total_orders == 0:
        failure_score = 0
    else:
        failure_rate = failed_orders / total_orders
        failure_score = min(failure_rate / 0.25, 1.0) * 50

    return round(complaint_score + failure_score, 2)


def get_weather_factor(rainfall_mm):
    """Convert rainfall into a weather risk score."""

    if rainfall_mm >= 30:
        return 1.0
    elif rainfall_mm >= 15:
        return 0.7
    elif rainfall_mm >= 5:
        return 0.4
    else:
        return 0.0


def calculate_priority_score(
    sli,
    error_budget,
    user_impact,
    rainfall_mm,
):
    """
    Calculate reliability priority using transparent weighted rules.
    """

    # SLO breach severity
    slo_risk = max(0, SLO_TARGET - sli) / SLO_TARGET * 100

    # Error budget risk
    budget_risk = 100 - error_budget

    # Weather risk
    weather_risk = get_weather_factor(rainfall_mm) * 100

    # Weighted priority score
    score = (
        0.40 * slo_risk
        + 0.35 * user_impact
        + 0.15 * budget_risk
        + 0.10 * weather_risk
    )

    return round(score, 2)


def classify_priority(score):

    if score >= 60:
        return "P1 - Critical"

    elif score >= 40:
        return "P2 - High"

    elif score >= 20:
        return "P3 - Medium"

    return "P4 - Low"


def generate_recommendation(score, locality):

    priority = classify_priority(score)

    if priority == "P1 - Critical":
        action = (
            f"Prioritize reliability work for {locality} "
            f"before lower-impact feature work."
        )

    elif priority == "P2 - High":
        action = (
            f"Schedule reliability work for {locality} "
            f"ahead of non-critical feature work."
        )

    elif priority == "P3 - Medium":
        action = (
            f"Monitor {locality} and schedule reliability "
            f"improvements based on capacity."
        )

    else:
        action = (
            f"No immediate reliability intervention required "
            f"for {locality}."
        )

    return action


def evaluate_locality(service_row, support_row, weather_row):

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

    priority_score = calculate_priority_score(
        sli,
        error_budget,
        user_impact,
        weather_row["rainfall_mm"]
    )

    priority = classify_priority(priority_score)

    recommendation = generate_recommendation(
        priority_score,
        service_row["locality"]
    )

    return {
        "locality": service_row["locality"],
        "SLI": round(sli, 2),
        "SLO": SLO_TARGET,
        "error_budget_remaining": round(error_budget, 2),
        "user_impact": user_impact,
        "rainfall_mm": weather_row["rainfall_mm"],
        "priority_score": priority_score,
        "priority": priority,
        "recommendation": recommendation,
    }
