from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

import pytest

from tileable import EventBus, Tile, TilePayload, TilePluginManager, TileRegistry
from tileable.contrib.observability import LogfireObserverPayload, LogfireObserverPlugin, LogfireObserverTile

if TYPE_CHECKING:
    from tileable.contrib.observability import LogEmitter
from tileable import invoke_tile
from tileable.schema import TileResult


class EchoPayload(TilePayload):
    message: str


class EchoResult(TileResult):
    message: str
    count: int


class EchoTile(Tile[EchoPayload, EchoResult]):
    name = "echo"

    def execute(self, payload: EchoPayload) -> EchoResult:
        count = self.context.state.setdefault("count", 0) + 1
        self.context.state["count"] = count
        self.context.emit("tile.debug", tile=self.name, message=payload.message)
        return EchoResult(message=payload.message.upper(), count=count)


@dataclass
class FakeEmitter:
    events: list[tuple[str, dict[str, object]]]

    def emit(self, event: str, payload: dict[str, object]) -> None:
        self.events.append((event, payload))


def test_logfire_observer_wraps_tile_execution() -> None:
    registry = TileRegistry()
    registry.register(EchoTile)

    bus = EventBus()
    emitter = FakeEmitter(events=[])
    state: dict[str, object] = {}

    result = invoke_tile(
        LogfireObserverTile,
        LogfireObserverPayload(tile="echo", payload=EchoPayload(message="hi"), registry=registry),
        registry=registry,
        event_bus=bus,
        services={"logfire": emitter},
        state=state,
    )

    assert result.result.message == "HI"
    assert state["count"] == 1

    event_names = [name for name, _ in emitter.events]
    assert event_names == ["tile.observer.started", "tile.observer.completed"]


def test_logfire_plugin_injects_emitter() -> None:
    registry = TileRegistry()
    registry.register(EchoTile)

    bus = EventBus()

    emitter = FakeEmitter(events=[])
    plugins = TilePluginManager()
    plugins.register(LogfireObserverPlugin(emitter=cast("LogEmitter", emitter)))

    result = invoke_tile(
        LogfireObserverTile,
        LogfireObserverPayload(tile="echo", payload=EchoPayload(message="plugin"), registry=registry),
        registry=registry,
        plugins=plugins,
        event_bus=bus,
    )

    assert result.result.message == "PLUGIN"
    assert emitter.events


def test_logfire_observer_emits_via_logfire(monkeypatch: pytest.MonkeyPatch) -> None:
    logfire = pytest.importorskip("logfire")

    registry = TileRegistry()
    registry.register(EchoTile)

    bus = EventBus()
    plugins = TilePluginManager()
    plugins.register(LogfireObserverPlugin())

    calls: list[tuple[str, dict[str, object]]] = []

    def fake_log(event: str, payload: dict[str, object]) -> None:
        calls.append((event, payload))

    monkeypatch.setattr(logfire, "log", fake_log)

    result = invoke_tile(
        LogfireObserverTile,
        LogfireObserverPayload(tile="echo", payload=EchoPayload(message="real"), registry=registry),
        registry=registry,
        plugins=plugins,
        event_bus=bus,
        state={},
    )

    assert result.result.message == "REAL"
    assert calls[0][0] == "tile.observer.started"
    assert calls[-1][0] == "tile.observer.completed"
