from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import cast

import pytest

from examples import run_greeting
from tileable import (
    EventBus,
    PluginError,
    Tile,
    TileExecutionError,
    TilePayload,
    TilePluginManager,
    TileRegistrationAggregateError,
    TileRegistrationError,
    TileRegistry,
    TileResult,
    ainvoke_tile,
    hookimpl,
    invoke_tile,
)


class EchoPayload(TilePayload):
    message: str


class EchoResult(TileResult):
    echoed: str


class EchoTile(Tile[EchoPayload, EchoResult]):
    name = "echo"
    description = "Uppercase echo tile."

    def execute(self, payload: EchoPayload) -> EchoResult:
        prefix = self.context.get_service_or("prefix", "")
        combined = f"{prefix}{payload.message}"
        self.context.emit("tile.debug", tile=self.name, data={"length": len(combined)})
        return EchoResult(echoed=combined.upper())


@pytest.fixture()
def registry() -> TileRegistry:
    reg = TileRegistry()
    reg.register(EchoTile)
    return reg


def test_invoke_tile_returns_result(registry: TileRegistry) -> None:
    result = invoke_tile(EchoTile, EchoPayload(message="hello"), registry=registry)
    assert result.echoed == "HELLO"


def test_invoke_tile_by_name_with_services_and_events(registry: TileRegistry) -> None:
    bus = EventBus()
    calls: list[tuple[str, dict[str, object]]] = []

    for event in ("tile.started", "tile.completed", "tile.debug"):

        def handler(sender: str, **data: object) -> None:
            calls.append((sender, data))

        bus.subscribe(event, handler)

    result = invoke_tile(
        "echo",
        EchoPayload(message="world"),
        registry=registry,
        event_bus=bus,
        services={"prefix": "hi-"},
    )

    assert result.echoed == "HI-WORLD"
    assert [event for event, _ in calls if event != "tile.debug"] == ["tile.started", "tile.completed"]
    debug_payloads = [payload for event, payload in calls if event == "tile.debug"]
    assert debug_payloads == [{"tile": "echo", "data": {"length": 8}}]


class BoomTile(Tile[EchoPayload, EchoResult]):
    name = "boom"

    def execute(self, payload: EchoPayload) -> EchoResult:  # pragma: no cover - executed in test
        raise ValueError("exploded")


def test_invoke_tile_wraps_exceptions() -> None:
    registry = TileRegistry()
    registry.register(BoomTile)
    bus = EventBus()
    failures: list[dict[str, object]] = []

    def failure_handler(sender: str, **data: object) -> None:
        failures.append(data)

    bus.subscribe("tile.failed", failure_handler)

    with pytest.raises(TileExecutionError) as exc_info:
        invoke_tile("boom", EchoPayload(message="fail"), registry=registry, event_bus=bus)

    execution_error = cast(TileExecutionError, exc_info.value)
    assert isinstance(execution_error.original, ValueError)
    assert len(failures) == 1
    failure_payload = failures[0]
    assert failure_payload["phase"] == "execute"
    assert isinstance(failure_payload["error"], ValueError)


class AsyncPayload(TilePayload):
    value: int


class AsyncResult(TileResult):
    doubled: int


class AsyncTile(Tile[AsyncPayload, AsyncResult]):
    name = "async"

    async def aexecute(self, payload: AsyncPayload) -> AsyncResult:
        await asyncio.sleep(0)
        return AsyncResult(doubled=payload.value * 2)

    def execute(self, payload: AsyncPayload) -> AsyncResult:  # pragma: no cover
        raise RuntimeError


@pytest.mark.asyncio()
async def test_ainvoke_tile_runs_async_path() -> None:
    registry = TileRegistry()
    registry.register(AsyncTile)
    result = await ainvoke_tile("async", AsyncPayload(value=21), registry=registry)
    assert result.doubled == 42


class PluginTile(Tile[EchoPayload, EchoResult]):
    name = "plugin-echo"

    def execute(self, payload: EchoPayload) -> EchoResult:
        note = self.context.state.setdefault("note", "")
        return EchoResult(echoed=f"{note}{payload.message}")


class EchoPlugin:
    @hookimpl
    def tile_specs(self):
        yield PluginTile

    @hookimpl
    def tile_startup(self, ctx, tile):
        ctx.state["note"] = "*"

    @hookimpl
    def tile_shutdown(self, ctx, tile, error):
        ctx.state["closed"] = True


def test_plugin_manager_registers_tiles_on_demand(registry: TileRegistry) -> None:
    plugins = TilePluginManager()
    plugins.register(EchoPlugin())

    result = invoke_tile(
        "plugin-echo",
        EchoPayload(message="plug"),
        registry=registry,
        plugins=plugins,
    )

    assert result.echoed == "*plug"
    assert registry.get("plugin-echo") is PluginTile


@pytest.mark.asyncio()
async def test_async_plugins_share_state() -> None:
    plugins = TilePluginManager()
    plugins.register(EchoPlugin())
    registry = TileRegistry()
    registry.register(AsyncTile)

    counts: defaultdict[str, int] = defaultdict(int)
    bus = EventBus()
    for event in ("tile.started", "tile.completed"):

        def handler(sender: str, *, _evt=event, **data: object) -> None:
            counts[_evt] += 1

        bus.subscribe(event, handler)

    result = await ainvoke_tile(
        PluginTile,
        EchoPayload(message="async"),
        registry=registry,
        plugins=plugins,
        event_bus=bus,
    )

    assert result.echoed == "*async"
    assert counts["tile.started"] == 1
    assert counts["tile.completed"] == 1


class NoNameTile(Tile[EchoPayload, EchoResult]):
    def execute(self, payload: EchoPayload) -> EchoResult:  # pragma: no cover - registration fails first
        return EchoResult(echoed=payload.message)


class BrokenPlugin:
    @hookimpl
    def tile_specs(self):
        yield NoNameTile


class FailingShutdownPlugin:
    @hookimpl
    def tile_specs(self):
        return []

    @hookimpl
    def tile_shutdown(self, ctx, tile, error):
        raise RuntimeError


class MixedPlugin:
    @hookimpl
    def tile_specs(self):
        return [EchoTile, NoNameTile]


class NonIterablePlugin:
    @hookimpl
    def tile_specs(self):
        return PluginTile


def test_plugin_registration_failure_surfaces_error(registry: TileRegistry) -> None:
    plugins = TilePluginManager()
    plugins.register(BrokenPlugin())

    with pytest.raises(TileRegistrationError) as exc_info:
        invoke_tile(
            "echo",
            EchoPayload(message="noop"),
            registry=registry,
            plugins=plugins,
        )

    assert "missing the 'name'" in str(exc_info.value)
    assert [record.name for record in registry.list()] == ["echo"]


def test_plugin_registration_failure_is_atomic(registry: TileRegistry) -> None:
    plugins = TilePluginManager()
    plugins.register(MixedPlugin())

    with pytest.raises(TileRegistrationAggregateError) as exc_info:
        invoke_tile(
            "echo",
            EchoPayload(message="noop"),
            registry=registry,
            plugins=plugins,
        )

    aggregated = exc_info.value
    assert isinstance(aggregated, TileRegistrationAggregateError)
    assert len(aggregated.errors) == 2
    assert [record.name for record in registry.list()] == ["echo"]


def test_shutdown_failure_prevents_completed_event(registry: TileRegistry) -> None:
    plugins = TilePluginManager()
    plugins.register(FailingShutdownPlugin())

    bus = EventBus()
    completed: list[dict[str, object]] = []
    failed: list[dict[str, object]] = []

    bus.subscribe("tile.completed", lambda sender, **payload: completed.append(payload))
    bus.subscribe("tile.failed", lambda sender, **payload: failed.append(payload))

    with pytest.raises(TileExecutionError) as exc_info:
        invoke_tile(
            "echo",
            EchoPayload(message="shutdown"),
            registry=registry,
            plugins=plugins,
            event_bus=bus,
        )

    error = cast(TileExecutionError, exc_info.value)
    assert isinstance(error.original, PluginError)
    assert not completed
    assert len(failed) == 1
    payload = failed[0]
    assert payload["phase"] == "shutdown"
    assert payload.get("original_error") is None
    assert isinstance(payload["error"], PluginError)


def test_shutdown_failure_after_tile_error_surfaces_plugin_error() -> None:
    registry = TileRegistry()
    registry.register(BoomTile)

    plugins = TilePluginManager()
    plugins.register(FailingShutdownPlugin())

    bus = EventBus()
    failures: list[dict[str, object]] = []
    bus.subscribe("tile.failed", lambda sender, **payload: failures.append(payload))

    with pytest.raises(TileExecutionError) as exc_info:
        invoke_tile(
            "boom",
            EchoPayload(message="fail"),
            registry=registry,
            plugins=plugins,
            event_bus=bus,
        )

    exc = cast(TileExecutionError, exc_info.value)
    assert isinstance(exc.original, PluginError)
    assert isinstance(exc.__cause__, ValueError)
    assert len(failures) == 1
    payload = failures[0]
    assert payload["phase"] == "shutdown"
    assert isinstance(payload.get("original_error"), ValueError)
    assert isinstance(payload["error"], PluginError)


class FailingPlugin:
    @hookimpl
    def tile_specs(self):
        yield PluginTile

    @hookimpl
    def tile_startup(self, ctx, tile):
        raise RuntimeError


def test_plugin_startup_failure_emits_runtime_stopped(registry: TileRegistry) -> None:
    plugins = TilePluginManager()
    plugins.register(FailingPlugin())
    bus = EventBus()
    observed: list[str] = []

    for name in ("runtime.started", "runtime.stopped"):

        def handler(sender: str, *, _evt=name, **_: object) -> None:
            observed.append(_evt)

        bus.subscribe(name, handler)

    with pytest.raises(TileExecutionError) as exc_info:
        invoke_tile(
            "plugin-echo",
            EchoPayload(message="plug"),
            registry=registry,
            plugins=plugins,
            event_bus=bus,
        )

    assert observed == ["runtime.started", "runtime.stopped"]
    plugin_error = cast(TileExecutionError, exc_info.value)
    assert isinstance(plugin_error.original, PluginError)


def test_documentation_example_matches_usage() -> None:
    result = run_greeting(name="Tileable")
    assert result.response == "Hi, Tileable!"
