"""Tileable - The modular framework for your ideas."""

from __future__ import annotations

from .context import TileContext
from .errors import (
    PluginError,
    TileError,
    TileExecutionError,
    TileLookupError,
    TileRegistrationAggregateError,
    TileRegistrationError,
)
from .events import (
    STANDARD_EVENTS,
    CapturedEvent,
    EventBus,
    EventRecorder,
    get_event_bus,
    reset_event_bus,
    set_event_bus,
)
from .plugins import HookSpecs, TilePluginManager, hookimpl, hookspec
from .registry import TileRecord, TileRegistry
from .runtime import (
    ainvoke_tile,
    get_plugins,
    get_registry,
    invoke_tile,
    reset_plugins,
    reset_registry,
    reset_runtime_defaults,
    scoped_runtime,
    set_plugins,
    set_registry,
)
from .schema import TilePayload, TileResult
from .tile import Tile

__all__ = [
    "STANDARD_EVENTS",
    "CapturedEvent",
    "EventBus",
    "EventRecorder",
    "HookSpecs",
    "PluginError",
    "Tile",
    "TileContext",
    "TileError",
    "TileExecutionError",
    "TileLookupError",
    "TilePayload",
    "TilePluginManager",
    "TileRecord",
    "TileRegistrationAggregateError",
    "TileRegistrationError",
    "TileRegistry",
    "TileResult",
    "ainvoke_tile",
    "get_event_bus",
    "get_plugins",
    "get_registry",
    "hookimpl",
    "hookspec",
    "invoke_tile",
    "reset_event_bus",
    "reset_plugins",
    "reset_registry",
    "reset_runtime_defaults",
    "scoped_runtime",
    "set_event_bus",
    "set_plugins",
    "set_registry",
]
