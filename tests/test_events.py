from __future__ import annotations

from tileable.events import STANDARD_EVENTS, EventBus, get_event_bus


def test_event_bus_subscribe_emit_and_unsubscribe() -> None:
    bus = EventBus()
    calls: list[tuple[str, dict[str, object]]] = []

    def handler(sender: str, **payload: object) -> None:
        calls.append((sender, payload))

    unsubscribe = bus.subscribe("custom.event", handler)
    bus.emit("custom.event", data=1)
    unsubscribe()
    bus.emit("custom.event", data=2)

    assert calls == [("custom.event", {"data": 1})]


def test_event_bus_unsubscribe_method() -> None:
    bus = EventBus()
    calls: dict[str, int] = {}

    for event in STANDARD_EVENTS:

        def handler(sender: str, *, _evt: str = event, **_: object) -> None:
            calls[_evt] = calls.get(_evt, 0) + 1

        bus.subscribe(event, handler, weak=False)
        bus.emit(event)  # fire once
        bus.unsubscribe(event, handler)
        bus.emit(event)

    assert all(calls.get(event, 0) == 1 for event in STANDARD_EVENTS)


def test_get_event_bus_returns_singleton() -> None:
    first = get_event_bus()
    second = get_event_bus()

    assert first is second
