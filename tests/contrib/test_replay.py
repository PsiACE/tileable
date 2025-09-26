from __future__ import annotations

import json
from pathlib import Path

from tileable import EventBus, TilePayload, TileRegistry, invoke_tile
from tileable.contrib.replay import ReplayPayload, ReplayRecorder, ReplaySeed, ReplayTile
from tileable.schema import TileResult
from tileable.tile import Tile


class AuditPayload(TilePayload):
    value: int


class AuditResult(TileResult):
    doubled: int


class AuditTile(Tile[AuditPayload, AuditResult]):
    name = "audit"

    def execute(self, payload: AuditPayload) -> AuditResult:
        if isinstance(payload, dict):
            payload = AuditPayload.model_validate(payload)
        doubled = payload.value * 2
        self.context.emit("tile.debug", tile=self.name, doubled=doubled)
        return AuditResult(doubled=doubled)


def test_replay_seed_roundtrip(tmp_path: Path) -> None:
    registry = TileRegistry()
    registry.register(AuditTile)
    bus = EventBus()

    with ReplayRecorder(bus, "tile.debug") as recorder:
        result = invoke_tile("audit", AuditPayload(value=2), registry=registry, event_bus=bus)

    assert result.doubled == 4
    seed = recorder.to_seed(tile="audit", payload=AuditPayload(value=2))
    path = tmp_path / "seed.json"
    seed.save(path)
    loaded = ReplaySeed.load(path)

    assert loaded.tile == "audit"
    assert loaded.payload == {"value": 2}
    assert loaded.events == recorder.events


def test_replay_tile_validates_events(tmp_path: Path) -> None:
    registry = TileRegistry()
    registry.register(AuditTile)
    bus = EventBus()

    with ReplayRecorder(bus, "tile.debug") as recorder:
        invoke_tile("audit", AuditPayload(value=3), registry=registry, event_bus=bus)

    seed = recorder.to_seed(tile="audit", payload=AuditPayload(value=3))
    path = tmp_path / "seed.json"
    seed.save(path)

    result = invoke_tile(
        ReplayTile,
        ReplayPayload(seed_path=str(path), registry=registry),
        event_bus=bus,
        registry=registry,
    )

    assert result.matches is True
    assert result.events == seed.events

    # Tamper with seed to force mismatch
    tampered = json.loads(path.read_text())
    tampered["events"][0]["payload"]["doubled"] = 999
    path.write_text(json.dumps(tampered))

    result = invoke_tile(
        ReplayTile,
        ReplayPayload(seed_path=str(path), registry=registry),
        event_bus=bus,
        registry=registry,
    )

    assert result.matches is False
    assert result.mismatches
