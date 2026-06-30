"""add_ticket_participants

Revision ID: 2c05fe572e50
Revises: 8d8bbb8b421e
Create Date: 2026-06-30 20:03:18.900746

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2c05fe572e50'
down_revision: Union[str, None] = '8d8bbb8b421e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ticket_participants',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('ticket_id', sa.UUID(), nullable=True),
        sa.Column('employee_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ticket_participants_employee_id'), 'ticket_participants', ['employee_id'], unique=False)
    op.create_index(op.f('ix_ticket_participants_id'), 'ticket_participants', ['id'], unique=False)
    op.create_index(op.f('ix_ticket_participants_ticket_id'), 'ticket_participants', ['ticket_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ticket_participants_ticket_id'), table_name='ticket_participants')
    op.drop_index(op.f('ix_ticket_participants_id'), table_name='ticket_participants')
    op.drop_index(op.f('ix_ticket_participants_employee_id'), table_name='ticket_participants')
    op.drop_table('ticket_participants')
