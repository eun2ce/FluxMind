from __future__ import annotations

import asyncio

from fluxmind.analytics import AnalyticsService
from fluxmind.conversation import ConversationService
from fluxmind.database import get_session_maker
from fluxmind.database.analytics_repository import SqlAlchemyAnalyticsRepository
from fluxmind.database.conversation_repository import SqlAlchemyConversationRepository
from fluxmind.domain_core import (
    AssistantRespondedEvent,
    MessageReceivedEvent,
)
from fluxmind.llm import LLMClient, LLMMessage, LLMRole
from fluxmind.llm.ollama_client import OllamaClient
from fluxmind.mq import EventPublisher, EventSubscriber
from fluxmind.mq.kafka import KafkaEventPublisher, KafkaEventSubscriber
from fluxmind.platform import get_settings


async def handle_message_received(
    event: MessageReceivedEvent,
    conversation_service: ConversationService,
    llm_client: LLMClient,
    event_publisher: EventPublisher,
) -> None:
    conv = await conversation_service.get_conversation(event.conversation_id)
    history = [
        LLMMessage(
            role=LLMRole(msg.role.value),
            content=msg.content,
        )
        for msg in conv.latest_messages()
    ]

    reply = await llm_client.generate(
        history,
        model=get_settings().ollama_model,
    )

    assistant_msg = await conversation_service.add_assistant_message(
        conversation_id=event.conversation_id,
        content=reply,
    )

    responded = AssistantRespondedEvent(
        conversation_id=assistant_msg.conversation_id,
        user_message_id=event.message_id,
        assistant_message_id=assistant_msg.id,
        content=assistant_msg.content,
    )
    settings = get_settings()
    await event_publisher.publish(
        topic=settings.mq_topic_conversation_events,
        event=responded,
        partition_key=str(assistant_msg.conversation_id),
    )


async def run_loop(
    subscriber: EventSubscriber,
    conversation_service: ConversationService,
    llm_client: LLMClient,
    event_publisher: EventPublisher,
    analytics_service: AnalyticsService,
    topic: str,
) -> None:
    async for raw_event in subscriber.iterate(topic=topic):
        if isinstance(raw_event, MessageReceivedEvent):
            await handle_message_received(
                raw_event,
                conversation_service=conversation_service,
                llm_client=llm_client,
                event_publisher=event_publisher,
            )
        elif isinstance(raw_event, AssistantRespondedEvent):
            await analytics_service.handle_assistant_responded(raw_event)


async def _main_async() -> None:
    settings = get_settings()

    session_maker = get_session_maker()
    conversation_repo = SqlAlchemyConversationRepository(session_maker)
    conversation_service = ConversationService(conversation_repo)
    analytics_repo = SqlAlchemyAnalyticsRepository(session_maker)
    analytics_service = AnalyticsService(analytics_repo)

    llm_client: LLMClient = OllamaClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
    )

    event_publisher: EventPublisher = KafkaEventPublisher(
        bootstrap_servers=settings.mq_bootstrap_servers,
    )
    subscriber: EventSubscriber = KafkaEventSubscriber(
        bootstrap_servers=settings.mq_bootstrap_servers,
        group_id=settings.mq_group_id_events_consumer,
        event_types={
            "MessageReceivedEvent": MessageReceivedEvent,
            "AssistantRespondedEvent": AssistantRespondedEvent,
        },
    )

    await run_loop(
        subscriber=subscriber,
        conversation_service=conversation_service,
        llm_client=llm_client,
        event_publisher=event_publisher,
        analytics_service=analytics_service,
        topic=settings.mq_topic_conversation_events,
    )


def main() -> None:
    asyncio.run(_main_async())


if __name__ == "__main__":
    main()
