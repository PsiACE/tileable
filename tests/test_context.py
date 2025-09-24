from __future__ import annotations

import pytest

from tileable.context import TileContext
from tileable.events import EventBus


def test_context_exposes_services_and_state() -> None:
    bus = EventBus()
    ctx = TileContext(event_bus=bus, services={"answer": 42}, state={"count": 1})

    services = ctx.services
    assert services["answer"] == 42
    with pytest.raises(TypeError):
        services["answer"] = 41  # type: ignore[index]
    ctx.set_service("greeting", "hi")
    assert ctx.get_service("greeting") == "hi"
    assert ctx.get_service_or("missing", "fallback") == "fallback"

    ctx.state["count"] = 2
    assert ctx.state["count"] == 2


def test_context_get_service_raises_with_message() -> None:
    ctx = TileContext(event_bus=EventBus())

    with pytest.raises(KeyError, match="Service 'db' is not available"):
        ctx.get_service("db")


def test_context_emit_proxies_to_bus() -> None:
    events: list[dict[str, object]] = []
    bus = EventBus()
    bus.subscribe("tile.debug", lambda sender, **payload: events.append(payload))

    ctx = TileContext(event_bus=bus)
    ctx.emit("tile.debug", tile="demo", data={"value": 1})

    assert events == [{"tile": "demo", "data": {"value": 1}}]
