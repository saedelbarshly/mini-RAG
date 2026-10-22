"""rename primary keys to id

Revision ID: 6e09513fea38
Revises: edd11ce611ea
Create Date: 2026-10-22 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '6e09513fea38'
down_revision: Union[str, Sequence[str], None] = 'edd11ce611ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Postgres keeps primary key and foreign key constraints attached on rename,
# so the constraints referencing these columns follow automatically.
RENAMES = (
    ('projects', 'project_id'),
    ('assets', 'asset_id'),
    ('chunks', 'chunk_id'),
)


def upgrade() -> None:
    """Upgrade schema."""
    for table, old_name in RENAMES:
        op.alter_column(table, old_name, new_column_name='id')


def downgrade() -> None:
    """Downgrade schema."""
    for table, old_name in RENAMES:
        op.alter_column(table, 'id', new_column_name=old_name)
