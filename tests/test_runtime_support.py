from __future__ import annotations

from collections.abc import Iterable

from tileable.plugins import TilePluginManager, hookimpl
from tileable.registry import TileRegistry
from tileable.runtime import get_plugins, get_registry, invoke_tile, scoped_runtime
from tileable.schema import TilePayload, TileResult
from tileable.tile import Tile


def test_default_singletons_are_reused() -> None:
    assert get_registry() is get_registry()
    assert get_plugins() is get_plugins()


class Payload(TilePayload):
    value: int


class Result(TileResult):
    doubled: int


class DoublerTile(Tile[Payload, Result]):
    name = "doubler"

    def execute(self, payload: Payload) -> Result:
        return Result(doubled=payload.value * 2)


class ExamplePlugin:
    @hookimpl
    def tile_specs(self) -> Iterable[type[Tile[Payload, Result]]]:
        yield DoublerTile


class ContextTile(Tile[Payload, Result]):
    name = "context"

    def execute(self, payload: Payload) -> Result:
        self.context.set_service("observed", payload.value)
        self.context.state["seen"] = payload.value
        return Result(doubled=payload.value * 3)


def test_plugin_iter_tiles_yields_unique_tiles() -> None:
    registry = TileRegistry()
    manager = TilePluginManager()
    manager.register(ExamplePlugin())

    collected = list(manager.iter_tiles())
    assert collected == [DoublerTile]

    # Registering again should not produce duplicates in registry refresh logic
    registry.register(DoublerTile)
    manager.register(ExamplePlugin())
    assert next(iter(manager.iter_tiles())) is DoublerTile


def test_invoke_tile_return_context_exposes_mutations() -> None:
    registry = TileRegistry()
    registry.register(ContextTile)
    state: dict[str, object] = {"runs": 0}

    result, ctx = invoke_tile(
        "context",
        Payload(value=7),
        registry=registry,
        state=state,
        return_context=True,
    )

    assert result.doubled == 21
    assert dict(ctx.services)["observed"] == 7
    assert ctx.state["seen"] == 7
    assert state["seen"] == 7


def test_scoped_runtime_restores_defaults() -> None:
    original_registry = get_registry()
    original_plugins = get_plugins()

    replacement_registry = TileRegistry()
    replacement_plugins = TilePluginManager()

    with scoped_runtime(registry=replacement_registry, plugins=replacement_plugins):
        assert get_registry() is replacement_registry
        assert get_plugins() is replacement_plugins

    assert get_registry() is original_registry
    assert get_plugins() is original_plugins
