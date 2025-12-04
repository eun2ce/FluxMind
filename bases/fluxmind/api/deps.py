from __future__ import annotations

from fluxmind.conversation import ConversationService
from fluxmind.database import get_session_maker
from fluxmind.database.conversation_repository import SqlAlchemyConversationRepository
from fluxmind.mq import EventPublisher
from fluxmind.mq.kafka import KafkaEventPublisher
from fluxmind.platform import get_settings

_session_maker = get_session_maker()
_conversation_repo = SqlAlchemyConversationRepository(_session_maker)
_conversation_service = ConversationService(_conversation_repo)

_settings = get_settings()
_event_publisher: EventPublisher = KafkaEventPublisher(
    bootstrap_servers=_settings.mq_bootstrap_servers,
)


def get_conversation_service() -> ConversationService:
    return _conversation_service


def get_event_publisher() -> EventPublisher:
    return _event_publisher
