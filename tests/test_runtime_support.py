from __future__ import annotations

from collections.abc import Iterable

from tileable.plugins import TilePluginManager, hookimpl
from tileable.registry import TileRegistry
from tileable.runtime import get_plugins, get_registry
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
