from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fluxmind.analytics import AnalyticsRepository
from fluxmind.domain_core import ConversationId
from sqlalchemy import insert, select, update

from .models import ConversationAnalyticsRow
from .session import AsyncSessionMaker


class SqlAlchemyAnalyticsRepository(AnalyticsRepository):
    def __init__(self, session_maker: AsyncSessionMaker) -> None:
        self._session_maker = session_maker

    async def increment_conversation_message_count(
        self,
        conversation_id: ConversationId,
        *,
        is_assistant: bool,
        occurred_at: datetime,
    ) -> None:
        conv_id = UUID(str(conversation_id))
        async with self._session_maker() as session:
            row = (
                await session.execute(
                    select(ConversationAnalyticsRow).where(
                        ConversationAnalyticsRow.conversation_id == conv_id,
                    ),
                )
            ).scalar_one_or_none()

            if row is None:
                user_count = 0
                assistant_count = 1 if is_assistant else 0
                await session.execute(
                    insert(ConversationAnalyticsRow).values(
                        conversation_id=conv_id,
                        user_message_count=user_count,
                        assistant_message_count=assistant_count,
                        last_message_at=occurred_at,
                    ),
                )
            else:
                await session.execute(
                    update(ConversationAnalyticsRow)
                    .where(ConversationAnalyticsRow.conversation_id == conv_id)
                    .values(
                        assistant_message_count=ConversationAnalyticsRow.assistant_message_count
                        + (1 if is_assistant else 0),
                        last_message_at=occurred_at,
                    ),
                )

            await session.commit()
