"""add updated_at server default

Revision ID: edd11ce611ea
Revises: 7950e2f955f8
Create Date: 2026-10-22 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'edd11ce611ea'
down_revision: Union[str, Sequence[str], None] = '7950e2f955f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLES = ('projects', 'assets', 'chunks')


def upgrade() -> None:
    """Upgrade schema."""
    for table in TABLES:
        op.alter_column(
            table,
            'updated_at',
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
            server_default=sa.text('now()'),
        )


def downgrade() -> None:
    """Downgrade schema."""
    for table in TABLES:
        op.alter_column(
            table,
            'updated_at',
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
            server_default=None,
        )
