"""Tile registry keeping track of available tile classes."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from .errors import TileLookupError, TileRegistrationError
from .tile import Tile


@dataclass(frozen=True)
class TileRecord:
    """Metadata describing a registered tile."""

    name: str
    tile_cls: type[Tile[Any, Any]]
    description: str | None
    source: str | None = None


class TileRegistry:
    """Central registry for tile classes."""

    def __init__(self) -> None:
        self._tiles: dict[str, TileRecord] = {}

    def register(self, tile_cls: type[Tile[Any, Any]], *, source: str | None = None) -> None:
        if not issubclass(tile_cls, Tile):
            raise TileRegistrationError.not_subclass(tile_cls)
        name = getattr(tile_cls, "name", None)
        if not name:
            raise TileRegistrationError.missing_name(tile_cls)
        if name in self._tiles:
            raise TileRegistrationError.duplicate(name)
        description = getattr(tile_cls, "description", None)
        self._tiles[name] = TileRecord(name=name, tile_cls=tile_cls, description=description, source=source)

    def bulk_register(self, tiles: Iterable[type[Tile[Any, Any]]], *, source: str | None = None) -> None:
        for tile_cls in tiles:
            self.register(tile_cls, source=source)

    def get(self, name: str) -> type[Tile[Any, Any]]:
        try:
            return self._tiles[name].tile_cls
        except KeyError as exc:
            raise TileLookupError.missing(name) from exc

    def info(self, name: str) -> TileRecord:
        try:
            return self._tiles[name]
        except KeyError as exc:
            raise TileLookupError.missing(name) from exc

    def list(self) -> list[TileRecord]:
        return list(self._tiles.values())

    def __contains__(self, name: object) -> bool:
        return name in self._tiles
