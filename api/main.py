from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.decision_engine import evaluate_locality


# Project paths
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


# FastAPI application
app = FastAPI(
    title="FoodPulse SLO Decision API",
    description="API for reliability and SLO-based decision support.",
    version="1.0.0"
)


# Request model for locality evaluation
class EvaluateRequest(BaseModel):
    locality: str


@app.get("/health")
def health_check():
    """
    Check whether the FoodPulse API is running.
    """
    return {
        "status": "online",
        "service": "FoodPulse SLO Decision API"
    }


@app.get("/localities")
def get_localities():
    """
    Return all available localities from service telemetry.
    """
    service_file = DATA_DIR / "service_metrics.csv"

    service = pd.read_csv(service_file)

    localities = sorted(
        service["locality"]
        .dropna()
        .unique()
        .tolist()
    )

    return {
        "count": len(localities),
        "localities": localities
    }


@app.post("/evaluate")
def evaluate(request: EvaluateRequest):
    """
    Evaluate the reliability priority for a selected locality.
    """

    # Load project data
    service = pd.read_csv(
        DATA_DIR / "service_metrics.csv"
    )

    support = pd.read_csv(
        DATA_DIR / "support_incidents.csv"
    )

    weather = pd.read_csv(
        DATA_DIR / "weather.csv"
    )

    # Filter data for the requested locality
    service_rows = service[
        service["locality"] == request.locality
    ]

    weather_rows = weather[
        weather["locality"] == request.locality
    ]

    support_rows = support[
        support["locality"] == request.locality
    ]

    # Error boundary: unknown locality
    if len(service_rows) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Locality '{request.locality}' not found."
        )

    # Error boundary: missing weather data
    if len(weather_rows) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Weather data not found for '{request.locality}'."
        )

    # Use the latest available records
    service_row = service_rows.iloc[-1]
    weather_row = weather_rows.iloc[-1]

    # Support incidents may not exist for every locality
    if len(support_rows) > 0:
        support_row = support_rows.iloc[-1]
    else:
        support_row = pd.Series({
            "customer_complaints": 0
        })

    # Run the existing FoodPulse decision engine
    decision = evaluate_locality(
        service_row,
        support_row,
        weather_row
    )

    # Convert NumPy values to standard Python values
    # so FastAPI can serialize the response as JSON.
    return {
        key: value.item() if hasattr(value, "item") else value
        for key, value in decision.items()
    }