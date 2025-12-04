from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import datetime
from enum import Enum
from typing import Type
from uuid import UUID

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fluxmind.domain_core import BaseEvent

from .interfaces import EventPublisher, EventSubscriber


def _json_default(obj: object) -> str:
    """
    중앙 집중 JSON 직렬화 규칙.

    - UUID      → str
    - datetime  → ISO 문자열
    - Enum      → value
    나머지는 일단 str()로 강제 직렬화한다.
    """
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    return str(obj)


class KafkaEventPublisher(EventPublisher):
    def __init__(self, bootstrap_servers: str) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._producer: AIOKafkaProducer | None = None
        self._started: bool = False

    async def _ensure_started(self) -> None:
        if self._producer is None:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self._bootstrap_servers,
                # 이벤트(dataclass)를 그대로 넘기되,
                # json.dumps(default=_json_default)로 UUID/datetime/Enum 등을 문자열로 변환한다.
                value_serializer=lambda v: json.dumps(v, default=_json_default).encode("utf-8"),
            )
        if not self._started:
            await self._producer.start()
            self._started = True

    async def stop(self) -> None:
        if self._producer is not None and self._started:
            await self._producer.stop()
            self._started = False

    async def publish(self, topic: str, event: BaseEvent, *, partition_key: str | None = None) -> None:
        await self._ensure_started()
        assert self._producer is not None
        payload = {
            "event_type": event.event_type,
            "data": event.__dict__,
        }
        if partition_key:
            await self._producer.send_and_wait(topic, payload, key=partition_key.encode("utf-8"))
        else:
            await self._producer.send_and_wait(topic, payload)


class KafkaEventSubscriber(EventSubscriber):
    def __init__(self, bootstrap_servers: str, group_id: str, event_types: dict[str, Type[BaseEvent]]) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._group_id = group_id
        self._event_types = event_types

    async def iterate(self, topic: str) -> AsyncIterator[BaseEvent]:
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )
        await consumer.start()
        try:
            async for msg in consumer:
                payload = msg.value
                event_type = payload.get("event_type")
                data = payload.get("data", {})
                cls = self._event_types.get(event_type)
                if cls is None:
                    continue
                yield cls(**data)
        finally:
            await consumer.stop()
