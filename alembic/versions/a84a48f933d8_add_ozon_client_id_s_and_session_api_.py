"""Add ozon client id's and session API token to users table

Revision ID: a84a48f933d8
Revises: a4dd89f749c6
Create Date: 2024-09-29 17:11:47.201767

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a84a48f933d8'
down_revision: Union[str, None] = 'a4dd89f749c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('ozon_seller_client_id', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('ozon_performance_client_id', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('ozon_performance_session_token', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'ozon_seller_client_id')
    op.drop_column('users', 'ozon_performance_client_id')
    op.drop_column('users', 'ozon_performance_session_token')
