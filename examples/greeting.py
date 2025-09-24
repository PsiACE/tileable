"""Greeting tile example demonstrating the Tileable workflow."""

from __future__ import annotations

from collections.abc import Iterable

from tileable import (
    EventBus,
    Tile,
    TileContext,
    TilePayload,
    TilePluginManager,
    TileRegistry,
    TileResult,
    hookimpl,
    invoke_tile,
)


class GreetingPayload(TilePayload):
    message: str


class GreetingResult(TileResult):
    response: str


class GreetingTile(Tile[GreetingPayload, GreetingResult]):
    """Tile that returns a friendly greeting, emitting debug events."""

    name = "greeting"
    description = "Return a friendly greeting with a prefix."

    def execute(self, payload: GreetingPayload) -> GreetingResult:
        prefix = self.context.get_service_or("prefix", "Hello")
        text = f"{prefix}, {payload.message}!"
        self.context.emit("tile.debug", tile=self.name, message=payload.message)
        return GreetingResult(response=text)


class GreetingPlugin:
    """Plugin that contributes :class:`GreetingTile` and seeds context state."""

    @hookimpl
    def tile_specs(self) -> Iterable[type[Tile[GreetingPayload, GreetingResult]]]:
        yield GreetingTile

    @hookimpl
    def tile_startup(self, ctx: TileContext, tile: Tile[GreetingPayload, GreetingResult]) -> None:
        ctx.state.setdefault("runs", 0)
        ctx.state["runs"] += 1
        ctx.set_service("prefix", ctx.get_service_or("prefix", "Hi"))


def run_greeting(*, prefix: str = "Hi", name: str = "Tileable") -> GreetingResult:
    """Execute :class:`GreetingTile` using a standalone registry."""

    registry = TileRegistry()
    registry.register(GreetingTile)
    return invoke_tile(
        "greeting",
        GreetingPayload(message=name),
        registry=registry,
        services={"prefix": prefix},
    )


def showcase(*, message: str = "Tileable") -> tuple[GreetingResult, list[dict[str, object]], dict[str, object]]:
    """Run the plugin-driven demo used in the docs and README."""

    registry = TileRegistry()
    plugins = TilePluginManager()
    plugins.register(GreetingPlugin())

    bus = EventBus()
    debug_events: list[dict[str, object]] = []
    bus.subscribe("tile.debug", lambda sender, **payload: debug_events.append(payload))

    state: dict[str, object] = {"runs": 0}
    result = invoke_tile(
        "greeting",
        GreetingPayload(message=message),
        registry=registry,
        plugins=plugins,
        event_bus=bus,
        state=state,
    )
    return result, debug_events, state


def main() -> None:
    """Execute the greeting showcase and print observable side effects."""

    result, debug_events, state = showcase()

    for payload in debug_events:
        print(f"[debug] {payload}")

    print(result.response)
    print(f"runs={state.get('runs')}")


if __name__ == "__main__":
    main()
