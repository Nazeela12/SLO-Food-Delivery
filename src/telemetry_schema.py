from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TelemetryEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    order_id: str
    event_time: datetime
    status: str