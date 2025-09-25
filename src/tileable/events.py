"""Event bus abstraction built on top of :mod:`blinker`."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from types import TracebackType
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


@dataclass(frozen=True)
class CapturedEvent:
    """Structured representation of an emitted event."""

    name: str
    payload: dict[str, Any]
    sender: Any | None = None


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

    def record(self, *events: str | Iterable[str], include_sender: bool = False) -> EventRecorder:
        """Capture emissions for ``events`` inside a context manager.

        When ``events`` is omitted the recorder listens to
        :data:`STANDARD_EVENTS`. The returned object exposes captured
        payloads for assertions and debugging.
        """

        names = _normalize_event_names(events)
        return EventRecorder(self, names, include_sender=include_sender)


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


def set_event_bus(bus: EventBus) -> None:
    global _default_bus
    _default_bus = bus


def reset_event_bus() -> None:
    set_event_bus(EventBus())


class EventRecorder:
    """Context manager that records events emitted by :class:`EventBus`."""

    def __init__(self, bus: EventBus, events: Iterable[str], *, include_sender: bool) -> None:
        event_names = tuple(dict.fromkeys(events))
        if not event_names:
            msg = "EventRecorder requires at least one event name"
            raise ValueError(msg)

        self._bus = bus
        self._event_names = event_names
        self._include_sender = include_sender
        self._records: list[CapturedEvent] = []
        self._subscriptions: list[Callable[[], None]] = []

    def __enter__(self) -> EventRecorder:
        for name in self._event_names:
            handler = self._create_handler(name)
            unsubscribe = self._bus.subscribe(name, handler, weak=False)
            self._subscriptions.append(unsubscribe)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        while self._subscriptions:
            unsubscribe = self._subscriptions.pop()
            unsubscribe()

    def __iter__(self) -> Iterator[CapturedEvent]:
        return iter(self._records)

    def __len__(self) -> int:
        return len(self._records)

    @property
    def events(self) -> tuple[str, ...]:
        """Names of the events being recorded."""

        return self._event_names

    def records(self) -> list[CapturedEvent]:
        """Return captured events in chronological order."""

        return list(self._records)

    def payloads(self, name: str | None = None) -> list[dict[str, Any]]:
        """Return recorded payloads.

        When ``name`` is provided only events matching the name are
        returned. Copies of the payload dictionaries are produced so callers
        can mutate them freely.
        """

        entries = self._records if name is None else [record for record in self._records if record.name == name]
        return [record.payload.copy() for record in entries]

    def last(self, name: str | None = None) -> CapturedEvent | None:
        """Return the most recent captured event, optionally filtered by name."""

        if name is None:
            return self._records[-1] if self._records else None
        for record in reversed(self._records):
            if record.name == name:
                return record
        return None

    def clear(self) -> None:
        """Drop any previously captured events."""

        self._records.clear()

    def _create_handler(self, name: str) -> Callable[..., None]:
        def handler(sender: Any, **payload: Any) -> None:
            captured = CapturedEvent(name=name, payload=dict(payload), sender=sender if self._include_sender else None)
            self._records.append(captured)

        return handler


def _normalize_event_names(events: tuple[str | Iterable[str], ...]) -> tuple[str, ...]:
    if not events:
        return STANDARD_EVENTS

    collected: list[str] = []
    for entry in events:
        if isinstance(entry, str):
            collected.append(entry)
            continue
        for candidate in entry:
            if not isinstance(candidate, str):
                msg = "Event names must be strings"
                raise TypeError(msg)
            collected.append(candidate)

    if not collected:
        return STANDARD_EVENTS

    # Preserve order while removing duplicates
    return tuple(dict.fromkeys(collected))
