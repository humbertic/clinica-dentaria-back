"""add table marcacoes

Revision ID: b61baf906ba0
Revises: 70b19f7fddaf
Create Date: 2025-05-20 07:50:59.367097

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b61baf906ba0'
down_revision: Union[str, None] = '70b19f7fddaf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
