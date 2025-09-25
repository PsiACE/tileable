"""Inspect tile execution details using ``return_context`` and event recording."""

from __future__ import annotations

from tileable import EventBus, Tile, TilePayload, TileRegistry, TileResult, invoke_tile


class AuditPayload(TilePayload):
    user: str


class AuditResult(TileResult):
    summary: str


class AuditTile(Tile[AuditPayload, AuditResult]):
    """Tile that records execution details in the context and emits debug events."""

    name = "audit"

    def execute(self, payload: AuditPayload) -> AuditResult:
        self.context.set_service("user", payload.user)
        count = self.context.state.setdefault("invocations", 0) + 1
        self.context.state["invocations"] = count
        self.context.emit("tile.debug", tile=self.name, user=payload.user, count=count)
        return AuditResult(summary=f"processed:{payload.user}")


def inspect_context(
    user: str = "Inspector",
) -> tuple[AuditResult, dict[str, object], dict[str, object], list[dict[str, object]]]:
    """Run :class:`AuditTile` and surface context/services/events for inspection."""

    registry = TileRegistry()
    registry.register(AuditTile)

    bus = EventBus()
    state: dict[str, object] = {"invocations": 0}

    with bus.record("tile.debug") as recorder:
        result, ctx = invoke_tile(
            "audit",
            AuditPayload(user=user),
            registry=registry,
            event_bus=bus,
            state=state,
            return_context=True,
        )

    services_snapshot = dict(ctx.services)
    state_snapshot = dict(ctx.state)
    debug_events = recorder.payloads()
    return result, services_snapshot, state_snapshot, debug_events


def main() -> None:
    result, services, state, events = inspect_context()
    print(result.summary)
    print(services)
    print(state)
    print(events)


if __name__ == "__main__":
    main()
