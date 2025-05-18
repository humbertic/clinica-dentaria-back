"""create orcamentos e itens

Revision ID: 377a886cd1c9
Revises: dc6507dc9b35
Create Date: 2025-05-16 23:07:21.026780

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '377a886cd1c9'
down_revision: Union[str, None] = 'dc6507dc9b35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
