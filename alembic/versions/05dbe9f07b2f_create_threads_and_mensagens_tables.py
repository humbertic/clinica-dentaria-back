"""Create threads and mensagens tables

Revision ID: 05dbe9f07b2f
Revises: 42dd891b1324
Create Date: 2025-06-23 10:53:21.875670

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05dbe9f07b2f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('Threads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('clinica_id', sa.Integer(), nullable=False),
        sa.Column('participante_a_id', sa.Integer(), nullable=True),
        sa.Column('participante_b_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['clinica_id'], ['Clinica.id'], ),
        sa.ForeignKeyConstraint(['participante_a_id'], ['Utilizador.id'], ),
        sa.ForeignKeyConstraint(['participante_b_id'], ['Utilizador.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index
    op.create_index('ix_threads_pair_clinica', 'Threads', 
                    ['clinica_id', 'participante_a_id', 'participante_b_id'], 
                    unique=True)
    
    # Create Mensagens table
    op.create_table('Mensagens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('clinica_id', sa.Integer(), nullable=False),
        sa.Column('thread_id', sa.Integer(), nullable=True),
        sa.Column('remetente_id', sa.Integer(), nullable=False),
        sa.Column('texto', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('lida', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['clinica_id'], ['Clinica.id'], ),
        sa.ForeignKeyConstraint(['remetente_id'], ['Utilizador.id'], ),
        sa.ForeignKeyConstraint(['thread_id'], ['Threads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )



def downgrade() -> None:
    """Downgrade schema."""
     # Drop tables in correct order (child table first)
    op.drop_table('Mensagens')
    op.drop_table('Threads')
