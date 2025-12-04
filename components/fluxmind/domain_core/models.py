from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import NewType, Sequence
from uuid import UUID, uuid4

ConversationId = NewType("ConversationId", UUID)
MessageId = NewType("MessageId", UUID)


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass(slots=True, frozen=True)
class Message:
    id: MessageId
    conversation_id: ConversationId
    role: MessageRole
    content: str
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )


@dataclass(slots=True)
class Conversation:
    id: ConversationId
    messages: list[Message] = field(default_factory=list)
    is_archived: bool = False
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    def add_message(self, role: MessageRole, content: str) -> Message:
        message = Message(
            id=MessageId(uuid4()),
            conversation_id=self.id,
            role=role,
            content=content,
        )
        self.messages.append(message)
        self.touch()
        return message

    def latest_messages(self, limit: int | None = None) -> Sequence[Message]:
        if limit is None or limit >= len(self.messages):
            return tuple(self.messages)
        return tuple(self.messages[-limit:])

    def archive(self) -> None:
        self.is_archived = True
        self.touch()

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
