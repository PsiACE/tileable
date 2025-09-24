"""Event bus abstraction built on top of :mod:`blinker`."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from blinker import Namespace

STANDARD_EVENTS = (
    "runtime.started",
    "runtime.stopped",
    "tile.started",
    "tile.completed",
    "tile.failed",
    "tile.debug",
)


class EventBus:
    """Small helper around :class:`blinker.Namespace`.

    The bus exposes ``emit``/``subscribe``/``unsubscribe`` methods to keep the
    public API tiny while still giving developers full control over the
    underlying signal system.
    """

    def __init__(self) -> None:
        self._namespace = Namespace()

    def emit(self, event: str, /, **payload: Any) -> None:
        """Broadcast ``payload`` to all subscribers of ``event``."""

        signal = self._namespace.signal(event)
        signal.send(event, **payload)

    def subscribe(self, event: str, handler: Callable[..., Any], *, weak: bool = False) -> Callable[[], None]:
        """Register ``handler`` for ``event`` and return an unsubscribe callback."""

        signal = self._namespace.signal(event)
        signal.connect(handler, weak=weak)
        return lambda: signal.disconnect(handler)

    def unsubscribe(self, event: str, handler: Callable[..., Any]) -> None:
        """Remove ``handler`` from ``event`` subscribers if previously registered."""

        signal = self._namespace.signal(event)
        signal.disconnect(handler)


_default_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Get a shared :class:`EventBus` instance.

    The helper keeps the footprint tiny for users who prefer not to manually
    manage bus instances yet allows passing a custom bus everywhere if desired.
    """

    global _default_bus

    if _default_bus is None:
        _default_bus = EventBus()
    return _default_bus
