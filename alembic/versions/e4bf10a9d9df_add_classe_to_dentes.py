"""add classe to Dentes

Revision ID: e4bf10a9d9df
Revises: d3203d61cf92
Create Date: 2025-05-15 20:23:42.470013

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column, case 


# revision identifiers, used by Alembic.
revision: str = 'e4bf10a9d9df'
down_revision: Union[str, None] = 'd3203d61cf92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) acrescenta coluna opcional
    op.add_column("Dentes", sa.Column("classe", sa.String(10)))

    # 2) tabela virtual p/ update
    dentes = table(
        "Dentes",
        column("posicao", sa.SmallInteger),
        column("classe", sa.String),
    )

    # 3) back-fill usando sa.case() correcto
    stmt = dentes.update().values(
        classe=case(
            (dentes.c.posicao.in_([1, 2]), "incisivo"),
            (dentes.c.posicao == 3,        "canino"),
            (dentes.c.posicao.in_([4, 5]), "premolar"),
            else_="molar",
        )
    )
    op.execute(stmt)

    # 4) NOT NULL + CHECK constraint
    op.alter_column("Dentes", "classe", nullable=False)
    op.create_check_constraint(
        "ck_dentes_classe",
        "Dentes",
        "classe in ('incisivo','canino','premolar','molar')",
    )

def downgrade():
    op.drop_constraint("ck_dentes_classe", "Dentes", type_="check")
    op.drop_column("Dentes", "classe")