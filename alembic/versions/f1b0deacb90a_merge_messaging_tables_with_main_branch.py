"""merge messaging tables with main branch

Revision ID: f1b0deacb90a
Revises: 05dbe9f07b2f, 19966495d30e
Create Date: 2025-06-23 11:08:17.286851

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1b0deacb90a'
down_revision: Union[str, None] = ('05dbe9f07b2f', '19966495d30e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
