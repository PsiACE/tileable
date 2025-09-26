"""Huey queue integration built as tiles."""

from __future__ import annotations

from typing import Any, Protocol

from tileable import Tile, TilePayload, TilePluginManager, TileRegistry, TileResult, hookimpl, invoke_tile

huey_module: Any | None
try:  # Optional dependency to satisfy packaging extras
    import huey as _huey  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - optional import
    huey_module = None
else:
    huey_module = _huey

_MISSING_DISPATCHER_MSG = "Huey dispatcher not provided and no 'huey_dispatcher' service registered"


class HueyDispatcher(Protocol):  # pragma: no cover - structural typing only
    def enqueue(
        self,
        *,
        tile: str,
        payload: Any,
        eta: float | None = None,
        queue: str | None = None,
    ) -> str:
        """Submit a tile invocation to the queue and return a task identifier."""


class HueyWorker(Protocol):  # pragma: no cover - structural typing only
    def __call__(self, tile: str, payload: Any) -> Any:
        """Execute the tile inside a worker process."""


class HueyDispatchPayload(TilePayload):
    """Payload accepted by :class:`HueyDispatchTile`."""

    tile: str
    payload: Any
    queue: str | None = None
    eta: float | None = None
    wait: bool = False
    dispatcher: Any | None = None
    registry: TileRegistry | None = None
    plugins: TilePluginManager | None = None


class HueyResult(TileResult):
    task_id: str | None
    status: str
    result: Any | None = None


class HueyDispatchTile(Tile[HueyDispatchPayload, HueyResult]):
    """Enqueue tile execution through a Huey-like dispatcher."""

    name = "huey-dispatch"
    description = "Dispatch tiles to a Huey-compatible queue."

    def execute(self, payload: HueyDispatchPayload) -> HueyResult:
        ctx = self.context
        dispatcher = payload.dispatcher
        if dispatcher is None:
            try:
                dispatcher = ctx.get_service("huey_dispatcher")
            except KeyError as exc:
                raise KeyError(_MISSING_DISPATCHER_MSG) from exc
        if not hasattr(dispatcher, "enqueue"):
            msg = "Huey dispatcher must implement an enqueue(tile=..., payload=...) method"
            raise TypeError(msg)

        task_id = dispatcher.enqueue(
            tile=payload.tile,
            payload=payload.payload,
            eta=payload.eta,
            queue=payload.queue,
        )

        if payload.wait:
            result = invoke_tile(
                payload.tile,
                payload.payload,
                event_bus=ctx.event_bus,
                registry=payload.registry,
                plugins=payload.plugins,
                state=ctx.state,
            )
            return HueyResult(task_id=task_id, status="completed", result=result)
        return HueyResult(task_id=task_id, status="queued")


class HueyWorkerPayload(TilePayload):
    """Payload processed by :class:`HueyWorkerTile`."""

    tile: str
    payload: Any
    registry: TileRegistry | None = None
    plugins: TilePluginManager | None = None


class HueyWorkerResult(TileResult):
    result: Any


class HueyWorkerTile(Tile[HueyWorkerPayload, HueyWorkerResult]):
    """Execute a tile inside a worker process."""

    name = "huey-worker"
    description = "Execute queued tile invocations inside a Huey worker."

    def execute(self, payload: HueyWorkerPayload) -> HueyWorkerResult:
        result = invoke_tile(
            payload.tile,
            payload.payload,
            event_bus=self.context.event_bus,
            registry=payload.registry,
            plugins=payload.plugins,
            state=self.context.state,
        )
        return HueyWorkerResult(result=result)


class HueyPlugin:
    """Plugin that injects a Huey dispatcher into tile context services."""

    def __init__(self, dispatcher: Any) -> None:
        self._dispatcher = dispatcher

    @hookimpl
    def tile_startup(self, ctx, tile) -> None:
        if ctx.get_service_or("huey_dispatcher") is None:
            ctx.set_service("huey_dispatcher", self._dispatcher)


__all__ = [
    "HueyDispatchPayload",
    "HueyDispatchTile",
    "HueyPlugin",
    "HueyResult",
    "HueyWorkerPayload",
    "HueyWorkerResult",
    "HueyWorkerTile",
]
