from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from fluxmind.conversation import ConversationService
from fluxmind.database import get_session_maker
from fluxmind.database.conversation_repository import SqlAlchemyConversationRepository
from fluxmind.domain_core import ConversationArchivedEvent
from fluxmind.mq import EventPublisher
from fluxmind.mq.kafka import KafkaEventPublisher
from fluxmind.platform import get_settings


async def archive_old_conversations(
    conversation_service: ConversationService,
    event_publisher: EventPublisher,
    *,
    older_than: datetime,
    topic: str,
) -> int:
    old_convs = await conversation_service.list_old_unarchived(older_than, limit=100)

    archived_count = 0
    for conv in old_convs:
        archived = await conversation_service.archive_conversation(conv.id)
        event = ConversationArchivedEvent(conversation_id=archived.id)
        await event_publisher.publish(
            topic=topic,
            event=event,
            partition_key=str(archived.id),
        )
        archived_count += 1

    return archived_count


async def run_worker_loop(
    conversation_service: ConversationService,
    event_publisher: EventPublisher,
    *,
    archive_interval_seconds: int,
    archive_older_than_days: int,
    topic: str,
) -> None:
    while True:
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=archive_older_than_days)
            count = await archive_old_conversations(
                conversation_service=conversation_service,
                event_publisher=event_publisher,
                older_than=cutoff,
                topic=topic,
            )
            if count > 0:
                print(f"Archived {count} conversations older than {archive_older_than_days} days")
        except Exception as e:
            print(f"Error in archive job: {e}")

        await asyncio.sleep(archive_interval_seconds)


async def _main_async() -> None:
    settings = get_settings()

    session_maker = get_session_maker()
    conversation_repo = SqlAlchemyConversationRepository(session_maker)
    conversation_service = ConversationService(conversation_repo)

    event_publisher: EventPublisher = KafkaEventPublisher(
        bootstrap_servers=settings.mq_bootstrap_servers,
    )

    await run_worker_loop(
        conversation_service=conversation_service,
        event_publisher=event_publisher,
        archive_interval_seconds=settings.worker_archive_interval_seconds,
        archive_older_than_days=settings.worker_archive_older_than_days,
        topic=settings.mq_topic_conversation_events,
    )


def main() -> None:
    asyncio.run(_main_async())


if __name__ == "__main__":
    main()
