from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_conversation_analytics"
down_revision = "0001_initial_conversations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "conversation_analytics",
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_message_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("assistant_message_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("conversation_analytics")
