"""Plugin integration powered by :mod:`pluggy`."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pluggy

from .errors import PluginError

hookspec = pluggy.HookspecMarker("tileable")
hookimpl = pluggy.HookimplMarker("tileable")


class HookSpecs:
    """Hook specification container registered with :class:`pluggy.PluginManager`."""

    @hookspec
    def tile_specs(self) -> Iterable[type]:  # pragma: no cover - executed via Pluggy
        """Yield or return an iterable of tile classes to register."""
        raise NotImplementedError

    @hookspec
    def tile_startup(self, ctx: Any, tile: Any) -> None:  # pragma: no cover - executed via Pluggy
        """Run before a tile executes."""
        raise NotImplementedError

    @hookspec
    def tile_shutdown(
        self, ctx: Any, tile: Any, error: BaseException | None
    ) -> None:  # pragma: no cover - executed via Pluggy
        """Run after a tile executes, regardless of success."""
        raise NotImplementedError


class TilePluginManager:
    """Thin wrapper around :class:`pluggy.PluginManager` with helpful utilities."""

    def __init__(self) -> None:
        self._manager = pluggy.PluginManager("tileable")
        self._manager.add_hookspecs(HookSpecs)

    @property
    def hook(self) -> pluggy.PluginManager.hook:  # type: ignore[valid-type]
        return self._manager.hook

    def register(self, plugin: Any, name: str | None = None) -> None:
        if self._manager.is_registered(plugin):
            raise PluginError("register", ValueError(f"Plugin {plugin!r} is already registered"))
        if name is not None and self._manager.has_plugin(name):
            raise PluginError("register", ValueError(f"Plugin name '{name}' is already registered"))
        self._manager.register(plugin, name=name)

    def iter_tiles(self) -> Iterable[type]:
        hook = self._manager.hook.tile_specs
        try:
            contributions = hook()
        except Exception as exc:  # pragma: no cover - defensive path
            raise PluginError("tile_specs", exc) from exc

        implementations = hook.get_hookimpls()
        for impl, contribution in zip(implementations, contributions, strict=False):
            if contribution is None:
                continue
            if not isinstance(contribution, Iterable):
                plugin_name = impl.plugin_name or repr(impl.plugin)
                error = TypeError(f"Plugin {plugin_name} returned non-iterable tile_specs result")
                raise PluginError("tile_specs", error) from error
            yield from contribution

    def startup(self, *, ctx: Any, tile: Any) -> None:
        try:
            self._manager.hook.tile_startup(ctx=ctx, tile=tile)
        except Exception as exc:
            raise PluginError("tile_startup", exc) from exc

    def shutdown(self, *, ctx: Any, tile: Any, error: BaseException | None) -> None:
        try:
            self._manager.hook.tile_shutdown(ctx=ctx, tile=tile, error=error)
        except Exception as exc:
            raise PluginError("tile_shutdown", exc) from exc
