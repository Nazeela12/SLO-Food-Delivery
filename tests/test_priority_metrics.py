import pandas as pd

from src.priority_metrics import (
    calculate_priority_justification
)


def test_priority_justification():

    service = pd.DataFrame(
        [
            {
                "locality": "RS Puram",
                "total_orders": 180,
                "on_time_orders": 135,
                "failed_orders": 45,
                "avg_delivery_minutes": 42
            }
        ]
    )

    weather = pd.DataFrame(
        [
            {
                "locality": "RS Puram",
                "rainfall_mm": 42,
                "weather_condition": "Heavy Rain"
            }
        ]
    )

    support = pd.DataFrame(
        [
            {
                "locality": "RS Puram",
                "customer_complaints": 25
            }
        ]
    )

    reliability = pd.DataFrame(
        [
            {
                "task_id": "RT001",
                "task_title":
                    "Increase delivery capacity during rain",
                "locality": "RS Puram",
                "priority": "P1"
            }
        ]
    )

    result = calculate_priority_justification(
        service,
        weather,
        support,
        reliability
    )

    assert result["total_priorities"] == 1

    assert result["justified_priorities"] == 1

    assert result["justification_percentage"] == 100.0