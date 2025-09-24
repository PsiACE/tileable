"""Custom exceptions used across the tileable package."""
from __future__ import annotations

from typing import Any


class TileError(RuntimeError):
    """Base error type for tile-related failures."""


class TileRegistrationError(TileError):
    """Raised when a tile cannot be registered or resolved."""


class TileLookupError(TileRegistrationError):
    """Raised when a tile name is not present in the registry."""


class TileExecutionError(TileError):
    """Raised when the tile execution fails."""

    def __init__(self, tile_name: str, payload: Any, original: BaseException):
        message = f"Tile '{tile_name}' failed: {original!r}"
        super().__init__(message)
        self.tile_name = tile_name
        self.payload = payload
        self.original = original


class PluginError(TileError):
    """Raised when a plugin hook fails."""

    def __init__(self, hook: str, original: BaseException):
        super().__init__(f"Plugin hook '{hook}' failed: {original!r}")
        self.hook = hook
        self.original = original
