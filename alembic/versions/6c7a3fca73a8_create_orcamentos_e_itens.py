"""create orcamentos e itens

Revision ID: 6c7a3fca73a8
Revises: d1d03c0fc4b3
Create Date: 2025-05-16 23:01:58.241091

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6c7a3fca73a8'
down_revision: Union[str, None] = 'd1d03c0fc4b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
