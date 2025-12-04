from __future__ import annotations

from uuid import uuid4

from .models import Conversation, ConversationId, MessageRole


def new_conversation(initial_user_message: str | None = None) -> Conversation:
    conv = Conversation(id=ConversationId(uuid4()))
    if initial_user_message:
        conv.add_message(MessageRole.USER, initial_user_message)
    return conv
