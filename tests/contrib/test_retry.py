from __future__ import annotations

import pytest

from tileable import EventBus, TilePayload, TileRegistry, invoke_tile
from tileable.contrib.retry import RetryPayload, RetryPolicy, RetryTile
from tileable.schema import TileResult
from tileable.tile import Tile


class CounterPayload(TilePayload):
    threshold: int


class CounterResult(TileResult):
    attempts: int


class FlakyTile(Tile[CounterPayload, CounterResult]):
    name = "flaky"

    def execute(self, payload: CounterPayload) -> CounterResult:
        attempts = self.context.state.setdefault("attempts", 0) + 1
        self.context.state["attempts"] = attempts
        if attempts < payload.threshold:
            raise RuntimeError("boom")
        return CounterResult(attempts=attempts)


def test_retry_tile_eventually_succeeds() -> None:
    registry = TileRegistry()
    registry.register(FlakyTile)

    bus = EventBus()
    state: dict[str, object] = {}

    result = invoke_tile(
        RetryTile,
        RetryPayload(
            tile="flaky",
            payload=CounterPayload(threshold=3),
            policy=RetryPolicy(max_attempts=5, backoff=0.0, jitter=0.0),
            event_bus=bus,
            registry=registry,
        ),
        registry=registry,
        state=state,
    )

    assert result.result.attempts == 3
    assert state["attempts"] == 3


def test_retry_tile_raises_after_exhaustion() -> None:
    registry = TileRegistry()
    registry.register(FlakyTile)

    with pytest.raises(RuntimeError) as exc_info:
        invoke_tile(
            RetryTile,
            RetryPayload(
                tile="flaky",
                payload=CounterPayload(threshold=5),
                policy=RetryPolicy(max_attempts=2, backoff=0.0, jitter=0.0),
                registry=registry,
            ),
            registry=registry,
            state={},
        )

    assert "boom" in str(exc_info.value)
