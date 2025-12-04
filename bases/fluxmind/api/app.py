from __future__ import annotations

from fastapi import Depends, FastAPI
from fluxmind.conversation import ConversationService
from fluxmind.domain_core import MessageReceivedEvent, MessageRole
from fluxmind.mq import EventPublisher
from fluxmind.platform import get_settings
from pydantic import BaseModel

from .deps import get_conversation_service, get_event_publisher


class CreateConversationRequest(BaseModel):
    initial_message: str | None = None


class CreateConversationResponse(BaseModel):
    conversation_id: str


app = FastAPI(title="FluxMind API")


@app.get("/healthz")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/conversations", status_code=201, response_model=CreateConversationResponse)
async def create_conversation(
    payload: CreateConversationRequest,
    conversation_service: ConversationService = Depends(get_conversation_service),
    event_publisher: EventPublisher = Depends(get_event_publisher),
) -> CreateConversationResponse:
    conv = await conversation_service.create_conversation(
        initial_user_message=payload.initial_message,
    )

    if payload.initial_message:
        user_msg = conv.messages[-1]
        event = MessageReceivedEvent(
            conversation_id=user_msg.conversation_id,
            message_id=user_msg.id,
            role=MessageRole.USER,
            content=user_msg.content,
        )
        settings = get_settings()
        await event_publisher.publish(
            topic=settings.mq_topic_conversation_events,
            event=event,
            partition_key=str(user_msg.conversation_id),
        )

    return CreateConversationResponse(conversation_id=str(conv.id))
