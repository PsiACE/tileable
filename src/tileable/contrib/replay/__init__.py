"""Replay helpers for reproducing tile runs."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tileable import EventBus, Tile, TilePayload, TilePluginManager, TileRegistry, TileResult, invoke_tile


@dataclass
class ReplaySeed:
    """Serialized description of a tile invocation."""

    tile: str
    payload: Any
    state: dict[str, Any] | None = None
    services: dict[str, Any] | None = None
    events: list[dict[str, Any]] | None = None

    def to_json(self) -> str:
        return json.dumps(
            {
                "tile": self.tile,
                "payload": self.payload,
                "state": self.state,
                "services": self.services,
                "events": self.events,
            },
            default=lambda value: value.model_dump() if hasattr(value, "model_dump") else value,
        )

    def save(self, path: str | Path) -> None:
        Path(path).write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> ReplaySeed:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            tile=data["tile"],
            payload=data["payload"],
            state=data.get("state"),
            services=data.get("services"),
            events=data.get("events"),
        )


_MISSING_REPLAY_SEED_MSG = "ReplayPayload requires either `seed` or `seed_path`."


class ReplayRecorder:
    """Context manager that records events and state for later replay."""

    def __init__(self, bus: EventBus, *events: str) -> None:
        self._bus = bus
        self._events = events or ("runtime.started", "runtime.stopped", "tile.started", "tile.completed", "tile.failed")
        self._records: list[dict[str, Any]] = []
        self._unsubscribers: list[Callable[[], None]] = []

    def __enter__(self) -> ReplayRecorder:
        for event in self._events:
            unsubscribe = self._bus.subscribe(event, self._make_handler(event), weak=False)
            self._unsubscribers.append(unsubscribe)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - deterministic teardown
        while self._unsubscribers:
            unsubscribe = self._unsubscribers.pop()
            unsubscribe()

    def _make_handler(self, name: str):
        def handler(sender: str, **payload: Any) -> None:
            entry = {"event": name, "sender": sender, "payload": payload}
            self._records.append(entry)

        return handler

    @property
    def events(self) -> list[dict[str, Any]]:
        return list(self._records)

    def to_seed(
        self,
        *,
        tile: str,
        payload: Any,
        state: dict[str, Any] | None = None,
        services: dict[str, Any] | None = None,
    ) -> ReplaySeed:
        return ReplaySeed(tile=tile, payload=payload, state=state, services=services, events=self.events)


class ReplayPayload(TilePayload):
    """Payload for :class:`ReplayTile`."""

    seed: ReplaySeed | None = None
    seed_path: str | None = None
    validate_events: bool = True
    registry: TileRegistry | None = None
    plugins: TilePluginManager | None = None


class ReplayResult(TileResult):
    """Result of a replayed tile invocation."""

    result: Any
    events: list[dict[str, Any]]
    matches: bool
    mismatches: list[str]


class ReplayTile(Tile[ReplayPayload, ReplayResult]):
    """Re-execute a tile from a previously recorded seed."""

    name = "replay"
    description = "Replay a recorded tile invocation from a seed."

    def execute(self, payload: ReplayPayload) -> ReplayResult:
        ctx = self.context
        seed = payload.seed or (ReplaySeed.load(payload.seed_path) if payload.seed_path else None)
        if seed is None:
            raise ValueError(_MISSING_REPLAY_SEED_MSG)

        state = seed.state.copy() if seed.state is not None else {}
        services = seed.services.copy() if seed.services is not None else None

        event_names = tuple(entry["event"] for entry in (seed.events or [])) or (
            "tile.started",
            "tile.completed",
            "tile.failed",
        )

        with ReplayRecorder(ctx.event_bus, *event_names) as recorder:
            result = invoke_tile(
                seed.tile,
                seed.payload,
                event_bus=ctx.event_bus,
                state=state,
                services=services,
                registry=payload.registry,
                plugins=payload.plugins,
            )

        events = recorder.events
        mismatches: list[str] = []
        if payload.validate_events and seed.events is not None:
            if len(events) != len(seed.events):
                mismatches.append("Event count differs from seed")
            for idx, (expected, observed) in enumerate(zip(seed.events or [], events, strict=False)):
                if expected != observed:
                    mismatches.append(f"Event mismatch at index {idx}")

        return ReplayResult(result=result, events=events, matches=not mismatches, mismatches=mismatches)


__all__ = [
    "ReplayPayload",
    "ReplayRecorder",
    "ReplayResult",
    "ReplaySeed",
    "ReplayTile",
]
