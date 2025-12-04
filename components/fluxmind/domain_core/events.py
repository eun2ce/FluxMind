from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import UUID, uuid4

from .models import ConversationId, MessageId, MessageRole


@dataclass(slots=True, frozen=True, kw_only=True)
class BaseEvent:
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        return self.__class__.__name__


@dataclass(slots=True, frozen=True, kw_only=True)
class MessageReceivedEvent(BaseEvent):
    conversation_id: ConversationId
    message_id: MessageId
    role: MessageRole
    content: str


@dataclass(slots=True, frozen=True, kw_only=True)
class AssistantRespondedEvent(BaseEvent):
    conversation_id: ConversationId
    user_message_id: MessageId
    assistant_message_id: MessageId
    content: str


@dataclass(slots=True, frozen=True, kw_only=True)
class ConversationArchivedEvent(BaseEvent):
    conversation_id: ConversationId


@dataclass(slots=True, frozen=True, kw_only=True)
class MessageFlaggedEvent(BaseEvent):
    conversation_id: ConversationId
    message_id: MessageId
    reason: str
