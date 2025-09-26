"""Observability helpers built as tiles."""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from typing import Any, Protocol

from tileable import EventBus, Tile, TilePayload, TilePluginManager, TileRegistry, TileResult, hookimpl, invoke_tile

logfire: Any | None
try:  # Optional dependency
    import logfire as _logfire  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - optional import
    logfire = None
else:
    logfire = _logfire

LOGFIRE_UNAVAILABLE_MSG = "logfire is not available"


class LogEmitter(Protocol):  # pragma: no cover - structural typing only
    def emit(self, event: str, payload: Mapping[str, Any]) -> None:
        """Emit an observability event."""


class _LoggingEmitter:
    """Fallback logger using the stdlib logging module."""

    def __init__(self, *, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger("tileable.logfire")

    def emit(self, event: str, payload: Mapping[str, Any]) -> None:
        self._logger.info("%s %s", event, dict(payload))


class _LogfireEmitter:
    """Adapter around :mod:`logfire` if the dependency is available."""

    def __init__(self) -> None:
        if logfire is None:  # pragma: no cover - defensive
            raise RuntimeError(LOGFIRE_UNAVAILABLE_MSG)

    def emit(self, event: str, payload: Mapping[str, Any]) -> None:  # pragma: no cover - requires logfire
        logfire.log(event, payload)  # type: ignore[attr-defined]


def _resolve_emitter(context_services: Mapping[str, Any]) -> LogEmitter:
    candidate = context_services.get("logfire") or context_services.get("logfire_client")
    if candidate is not None and hasattr(candidate, "emit"):
        emit = candidate.emit
        if callable(emit):
            return candidate  # type: ignore[return-value]
    if logfire is not None:
        return _LogfireEmitter()
    return _LoggingEmitter()


class LogfireObserverPayload(TilePayload):
    """Payload for :class:`LogfireObserverTile`.

    Attributes:
        tile: Target tile name to invoke.
        payload: Payload object to pass to the target tile.
        metadata: Optional metadata appended to emitted events.
        event_bus: Optional event bus override; defaults to the observer's bus.
        state: Optional state dictionary shared with the target tile.
        services: Optional services mapping passed to the target tile.
    """

    tile: str
    payload: Any
    metadata: dict[str, Any] | None = None
    event_bus: EventBus | None = None
    state: dict[str, Any] | None = None
    services: dict[str, Any] | None = None
    registry: TileRegistry | None = None
    plugins: TilePluginManager | None = None


class LogfireObserverResult(TileResult):
    """Wraps the original tile result along with telemetry metadata."""

    result: Any
    duration_ms: float
    metadata: dict[str, Any]


class LogfireObserverTile(Tile[LogfireObserverPayload, LogfireObserverResult]):
    """Tile that executes another tile while emitting Logfire-friendly events."""

    name = "logfire-observer"
    description = "Wrap a tile execution with Logfire observability events."

    def execute(self, payload: LogfireObserverPayload) -> LogfireObserverResult:
        ctx = self.context
        emitter = _resolve_emitter(ctx.services)
        metadata = {"tile": payload.tile, **(payload.metadata or {})}

        start_time = time.perf_counter()
        emitter.emit("tile.observer.started", {"metadata": metadata})

        shared_state = payload.state if payload.state is not None else ctx.state
        target_services = payload.services

        try:
            result = invoke_tile(
                payload.tile,
                payload.payload,
                event_bus=payload.event_bus or ctx.event_bus,
                state=shared_state,
                services=target_services,
                registry=payload.registry,
                plugins=payload.plugins,
            )
        except Exception as exc:
            duration = (time.perf_counter() - start_time) * 1000
            emitter.emit(
                "tile.observer.failed",
                {"metadata": metadata, "error": repr(exc), "duration_ms": duration},
            )
            raise

        duration = (time.perf_counter() - start_time) * 1000
        emitter.emit(
            "tile.observer.completed",
            {"metadata": metadata, "duration_ms": duration},
        )
        return LogfireObserverResult(result=result, duration_ms=duration, metadata=metadata)


class LogfireObserverPlugin:
    """Plugin that ensures a logfire-compatible emitter is available."""

    def __init__(self, emitter: LogEmitter | None = None) -> None:
        self._emitter = emitter

    @hookimpl
    def tile_startup(self, ctx, tile) -> None:
        if ctx.get_service_or("logfire") is not None:
            return
        if self._emitter is not None:
            ctx.set_service("logfire", self._emitter)
            return
        if logfire is not None:
            ctx.set_service("logfire", _LogfireEmitter())
        else:
            ctx.set_service("logfire", _LoggingEmitter())


__all__ = [
    "LogfireObserverPayload",
    "LogfireObserverPlugin",
    "LogfireObserverResult",
    "LogfireObserverTile",
]
