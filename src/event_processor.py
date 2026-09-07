from datetime import datetime, timedelta


class EventProcessor:

    def __init__(self, allowed_delay_seconds=30):

        self.allowed_delay = timedelta(
            seconds=allowed_delay_seconds
        )

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

        event_id = event["event_id"]
        order_id = event["order_id"]

        event_time = datetime.fromisoformat(
            event["event_time"]
        )

        # Duplicate detection
        if event_id in self.processed_event_ids:

            self.stats["duplicates"] += 1

            return {
                "status": "duplicate",
                "event_id": event_id,
                "message": "Duplicate event ignored."
            }

        # Out-of-order detection
        out_of_order = False

        if self.latest_event_time is not None:

            if event_time < self.latest_event_time:
                out_of_order = True
                self.stats["out_of_order"] += 1

        # Delayed event detection
        delayed = False

        if self.latest_event_time is not None:

            if (
                self.latest_event_time - event_time
                > self.allowed_delay
            ):
                delayed = True
                self.stats["delayed"] += 1

        # Record event ID
        self.processed_event_ids.add(event_id)

        # Update order state safely
        current_state = self.order_state.get(order_id)

        if current_state is None:

            self.order_state[order_id] = {
                "status": event["status"],
                "event_time": event_time
            }

        else:

            current_event_time = current_state["event_time"]

            # Older events cannot overwrite newer state
            if event_time >= current_event_time:

                self.order_state[order_id] = {
                    "status": event["status"],
                    "event_time": event_time
                }

        # Update latest event time
        if (
            self.latest_event_time is None
            or event_time > self.latest_event_time
        ):
            self.latest_event_time = event_time

        self.stats["processed"] += 1

        if delayed:
            status = "delayed"

        elif out_of_order:
            status = "out_of_order"

        else:
            status = "processed"

        return {
            "status": status,
            "event_id": event_id,
            "order_id": order_id,
            "message": "Event processed safely."
        }

    def get_order_state(self, order_id):

        return self.order_state.get(order_id)

    def get_statistics(self):

        return self.stats.copy()