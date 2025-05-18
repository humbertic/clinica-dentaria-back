"""create orcamentos e itens

Revision ID: dc6507dc9b35
Revises: 6c7a3fca73a8
Create Date: 2025-05-16 23:03:06.703758

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dc6507dc9b35'
down_revision: Union[str, None] = '6c7a3fca73a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
