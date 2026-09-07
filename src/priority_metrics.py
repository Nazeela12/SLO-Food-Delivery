import pandas as pd

from src.decision_engine import evaluate_locality


def calculate_priority_justification(
    service,
    weather,
    support,
    reliability
):
    """
    Calculate the percentage of reliability priorities
    supported by measured user/service evidence.
    """

    results = []

    for _, task in reliability.iterrows():

        locality = task["locality"]

        # Skip generic tasks for now
        if locality == "All":
            continue

        service_rows = service[
            service["locality"] == locality
        ]

        weather_rows = weather[
            weather["locality"] == locality
        ]

        support_rows = support[
            support["locality"] == locality
        ]

        # If required data is missing, mark as not justified
        if len(service_rows) == 0:
            continue

        if len(weather_rows) == 0:
            continue

        service_row = service_rows.iloc[-1]
        weather_row = weather_rows.iloc[-1]

        if len(support_rows) > 0:
            support_row = support_rows.iloc[-1]
        else:
            support_row = pd.Series(
                {
                    "customer_complaints": 0
                }
            )

        # Run decision engine
        decision = evaluate_locality(
            service_row,
            support_row,
            weather_row
        )

        # -------------------------------------------------
        # EVIDENCE RULES
        # -------------------------------------------------

        slo_breach = (
            decision["SLI"] < decision["SLO"]
        )

        high_user_impact = (
            decision["user_impact"] >= 40
        )

        low_error_budget = (
            decision["error_budget_remaining"] <= 50
        )

        # At least one measured risk signal
        justified = (
            slo_breach
            or high_user_impact
            or low_error_budget
        )

        results.append(
            {
                "task_id": task["task_id"],
                "task_title": task["task_title"],
                "locality": locality,
                "task_priority": task["priority"],
                "SLI": decision["SLI"],
                "SLO": decision["SLO"],
                "error_budget_remaining":
                    decision["error_budget_remaining"],
                "user_impact":
                    decision["user_impact"],
                "priority_score":
                    decision["priority_score"],
                "SLO_breach":
                    slo_breach,
                "high_user_impact":
                    high_user_impact,
                "low_error_budget":
                    low_error_budget,
                "justified":
                    justified
            }
        )

    results_df = pd.DataFrame(results)

    if len(results_df) == 0:

        return {
            "total_priorities": 0,
            "justified_priorities": 0,
            "justification_percentage": 0,
            "details": results_df
        }

    total_priorities = len(results_df)

    justified_priorities = int(
        results_df["justified"].sum()
    )

    justification_percentage = (
        justified_priorities
        / total_priorities
    ) * 100

    return {
        "total_priorities": total_priorities,
        "justified_priorities": justified_priorities,
        "justification_percentage":
            round(justification_percentage, 2),
        "details": results_df
    }