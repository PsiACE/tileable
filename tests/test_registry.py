from __future__ import annotations

import pytest

from tileable.registry import TileRecord, TileRegistry
from tileable.tile import Tile
from tileable.schema import TilePayload, TileResult
from tileable.errors import TileLookupError, TileRegistrationError


class Payload(TilePayload):
    value: int


class Result(TileResult):
    doubled: int


class DemoTile(Tile[Payload, Result]):
    name = "demo"

    def execute(self, payload: Payload) -> Result:
        return Result(doubled=payload.value * 2)


def test_registry_register_and_retrieve() -> None:
    registry = TileRegistry()
    registry.register(DemoTile)

    record = registry.info("demo")
    assert isinstance(record, TileRecord)
    assert record.tile_cls is DemoTile
    assert "demo" in registry
    assert registry.get("demo") is DemoTile


def test_registry_bulk_register_and_list() -> None:
    registry = TileRegistry()

    class AnotherTile(DemoTile):
        name = "another"

    registry.bulk_register([DemoTile, AnotherTile], source="plugins")

    names = sorted(record.name for record in registry.list())
    assert names == ["another", "demo"]


def test_registry_rejects_invalid_tiles() -> None:
    registry = TileRegistry()

    class NoNameTile(Tile[Payload, Result]):
        def execute(self, payload: Payload) -> Result:  # pragma: no cover - not executed
            return Result(doubled=payload.value)

    with pytest.raises(TileRegistrationError):
        registry.register(NO_TILE := type("NotATile", (), {}))  # type: ignore[arg-type]

    with pytest.raises(TileRegistrationError):
        registry.register(NoNameTile)

    registry.register(DemoTile)
    with pytest.raises(TileRegistrationError):
        registry.register(DemoTile)


def test_registry_lookup_errors() -> None:
    registry = TileRegistry()
    with pytest.raises(TileLookupError):
        registry.get("missing")
    with pytest.raises(TileLookupError):
        registry.info("missing")
