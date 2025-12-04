from __future__ import annotations

import pytest
from fluxmind.conversation import ConversationRepository, ConversationService
from fluxmind.domain_core import Conversation, ConversationId, MessageReceivedEvent, MessageRole
from fluxmind.events_consumer.main import handle_message_received
from fluxmind.llm import LLMClient, LLMMessage, LLMRole
from fluxmind.mq import EventPublisher


class InMemoryConversationRepository(ConversationRepository):
    def __init__(self) -> None:
        self._store: dict[ConversationId, Conversation] = {}

    async def get(self, conversation_id: ConversationId) -> Conversation | None:
        return self._store.get(conversation_id)

    async def save(self, conversation: Conversation) -> None:
        self._store[conversation.id] = conversation

    async def list_messages(self, conversation_id: ConversationId, limit: int | None = None):
        conv = self._store.get(conversation_id)
        if conv is None:
            return []
        return conv.latest_messages(limit=limit)


class CollectingEventPublisher(EventPublisher):
    def __init__(self) -> None:
        self.published: list[tuple[str, object]] = []

    async def publish(self, topic: str, event, *, partition_key: str | None = None):
        self.published.append((topic, event))


class EchoLLMClient(LLMClient):
    async def generate(
        self, messages: list[LLMMessage], *, model: str, temperature: float | None = None, max_tokens: int | None = None
    ) -> str:
        for msg in reversed(messages):
            if msg.role == LLMRole.USER:
                return f"echo: {msg.content}"
        return "echo: (no user message)"


@pytest.mark.asyncio
async def test_message_flow_user_to_assistant():
    repo = InMemoryConversationRepository()
    service = ConversationService(repo)
    publisher = CollectingEventPublisher()
    llm = EchoLLMClient()

    conv = await service.create_conversation("hello")
    user_msg = conv.messages[-1]
    event = MessageReceivedEvent(
        conversation_id=user_msg.conversation_id,
        message_id=user_msg.id,
        role=MessageRole.USER,
        content=user_msg.content,
    )

    await handle_message_received(
        event,
        conversation_service=service,
        llm_client=llm,
        event_publisher=publisher,
    )

    updated_conv = await service.get_conversation(conv.id)
    assert len(updated_conv.messages) == 2
    assert updated_conv.messages[-1].role == MessageRole.ASSISTANT
    assert "echo: hello" == updated_conv.messages[-1].content

    assert len(publisher.published) == 1
    topic, evt = publisher.published[0]
    from fluxmind.domain_core import AssistantRespondedEvent

    assert isinstance(evt, AssistantRespondedEvent)
    assert evt.conversation_id == conv.id
    assert evt.user_message_id == user_msg.id
