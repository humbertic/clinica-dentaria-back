"""dentes e faces

Revision ID: d3203d61cf92
Revises: b33f2d423686
Create Date: 2025-05-15 19:54:09.050433

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3203d61cf92'
down_revision: Union[str, None] = 'b33f2d423686'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "Dentes",
        sa.Column("id", sa.SmallInteger, primary_key=True),
        sa.Column("codigo_fdi", sa.String(2), nullable=False, unique=True),
        sa.Column("tipo", sa.String(10), nullable=False),
        sa.Column("arcada", sa.String(10), nullable=False),
        sa.Column("quadrante", sa.SmallInteger, nullable=False),
        sa.Column("posicao", sa.SmallInteger, nullable=False),
    )

    op.create_table(
        "Faces",
        sa.Column("id", sa.String(1), primary_key=True),
        sa.Column("descricao", sa.String(20), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("Faces")
    op.drop_table("Dentes")


