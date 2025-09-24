"""Execution helpers for running tiles."""
from __future__ import annotations

import inspect
from typing import Any, Mapping, MutableMapping, Tuple, TypeAlias, TypeVar

from .context import TileContext
from .errors import TileExecutionError, TileRegistrationError
from .events import EventBus, get_event_bus
from .plugins import TilePluginManager
from .registry import TileRegistry
from .tile import Tile

TileRef: TypeAlias = str | type[Tile[Any, Any]] | Tile[Any, Any]
PayloadT = TypeVar("PayloadT", bound=Any)
ResultT = TypeVar("ResultT", bound=Any)

_default_registry = TileRegistry()
_default_plugins = TilePluginManager()


def get_registry() -> TileRegistry:
    return _default_registry


def get_plugins() -> TilePluginManager:
    return _default_plugins


def _coerce_tile(tile: TileRef, registry: TileRegistry) -> Tuple[type[Tile[Any, Any]], Tile[Any, Any]]:
    if isinstance(tile, Tile):
        return type(tile), tile
    if isinstance(tile, str):
        tile_cls = registry.get(tile)
        return tile_cls, tile_cls()
    if inspect.isclass(tile) and issubclass(tile, Tile):
        return tile, tile()
    raise TileRegistrationError(f"Unsupported tile reference: {tile!r}")


def _prepare_context(
    *,
    tile: Tile[Any, Any],
    event_bus: EventBus,
    services: Mapping[str, Any] | None,
    state: MutableMapping[str, Any] | None,
) -> TileContext:
    ctx = TileContext(event_bus=event_bus, services=services, state=state)
    tile.set_context(ctx)
    return ctx


def _refresh_registry_from_plugins(registry: TileRegistry, plugins: TilePluginManager) -> None:
    for tile_cls in plugins.iter_tiles():
        name = getattr(tile_cls, "name", None)
        if name and name in registry:
            continue
        try:
            registry.register(tile_cls, source=getattr(tile_cls, "__module__", None))
        except TileRegistrationError:
            continue


def _resolve_invocation(
    tile: TileRef,
    payload: Any,
    *,
    registry: TileRegistry | None,
    event_bus: EventBus | None,
    plugins: TilePluginManager | None,
    services: Mapping[str, Any] | None,
    state: MutableMapping[str, Any] | None,
) -> tuple[type[Tile[Any, Any]], Tile[Any, Any], TileContext, EventBus, TilePluginManager]:
    registry = registry or _default_registry
    plugins = plugins or _default_plugins
    _refresh_registry_from_plugins(registry, plugins)
    resolved_bus = event_bus or get_event_bus()
    tile_cls, tile_obj = _coerce_tile(tile, registry)
    ctx = _prepare_context(tile=tile_obj, event_bus=resolved_bus, services=services, state=state)
    return tile_cls, tile_obj, ctx, resolved_bus, plugins


def _start_invocation(
    *,
    tile_cls: type[Tile[Any, Any]],
    tile_obj: Tile[Any, Any],
    payload: Any,
    ctx: TileContext,
    event_bus: EventBus,
    plugins: TilePluginManager,
) -> None:
    event_bus.emit("runtime.started", tile=tile_cls.name, payload=payload, services=ctx.services)
    try:
        plugins.startup(ctx=ctx, tile=tile_obj)
    except Exception:
        event_bus.emit("runtime.stopped", tile=tile_cls.name, payload=payload)
        tile_obj.set_context(None)
        raise
    event_bus.emit("tile.started", tile=tile_cls.name, payload=payload)


def _complete_invocation(
    *,
    tile_cls: type[Tile[Any, Any]],
    tile_obj: Tile[Any, Any],
    payload: Any,
    result: Any,
    ctx: TileContext,
    event_bus: EventBus,
    plugins: TilePluginManager,
) -> Any:
    event_bus.emit("tile.completed", tile=tile_cls.name, payload=payload, result=result)
    plugins.shutdown(ctx=ctx, tile=tile_obj, error=None)
    return result


def _handle_execution_failure(
    *,
    tile_cls: type[Tile[Any, Any]],
    tile_obj: Tile[Any, Any],
    payload: Any,
    ctx: TileContext,
    event_bus: EventBus,
    plugins: TilePluginManager,
    error: Exception,
) -> None:
    event_bus.emit("tile.failed", tile=tile_cls.name, payload=payload, error=error)
    plugins.shutdown(ctx=ctx, tile=tile_obj, error=error)
    raise TileExecutionError(tile_cls.name, payload, error) from error


def _finalize_invocation(
    *,
    tile_cls: type[Tile[Any, Any]],
    tile_obj: Tile[Any, Any],
    payload: Any,
    event_bus: EventBus,
    started: bool,
) -> None:
    if started:
        event_bus.emit("runtime.stopped", tile=tile_cls.name, payload=payload)
    tile_obj.set_context(None)


def invoke_tile(
    tile: TileRef,
    payload: Any,
    *,
    registry: TileRegistry | None = None,
    event_bus: EventBus | None = None,
    plugins: TilePluginManager | None = None,
    services: Mapping[str, Any] | None = None,
    state: MutableMapping[str, Any] | None = None,
) -> Any:
    """Execute ``tile`` synchronously and return the result."""

    tile_cls, tile_obj, ctx, resolved_bus, resolved_plugins = _resolve_invocation(
        tile,
        payload,
        registry=registry,
        event_bus=event_bus,
        plugins=plugins,
        services=services,
        state=state,
    )

    started = False
    try:
        _start_invocation(
            tile_cls=tile_cls,
            tile_obj=tile_obj,
            payload=payload,
            ctx=ctx,
            event_bus=resolved_bus,
            plugins=resolved_plugins,
        )
        started = True
        result = tile_obj.execute(payload)
    except TileExecutionError:
        raise
    except Exception as exc:
        _handle_execution_failure(
            tile_cls=tile_cls,
            tile_obj=tile_obj,
            payload=payload,
            ctx=ctx,
            event_bus=resolved_bus,
            plugins=resolved_plugins,
            error=exc,
        )
    else:
        return _complete_invocation(
            tile_cls=tile_cls,
            tile_obj=tile_obj,
            payload=payload,
            result=result,
            ctx=ctx,
            event_bus=resolved_bus,
            plugins=resolved_plugins,
        )
    finally:
        _finalize_invocation(
            tile_cls=tile_cls,
            tile_obj=tile_obj,
            payload=payload,
            event_bus=resolved_bus,
            started=started,
        )


async def ainvoke_tile(
    tile: TileRef,
    payload: Any,
    *,
    registry: TileRegistry | None = None,
    event_bus: EventBus | None = None,
    plugins: TilePluginManager | None = None,
    services: Mapping[str, Any] | None = None,
    state: MutableMapping[str, Any] | None = None,
) -> Any:
    """Async counterpart to :func:`invoke_tile`."""

    tile_cls, tile_obj, ctx, resolved_bus, resolved_plugins = _resolve_invocation(
        tile,
        payload,
        registry=registry,
        event_bus=event_bus,
        plugins=plugins,
        services=services,
        state=state,
    )

    started = False
    try:
        _start_invocation(
            tile_cls=tile_cls,
            tile_obj=tile_obj,
            payload=payload,
            ctx=ctx,
            event_bus=resolved_bus,
            plugins=resolved_plugins,
        )
        started = True
        result = await tile_obj.aexecute(payload)
    except TileExecutionError:
        raise
    except Exception as exc:
        _handle_execution_failure(
            tile_cls=tile_cls,
            tile_obj=tile_obj,
            payload=payload,
            ctx=ctx,
            event_bus=resolved_bus,
            plugins=resolved_plugins,
            error=exc,
        )
    else:
        return _complete_invocation(
            tile_cls=tile_cls,
            tile_obj=tile_obj,
            payload=payload,
            result=result,
            ctx=ctx,
            event_bus=resolved_bus,
            plugins=resolved_plugins,
        )
    finally:
        _finalize_invocation(
            tile_cls=tile_cls,
            tile_obj=tile_obj,
            payload=payload,
            event_bus=resolved_bus,
            started=started,
        )
