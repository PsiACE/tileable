"""Event-driven orchestration helpers as tiles."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from tileable import EventBus, Tile, TilePayload, TilePluginManager, TileRegistry, TileResult, invoke_tile

RouteFn = Callable[[EventBus, str, dict[str, Any]], None]


class EventFlowPayload(TilePayload):
    """Payload for :class:`EventFlowTile`."""

    entry_tile: str
    entry_payload: Any
    registry: TileRegistry
    plugins: TilePluginManager | None = None
    services: dict[str, Any] | None = None


@dataclass
class Subscription:
    """Represents a subscription mapping an event to a handler."""

    event: str
    handler: RouteFn


def register_event_flow(*subscriptions: Subscription, name: str = "event-flow") -> type[Tile]:
    """Create a flow tile that routes based on emitted events."""

    tile_name = name

    class EventFlowTile(Tile[EventFlowPayload, TileResult]):
        name = tile_name

        def execute(self, payload: EventFlowPayload) -> TileResult:
            bus = self.context.event_bus
            registry = payload.registry
            plugins = payload.plugins
            services = payload.services

            unsubscribers = []
            try:
                for subscription in subscriptions:
                    event_name = subscription.event
                    handler = subscription.handler
                    unsubscribers.append(
                        bus.subscribe(
                            event_name,
                            lambda sender, handler=handler, **data: handler(bus, sender, data),
                        )
                    )

                invoke_tile(
                    payload.entry_tile,
                    payload.entry_payload,
                    registry=registry,
                    plugins=plugins,
                    event_bus=bus,
                    services=services,
                )
            finally:
                while unsubscribers:
                    unsubscribers.pop()()

            return TileResult()

    return EventFlowTile


__all__ = [
    "EventFlowPayload",
    "Subscription",
    "register_event_flow",
]
