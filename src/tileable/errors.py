"""Custom exceptions used across the tileable package."""

from __future__ import annotations

from typing import Any


class TileError(RuntimeError):
    """Base error type for tile-related failures."""


class TileRegistrationError(TileError):
    """Raised when a tile cannot be registered or resolved."""

    @classmethod
    def not_subclass(cls, tile_cls: type[Any]) -> TileRegistrationError:
        return cls(f"{tile_cls!r} is not a Tile subclass")

    @classmethod
    def missing_name(cls, tile_cls: type[Any]) -> TileRegistrationError:
        return cls(f"Tile class {tile_cls.__name__} is missing the 'name' attribute")

    @classmethod
    def duplicate(cls, name: str) -> TileRegistrationError:
        return cls(f"Tile '{name}' is already registered")

    @classmethod
    def unsupported_reference(cls, ref: Any) -> TileRegistrationError:
        return cls(f"Unsupported tile reference: {ref!r}")


class TileLookupError(TileRegistrationError):
    """Raised when a tile name is not present in the registry."""

    @classmethod
    def missing(cls, name: str) -> TileLookupError:
        return cls(f"Tile '{name}' is not registered")


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
