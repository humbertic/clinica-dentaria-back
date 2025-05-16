"""add requer_dente to Artigos

Revision ID: d1d03c0fc4b3
Revises: e4bf10a9d9df
Create Date: 2025-05-15 20:58:02.185158

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1d03c0fc4b3'
down_revision: Union[str, None] = 'e4bf10a9d9df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) adicionar com default=False e permitir null temporariamente
    op.add_column("Artigos", sa.Column("requer_dente", sa.Boolean, server_default=sa.false()))
    op.add_column("Artigos", sa.Column("requer_face",  sa.Boolean, server_default=sa.false()))

    # 2) tornar NOT NULL e remover server_default se quiseres
    op.alter_column("Artigos", "requer_dente", nullable=False, server_default=None)
    op.alter_column("Artigos", "requer_face",  nullable=False, server_default=None)

def downgrade():
    op.drop_column("Artigos", "requer_face")
    op.drop_column("Artigos", "requer_dente")

