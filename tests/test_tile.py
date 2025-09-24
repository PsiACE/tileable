from __future__ import annotations

import pytest

from tileable.context import TileContext
from tileable.events import EventBus
from tileable.schema import TilePayload, TileResult
from tileable.tile import Tile


class Payload(TilePayload):
    value: int


class Result(TileResult):
    value: int


class SimpleTile(Tile[Payload, Result]):
    name = "simple"

    def execute(self, payload: Payload) -> Result:
        return Result(value=payload.value)


def test_tile_requires_context_before_use() -> None:
    tile = SimpleTile()

    with pytest.raises(RuntimeError):
        _ = tile.context

    ctx = TileContext(event_bus=EventBus())
    tile.set_context(ctx)
    assert tile.context is ctx
