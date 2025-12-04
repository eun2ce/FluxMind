from __future__ import annotations

from abc import ABC
from datetime import datetime
from typing import Protocol, Sequence

from fluxmind.domain_core import (
    Conversation,
    ConversationId,
    Message,
    MessageRole,
    new_conversation,
)


class ConversationRepository(Protocol):
    async def get(self, conversation_id: ConversationId) -> Conversation | None: ...

    async def save(self, conversation: Conversation) -> None: ...

    async def list_messages(
        self,
        conversation_id: ConversationId,
        limit: int | None = None,
    ) -> Sequence[Message]: ...

    async def list_old_unarchived(
        self,
        older_than: datetime,
        *,
        limit: int = 100,
    ) -> Sequence[Conversation]: ...


class ConversationService(ABC):
    def __init__(self, repository: ConversationRepository) -> None:
        self._repository = repository

    async def create_conversation(
        self,
        initial_user_message: str | None = None,
    ) -> Conversation:
        conv = new_conversation(initial_user_message)
        await self._repository.save(conv)
        return conv

    async def add_user_message(
        self,
        conversation_id: ConversationId,
        content: str,
    ) -> Message:
        conv = await self._require_conversation(conversation_id)
        message = conv.add_message(MessageRole.USER, content)
        await self._repository.save(conv)
        return message

    async def add_assistant_message(
        self,
        conversation_id: ConversationId,
        content: str,
    ) -> Message:
        conv = await self._require_conversation(conversation_id)
        message = conv.add_message(MessageRole.ASSISTANT, content)
        await self._repository.save(conv)
        return message

    async def get_conversation(
        self,
        conversation_id: ConversationId,
    ) -> Conversation:
        return await self._require_conversation(conversation_id)

    async def list_messages(
        self,
        conversation_id: ConversationId,
        limit: int | None = None,
    ) -> Sequence[Message]:
        return await self._repository.list_messages(
            conversation_id=conversation_id,
            limit=limit,
        )

    async def archive_conversation(
        self,
        conversation_id: ConversationId,
    ) -> Conversation:
        conv = await self._require_conversation(conversation_id)
        conv.archive()
        await self._repository.save(conv)
        return conv

    async def list_old_unarchived(
        self,
        older_than: datetime,
        *,
        limit: int = 100,
    ) -> Sequence[Conversation]:
        return await self._repository.list_old_unarchived(
            older_than=older_than,
            limit=limit,
        )

    async def _require_conversation(
        self,
        conversation_id: ConversationId,
    ) -> Conversation:
        conv = await self._repository.get(conversation_id)
        if conv is None:
            raise LookupError(f"Conversation not found: {conversation_id}")
        return conv
