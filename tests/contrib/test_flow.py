from __future__ import annotations

from typing import Any

from tileable import EventBus, TileRegistry, invoke_tile
from tileable.contrib.flow import EventFlowPayload, Subscription, register_event_flow
from tileable.schema import TilePayload, TileResult
from tileable.tile import Tile


class FetchPayload(TilePayload):
    order_id: int


class FetchResult(TileResult):
    amount: int


class ScorePayload(TilePayload):
    order_id: int
    amount: int


class ScoreResult(TileResult):
    segment: str


class NotifyPayload(TilePayload):
    order_id: int
    segment: str


class FetchTile(Tile[FetchPayload, FetchResult]):
    name = "fetch"

    def execute(self, payload: FetchPayload) -> FetchResult:
        amount = 50 + (payload.order_id % 3) * 30
        history = self.context.state.setdefault("history", [])
        history.append({"step": "fetch", "amount": amount})
        result = FetchResult(amount=amount)
        self.context.emit(
            "flow.fetch.completed",
            tile=self.name,
            payload=payload,
            result=result,
            history=list(history),
        )
        return result


class ScoreTile(Tile[ScorePayload, ScoreResult]):
    name = "score"

    def execute(self, payload: ScorePayload) -> ScoreResult:
        segment = "vip" if payload.amount >= 90 else "standard"
        history = self.context.state.setdefault("history", [])
        history.append({"step": "score", "segment": segment})
        result = ScoreResult(segment=segment)
        self.context.emit(
            "flow.score.completed",
            tile=self.name,
            payload=payload,
            result=result,
            history=list(history),
        )
        return result


class NotifyTile(Tile[NotifyPayload, TileResult]):
    name = "notify"

    def execute(self, payload: NotifyPayload) -> TileResult:
        collector: list[dict[str, Any]] = self.context.get_service("collector")
        history = list(self.context.state.get("history", []))
        history.append({"step": "notify", "segment": payload.segment})
        collector.append({"order_id": payload.order_id, "segment": payload.segment, "history": history})
        return TileResult()


def test_event_flow_tile_routes_and_aggregates() -> None:
    registry = TileRegistry()
    registry.register(FetchTile)
    registry.register(ScoreTile)
    registry.register(NotifyTile)

    collector: list[dict[str, Any]] = []
    bus = EventBus()

    def fetch_router(event_bus: EventBus, sender: str, data: dict[str, Any]) -> None:
        payload: FetchPayload = data["payload"]
        result: FetchResult = data["result"]
        history = data.get("history", [])

        if result.amount >= 90:
            invoke_tile(
                "score",
                ScorePayload(order_id=payload.order_id, amount=result.amount),
                registry=registry,
                event_bus=event_bus,
                services={"collector": collector},
                state={"history": history},
            )
        else:
            invoke_tile(
                "notify",
                NotifyPayload(order_id=payload.order_id, segment="standard"),
                registry=registry,
                event_bus=event_bus,
                services={"collector": collector},
                state={"history": history},
            )

    def score_router(event_bus: EventBus, sender: str, data: dict[str, Any]) -> None:
        payload: ScorePayload = data["payload"]
        result: ScoreResult = data["result"]
        history = data.get("history", [])

        invoke_tile(
            "notify",
            NotifyPayload(order_id=payload.order_id, segment=result.segment),
            registry=registry,
            event_bus=event_bus,
            services={"collector": collector},
            state={"history": history},
        )

    flow_tile = register_event_flow(
        Subscription("flow.fetch.completed", fetch_router),
        Subscription("flow.score.completed", score_router),
    )

    invoke_tile(
        flow_tile,
        EventFlowPayload(
            entry_tile="fetch",
            entry_payload=FetchPayload(order_id=1),
            registry=registry,
        ),
        registry=registry,
        event_bus=bus,
        services={"collector": collector},
        state={"history": []},
    )

    assert collector
    entry = collector[0]
    assert entry["order_id"] == 1
    history_steps = [step["step"] for step in entry["history"]]
    assert "fetch" in history_steps
    if entry["segment"] == "vip":
        assert "score" in history_steps
    else:
        assert "score" not in history_steps
