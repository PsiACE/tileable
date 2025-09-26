"""Retry helpers implemented as tiles."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from random import Random
from typing import Any

from tileable import (
    EventBus,
    Tile,
    TilePayload,
    TilePluginManager,
    TileRegistry,
    TileResult,
    ainvoke_tile,
    invoke_tile,
)

_RANDOM = Random()  # noqa: S311 - pseudo random suffices for jitter
_RETRY_EXHAUSTED_MSG = "Retry policy exhausted without returning a result"


@dataclass
class RetryPolicy:
    """Retry policy configuration used by :class:`RetryTile`."""

    max_attempts: int = 3
    backoff: float = 0.1
    max_backoff: float | None = 2.0
    jitter: float = 0.1
    retry_exceptions: tuple[type[BaseException], ...] = (Exception,)
    non_retry_exceptions: tuple[type[BaseException], ...] = ()

    def should_retry(self, exc: BaseException, attempt: int) -> bool:
        if attempt >= self.max_attempts:
            return False
        if isinstance(exc, self.non_retry_exceptions):
            return False
        return isinstance(exc, self.retry_exceptions)

    def compute_delay(self, attempt: int) -> float:
        base = self.backoff * (2 ** (attempt - 1))
        if self.max_backoff is not None:
            base = min(base, self.max_backoff)
        jitter = _RANDOM.uniform(0, self.jitter) if self.jitter else 0.0
        return base + jitter


class RetryPayload(TilePayload):
    """Payload wrapping another tile to add retry behaviour."""

    tile: str
    payload: Any
    policy: RetryPolicy | None = None
    event_bus: EventBus | None = None
    state: dict[str, Any] | None = None
    services: dict[str, Any] | None = None
    registry: TileRegistry | None = None
    plugins: TilePluginManager | None = None


class RetryResult(TileResult):
    """Result wrapper exposing the inner result and attempt count."""

    result: Any
    attempts: int


class RetryTile(Tile[RetryPayload, RetryResult]):
    """Execute a tile with retry semantics."""

    name = "retry"
    description = "Retry a tile according to a configurable policy."

    def execute(self, payload: RetryPayload) -> RetryResult:
        ctx = self.context
        policy = payload.policy or RetryPolicy()
        attempts = 0
        shared_state = payload.state if payload.state is not None else ctx.state

        while attempts < policy.max_attempts:
            attempts += 1
            try:
                result = invoke_tile(
                    payload.tile,
                    payload.payload,
                    event_bus=payload.event_bus or ctx.event_bus,
                    state=shared_state,
                    services=payload.services,
                    registry=payload.registry,
                    plugins=payload.plugins,
                )
                return RetryResult(result=result, attempts=attempts)
            except Exception as exc:
                ctx.event_bus.emit(
                    "tile.retrying",
                    tile=payload.tile,
                    attempt=attempts,
                    max_attempts=policy.max_attempts,
                    error=exc,
                )
                if not policy.should_retry(exc, attempts):
                    raise
                delay = policy.compute_delay(attempts)
                time.sleep(delay)

        raise RuntimeError(_RETRY_EXHAUSTED_MSG)

    async def aexecute(self, payload: RetryPayload) -> RetryResult:
        ctx = self.context
        policy = payload.policy or RetryPolicy()
        attempts = 0
        shared_state = payload.state if payload.state is not None else ctx.state

        while attempts < policy.max_attempts:
            attempts += 1
            try:
                result = await ainvoke_tile(
                    payload.tile,
                    payload.payload,
                    event_bus=payload.event_bus or ctx.event_bus,
                    state=shared_state,
                    services=payload.services,
                    registry=payload.registry,
                    plugins=payload.plugins,
                )
                return RetryResult(result=result, attempts=attempts)
            except Exception as exc:
                ctx.event_bus.emit(
                    "tile.retrying",
                    tile=payload.tile,
                    attempt=attempts,
                    max_attempts=policy.max_attempts,
                    error=exc,
                )
                if not policy.should_retry(exc, attempts):
                    raise
                delay = policy.compute_delay(attempts)
                await asyncio.sleep(delay)

        raise RuntimeError(_RETRY_EXHAUSTED_MSG)


__all__ = [
    "RetryPayload",
    "RetryPolicy",
    "RetryResult",
    "RetryTile",
]
