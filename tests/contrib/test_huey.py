from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from huey import MemoryHuey

from tileable import TilePayload, TilePluginManager, TileRegistry, invoke_tile
from tileable.contrib.huey import (
    HueyDispatchPayload,
    HueyDispatchTile,
    HueyPlugin,
    HueyWorkerPayload,
    HueyWorkerTile,
)
from tileable.schema import TileResult
from tileable.tile import Tile


class AddPayload(TilePayload):
    value: int


class AddResult(TileResult):
    total: int


class AddTile(Tile[AddPayload, AddResult]):
    name = "add"

    def execute(self, payload: AddPayload) -> AddResult:
        total = self.context.state.setdefault("total", 0) + payload.value
        self.context.state["total"] = total
        return AddResult(total=total)


@dataclass
class FakeDispatcher:
    calls: list[dict[str, object]]

    def enqueue(self, *, tile: str, payload: object, eta: float | None = None, queue: str | None = None) -> str:
        self.calls.append({"tile": tile, "payload": payload, "eta": eta, "queue": queue})
        return f"task-{len(self.calls)}"


def test_huey_dispatch_tile_enqueues_tasks() -> None:
    registry = TileRegistry()
    registry.register(AddTile)

    dispatcher = FakeDispatcher(calls=[])

    result = invoke_tile(
        HueyDispatchTile,
        HueyDispatchPayload(tile="add", payload=AddPayload(value=3), dispatcher=dispatcher, registry=registry),
        registry=registry,
    )

    assert result.status == "queued"
    assert result.task_id == "task-1"
    assert dispatcher.calls[0]["tile"] == "add"


def test_huey_dispatch_tile_wait_executes_inline() -> None:
    registry = TileRegistry()
    registry.register(AddTile)

    dispatcher = FakeDispatcher(calls=[])

    state: dict[str, object] = {}
    result = invoke_tile(
        HueyDispatchTile,
        HueyDispatchPayload(
            tile="add",
            payload=AddPayload(value=5),
            dispatcher=dispatcher,
            wait=True,
            registry=registry,
        ),
        registry=registry,
        state=state,
    )

    assert result.status == "completed"
    assert result.result.total == 5
    assert state["total"] == 5


def test_huey_worker_tile_executes_job() -> None:
    registry = TileRegistry()
    registry.register(AddTile)

    state: dict[str, object] = {}
    result = invoke_tile(
        HueyWorkerTile,
        HueyWorkerPayload(tile="add", payload=AddPayload(value=2), registry=registry),
        registry=registry,
        state=state,
    )

    assert result.result.total == 2


def test_huey_plugin_supplies_dispatcher() -> None:
    registry = TileRegistry()
    registry.register(AddTile)

    dispatcher = FakeDispatcher(calls=[])
    plugins = TilePluginManager()
    plugins.register(HueyPlugin(dispatcher))

    result = invoke_tile(
        HueyDispatchTile,
        HueyDispatchPayload(tile="add", payload=AddPayload(value=1), registry=registry, wait=True),
        registry=registry,
        plugins=plugins,
        state={"total": 0},
    )

    assert result.status == "completed"


def test_huey_dispatch_with_real_huey() -> None:
    pytest.importorskip("huey")

    registry = TileRegistry()
    registry.register(AddTile)

    huey = MemoryHuey(immediate=False)

    class HueyDispatcherAdapter:
        def __init__(self, huey_instance: MemoryHuey, registry: TileRegistry, state: dict[str, object]) -> None:
            self._huey = huey_instance
            self._registry = registry
            self._state = state
            self._jobs: list[Any] = []

            @self._huey.task()
            def run(tile_name: str, payload: dict[str, Any]) -> Any:
                return invoke_tile(
                    tile_name,
                    payload,
                    registry=self._registry,
                    state=self._state,
                )

            self._task = run

        def enqueue(self, *, tile: str, payload: Any, eta: float | None = None, queue: str | None = None) -> str:
            job = self._task.s(tile, payload)
            self._huey.enqueue(job)
            self._jobs.append(job)
            return job.id

        def execute_next(self) -> Any:
            job = self._jobs.pop(0)
            return huey.execute(job)

    shared_state: dict[str, object] = {"total": 0}
    adapter = HueyDispatcherAdapter(huey, registry, shared_state)
    plugins = TilePluginManager()
    plugins.register(HueyPlugin(adapter))

    result = invoke_tile(
        HueyDispatchTile,
        HueyDispatchPayload(tile="add", payload=AddPayload(value=7), registry=registry),
        registry=registry,
        plugins=plugins,
    )

    assert result.status == "queued"
    adapter.execute_next()
    assert shared_state["total"] == 7
