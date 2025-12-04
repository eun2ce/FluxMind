from __future__ import annotations

from datetime import datetime
from typing import Sequence
from uuid import UUID

from fluxmind.conversation import ConversationRepository
from fluxmind.domain_core import (
    Conversation,
    ConversationId,
    Message,
    MessageId,
)
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import ConversationRow, MessageRow
from .session import AsyncSessionMaker


def _row_to_domain_conversation(row: ConversationRow, messages: Sequence[MessageRow]) -> Conversation:
    conv = Conversation(
        id=ConversationId(row.id),
        is_archived=row.is_archived,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
    for msg_row in messages:
        conv.messages.append(
            Message(
                id=MessageId(msg_row.id),
                conversation_id=ConversationId(msg_row.conversation_id),
                role=msg_row.role,
                content=msg_row.content,
                created_at=msg_row.created_at,
            ),
        )
    return conv


class SqlAlchemyConversationRepository(ConversationRepository):
    def __init__(self, session_maker: AsyncSessionMaker) -> None:
        self._session_maker = session_maker

    async def get(self, conversation_id: ConversationId) -> Conversation | None:
        async with self._session_maker() as session:
            row = await session.get(ConversationRow, UUID(str(conversation_id)))
            if row is None:
                return None

            messages = (
                (
                    await session.execute(
                        select(MessageRow).where(MessageRow.conversation_id == row.id).order_by(MessageRow.created_at)
                    )
                )
                .scalars()
                .all()
            )

            return _row_to_domain_conversation(row, messages)

    async def save(self, conversation: Conversation) -> None:
        async with self._session_maker() as session:
            await self._upsert_conversation(session, conversation)
            await session.commit()

    async def list_messages(
        self,
        conversation_id: ConversationId,
        limit: int | None = None,
    ):
        conv = await self.get(conversation_id)
        if conv is None:
            return []
        return conv.latest_messages(limit=limit)

    async def list_old_unarchived(
        self,
        older_than: datetime,
        *,
        limit: int = 100,
    ) -> Sequence[Conversation]:
        async with self._session_maker() as session:
            rows = (
                (
                    await session.execute(
                        select(ConversationRow)
                        .where(
                            ~ConversationRow.is_archived,
                            ConversationRow.updated_at < older_than,
                        )
                        .order_by(ConversationRow.updated_at)
                        .limit(limit)
                    )
                )
                .scalars()
                .all()
            )

            result = []
            for row in rows:
                messages = (
                    (
                        await session.execute(
                            select(MessageRow)
                            .where(MessageRow.conversation_id == row.id)
                            .order_by(MessageRow.created_at)
                        )
                    )
                    .scalars()
                    .all()
                )
                result.append(_row_to_domain_conversation(row, messages))

            return result

    async def _upsert_conversation(
        self,
        session: AsyncSession,
        conv: Conversation,
    ) -> None:
        conv_id: UUID = UUID(str(conv.id))

        row = await session.get(ConversationRow, conv_id)
        if row is None:
            row = ConversationRow(
                id=conv_id,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                is_archived=conv.is_archived,
            )
            session.add(row)
        else:
            row.updated_at = conv.updated_at
            row.is_archived = conv.is_archived

        await session.execute(
            delete(MessageRow).where(MessageRow.conversation_id == conv_id),
        )

        for msg in conv.messages:
            msg_id: UUID = UUID(str(msg.id))
            session.add(
                MessageRow(
                    id=msg_id,
                    conversation_id=conv_id,
                    role=msg.role,
                    content=msg.content,
                    created_at=msg.created_at,
                ),
            )
