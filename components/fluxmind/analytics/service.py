from __future__ import annotations

from abc import ABC
from datetime import datetime
from typing import Protocol

from fluxmind.domain_core import AssistantRespondedEvent, ConversationId


class AnalyticsRepository(Protocol):
    async def increment_conversation_message_count(
        self,
        conversation_id: ConversationId,
        *,
        is_assistant: bool,
        occurred_at: datetime,
    ) -> None: ...


class AnalyticsService(ABC):
    def __init__(self, repository: AnalyticsRepository) -> None:
        self._repository = repository

    async def handle_assistant_responded(
        self,
        event: AssistantRespondedEvent,
    ) -> None:
        await self._repository.increment_conversation_message_count(
            conversation_id=event.conversation_id,
            is_assistant=True,
            occurred_at=event.occurred_at,
        )
