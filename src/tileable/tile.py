"""Tile base class that powers every piece of functionality."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import ClassVar

from .context import TileContext
from .schema import TilePayload, TileResult


class Tile[PayloadT: TilePayload, ResultT: TileResult](ABC):
    """Base class to implement custom tiles.

    Subclasses should define a unique ``name`` and implement ``execute``. When
    async support is required override ``aexecute``; otherwise the default
    implementation safely offloads the sync ``execute`` via ``asyncio.to_thread``.
    """

    name: ClassVar[str]
    description: ClassVar[str | None] = None

    def __init__(self, *, context: TileContext | None = None) -> None:
        self._context = context

    @property
    def context(self) -> TileContext:
        if self._context is None:
            msg = "Tile context is not attached. Pass `context=` when instantiating or use `invoke_tile`."
            raise RuntimeError(msg)
        return self._context

    def set_context(self, context: TileContext | None) -> None:
        """Attach or detach the runtime context."""

        self._context = context

    @abstractmethod
    def execute(self, payload: PayloadT) -> ResultT:
        """Execute the tile synchronously."""

    async def aexecute(self, payload: PayloadT) -> ResultT:
        """Execute the tile asynchronously.

        The default behavior offloads ``execute`` to a worker thread, ensuring the
        event loop never blocks. Overriding tiles can provide a native async
        implementation if needed.
        """

        return await asyncio.to_thread(self.execute, payload)
