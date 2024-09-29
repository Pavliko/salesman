"""Add last_message_id to users table

Revision ID: a4dd89f749c6
Revises: 7725043b17d6
Create Date: 2024-09-26 17:37:15.670907

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4dd89f749c6'
down_revision: Union[str, None] = '7725043b17d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('users',
        sa.Column('last_message_id', sa.BigInteger(), nullable=True)
    )

def downgrade():
    op.drop_column('users', 'last_message_id')