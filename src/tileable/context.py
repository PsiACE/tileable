"""Execution context injected into every tile instance."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from types import MappingProxyType
from typing import Any

from .events import EventBus


class TileContext:
    """Runtime context that tiles can use to interact with the system."""

    def __init__(
        self,
        *,
        event_bus: EventBus,
        services: Mapping[str, Any] | None = None,
        state: MutableMapping[str, Any] | None = None,
    ) -> None:
        self._event_bus = event_bus
        self._services: dict[str, Any] = dict(services or {})
        self._state: MutableMapping[str, Any] = state if state is not None else {}

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    @property
    def services(self) -> Mapping[str, Any]:
        """Read-only view of registered services."""

        return MappingProxyType(self._services)

    @property
    def state(self) -> MutableMapping[str, Any]:
        """Mutable state bag shared across the current invocation."""

        return self._state

    def emit(self, event: str, /, **payload: Any) -> None:
        """Emit ``event`` with ``payload`` through the event bus."""

        self._event_bus.emit(event, **payload)

    def get_service(self, name: str) -> Any:
        """Return a registered service or raise ``KeyError``."""

        try:
            return self._services[name]
        except KeyError as exc:  # pragma: no cover - defensive path
            raise KeyError(name) from exc

    def get_service_or(self, name: str, default: Any | None = None) -> Any | None:
        """Return a service if available, otherwise ``default``."""

        return self._services.get(name, default)

    def set_service(self, name: str, value: Any) -> None:
        """Register or override a service for the current invocation."""

        self._services[name] = value
