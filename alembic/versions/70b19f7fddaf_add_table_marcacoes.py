"""add table marcacoes

Revision ID: 70b19f7fddaf
Revises: 467d8b5c07e4
Create Date: 2025-05-20 07:50:34.094221

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '70b19f7fddaf'
down_revision: Union[str, None] = '467d8b5c07e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
