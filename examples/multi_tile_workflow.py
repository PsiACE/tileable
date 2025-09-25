"""Compose multiple tiles with shared state and event recording."""

from __future__ import annotations

from collections.abc import Iterable

from tileable import EventBus, Tile, TilePayload, TilePluginManager, TileRegistry, TileResult, hookimpl, invoke_tile


class PreparePayload(TilePayload):
    topic: str


class PrepareResult(TileResult):
    topic: str


class NotifyPayload(TilePayload):
    topic: str


class NotifyResult(TileResult):
    summary: str


class PrepareTile(Tile[PreparePayload, PrepareResult]):
    name = "prepare"

    def execute(self, payload: PreparePayload) -> PrepareResult:
        log = self.context.state.setdefault("log", [])
        entry = f"prepared:{payload.topic}"
        log.append(entry)
        self.context.emit("tile.debug", tile=self.name, entry=entry)
        self.context.set_service("last_topic", payload.topic)
        return PrepareResult(topic=payload.topic)


class NotifyTile(Tile[NotifyPayload, NotifyResult]):
    name = "notify"

    def execute(self, payload: NotifyPayload) -> NotifyResult:
        log = self.context.state.setdefault("log", [])
        entry = f"notified:{payload.topic}"
        log.append(entry)
        self.context.emit("tile.debug", tile=self.name, entry=entry)
        return NotifyResult(summary=entry)


class WorkflowPlugin:
    @hookimpl
    def tile_specs(self) -> Iterable[type[Tile]]:
        yield PrepareTile
        yield NotifyTile


def run_multi_tile_workflow(topic: str = "demo") -> tuple[str, dict[str, object], list[dict[str, object]]]:
    """Run two tiles sequentially while sharing state and capturing debug events."""

    registry = TileRegistry()
    plugins = TilePluginManager()
    plugins.register(WorkflowPlugin())

    bus = EventBus()
    state: dict[str, object] = {"log": []}

    with bus.record("tile.debug") as recorder:
        prepare_result = invoke_tile(
            "prepare",
            PreparePayload(topic=topic),
            registry=registry,
            plugins=plugins,
            event_bus=bus,
            state=state,
        )
        notify_result = invoke_tile(
            "notify",
            NotifyPayload(topic=prepare_result.topic),
            registry=registry,
            plugins=plugins,
            event_bus=bus,
            state=state,
        )

    return notify_result.summary, state, recorder.payloads()


def main() -> None:
    summary, state, events = run_multi_tile_workflow()
    print(summary)
    print(state)
    print(events)


if __name__ == "__main__":
    main()
