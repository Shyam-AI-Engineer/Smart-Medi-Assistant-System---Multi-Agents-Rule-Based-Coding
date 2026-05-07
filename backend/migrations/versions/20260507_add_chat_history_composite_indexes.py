"""add chat_history composite indexes

Revision ID: a1b2c3d4e5f6
Revises: 7eecc298c28d
Create Date: 2026-05-07 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '7eecc298c28d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Covers: filter(patient_id=...).order_by(created_at.desc())
    # Used by: chat history listing, doctor patient view, chat_service.get_history
    op.create_index(
        'ix_chat_history_patient_created',
        'chat_history',
        ['patient_id', 'created_at'],
    )
    # Covers: filter(created_at >= cutoff).group_by(agent_used)
    # Used by: admin analytics (daily metrics, agent distribution)
    op.create_index(
        'ix_chat_history_created_agent',
        'chat_history',
        ['created_at', 'agent_used'],
    )


def downgrade() -> None:
    op.drop_index('ix_chat_history_created_agent', table_name='chat_history')
    op.drop_index('ix_chat_history_patient_created', table_name='chat_history')
