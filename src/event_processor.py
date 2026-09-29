from datetime import datetime, timedelta
from src.telemetry_schema import TelemetryEvent


class EventProcessor:

    def __init__(self, allowed_delay_seconds=30):
        self.allowed_delay = timedelta(seconds=allowed_delay_seconds)

        self.processed_event_ids = set()
        self.order_state = {}
        self.latest_event_time = None

        self.stats = {
            "processed": 0,
            "duplicates": 0,
            "delayed": 0,
            "out_of_order": 0
        }

    def process_event(self, event):

        # Validate the incoming telemetry event
        validated_event = TelemetryEvent.model_validate(event)

        # Use the validated values
        event_id = validated_event.event_id
        order_id = validated_event.order_id
        event_time = validated_event.event_time
        status = validated_event.status

        # Check for duplicate event
        if event_id in self.processed_event_ids:
            self.stats["duplicates"] += 1

            return {
                "status": "duplicate",
                "event_id": event_id,
                "message": "Duplicate event ignored."
            }

        # Check whether the event is out of order
        out_of_order = False

        if self.latest_event_time is not None:

            if event_time < self.latest_event_time:
                out_of_order = True
                self.stats["out_of_order"] += 1

        # Check whether the event is delayed
        delayed = False

        if self.latest_event_time is not None:

            if self.latest_event_time - event_time > self.allowed_delay:
                delayed = True
                self.stats["delayed"] += 1

        # Mark event as processed
        self.processed_event_ids.add(event_id)

        # Get current state of the order
        current_state = self.order_state.get(order_id)

        if current_state is None:

            self.order_state[order_id] = {
                "status": status,
                "event_time": event_time
            }

        else:

            current_event_time = current_state["event_time"]

            # Only update state when the new event is newer
            if event_time >= current_event_time:

                self.order_state[order_id] = {
                    "status": status,
                    "event_time": event_time
                }

        # Update latest event time
        if (
            self.latest_event_time is None
            or event_time > self.latest_event_time
        ):
            self.latest_event_time = event_time

        # Count successfully processed event
        self.stats["processed"] += 1

        # Determine final processing status
        if delayed:
            result_status = "delayed"

        elif out_of_order:
            result_status = "out_of_order"

        else:
            result_status = "processed"

        return {
            "status": result_status,
            "event_id": event_id,
            "order_id": order_id,
            "message": "Event processed safely."
        }

    def get_order_state(self, order_id):
        return self.order_state.get(order_id)

    def get_statistics(self):
        return self.stats.copy()