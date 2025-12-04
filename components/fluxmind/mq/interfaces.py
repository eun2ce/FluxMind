from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Callable
from typing import Protocol, TypeVar

from fluxmind.domain_core import BaseEvent

E = TypeVar("E", bound=BaseEvent)


class EventPublisher(Protocol):
    async def publish(self, topic: str, event: BaseEvent, *, partition_key: str | None = None) -> None: ...


class EventSubscriber(ABC):
    @abstractmethod
    async def iterate(
        self,
        topic: str,
    ) -> AsyncIterator[BaseEvent]: ...

    async def consume(
        self,
        topic: str,
        handler: Callable[[BaseEvent], None | object | BaseException],
    ) -> None:
        async for event in self.iterate(topic):
            handler(event)
