from src.event_processor import EventProcessor


def test_normal_events():

    processor = EventProcessor()

    event1 = {
        "event_id": "E001",
        "order_id": "O001",
        "event_time": "2026-09-07T10:00:00",
        "status": "PLACED"
    }

    event2 = {
        "event_id": "E002",
        "order_id": "O001",
        "event_time": "2026-09-07T10:00:10",
        "status": "ACCEPTED"
    }

    processor.process_event(event1)
    processor.process_event(event2)

    state = processor.get_order_state("O001")

    assert state["status"] == "ACCEPTED"


def test_duplicate_event():

    processor = EventProcessor()

    event = {
        "event_id": "E001",
        "order_id": "O001",
        "event_time": "2026-09-07T10:00:00",
        "status": "PLACED"
    }

    result1 = processor.process_event(event)
    result2 = processor.process_event(event)

    assert result1["status"] == "processed"
    assert result2["status"] == "duplicate"

    stats = processor.get_statistics()

    assert stats["duplicates"] == 1
    assert stats["processed"] == 1


def test_out_of_order_event():

    processor = EventProcessor()

    event1 = {
        "event_id": "E001",
        "order_id": "O001",
        "event_time": "2026-09-07T10:00:10",
        "status": "PICKED_UP"
    }

    event2 = {
        "event_id": "E002",
        "order_id": "O001",
        "event_time": "2026-09-07T10:00:05",
        "status": "ACCEPTED"
    }

    processor.process_event(event1)

    result = processor.process_event(event2)

    assert result["status"] == "out_of_order"

    state = processor.get_order_state("O001")

    assert state["status"] == "PICKED_UP"


def test_delayed_event():

    processor = EventProcessor(
        allowed_delay_seconds=30
    )

    event1 = {
        "event_id": "E001",
        "order_id": "O001",
        "event_time": "2026-09-07T10:01:00",
        "status": "PICKED_UP"
    }

    event2 = {
        "event_id": "E002",
        "order_id": "O002",
        "event_time": "2026-09-07T10:00:00",
        "status": "PLACED"
    }

    processor.process_event(event1)

    result = processor.process_event(event2)

    assert result["status"] == "delayed"

    stats = processor.get_statistics()

    assert stats["delayed"] == 1


def test_recovery_without_state_corruption():

    processor = EventProcessor()

    events = [

        {
            "event_id": "E001",
            "order_id": "O001",
            "event_time": "2026-09-07T10:00:00",
            "status": "PLACED"
        },

        {
            "event_id": "E002",
            "order_id": "O001",
            "event_time": "2026-09-07T10:00:10",
            "status": "ACCEPTED"
        },

        # Out-of-order event
        {
            "event_id": "E003",
            "order_id": "O001",
            "event_time": "2026-09-07T10:00:05",
            "status": "PLACED"
        },

        # Duplicate event
        {
            "event_id": "E002",
            "order_id": "O001",
            "event_time": "2026-09-07T10:00:10",
            "status": "ACCEPTED"
        },

        # New valid event
        {
            "event_id": "E004",
            "order_id": "O001",
            "event_time": "2026-09-07T10:00:20",
            "status": "PICKED_UP"
        }
    ]

    for event in events:
        processor.process_event(event)

    state = processor.get_order_state("O001")

    # Newest valid event must determine final state
    assert state["status"] == "PICKED_UP"

    stats = processor.get_statistics()

    assert stats["duplicates"] == 1
    assert stats["out_of_order"] == 1
    assert stats["processed"] == 4