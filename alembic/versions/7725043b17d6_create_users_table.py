"""Create users table

Revision ID: 7725043b17d6
Revises: 
Create Date: 2024-09-23 18:39:50.516680

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func


# revision identifiers, used by Alembic.
revision: str = '7725043b17d6'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('telegram_id', sa.BigInteger, nullable=False),
        sa.Column('telegram_name', sa.String(length=255), nullable=True),
        sa.Column('ozon_seller_token', sa.String(length=255), nullable=True),
        sa.Column('is_ozon_seller_token_valid', sa.Boolean, nullable=False, default=False),
        sa.Column('ozon_performance_token', sa.String(length=255), nullable=True),
        sa.Column('is_performance_token_valid', sa.Boolean, nullable=False, default=False),
        sa.Column('current_state', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=func.now(), onupdate=func.now()),
        sa.Column('deleted', sa.Boolean, nullable=False, default=False)
    )


def downgrade() -> None:
    op.drop_table('users')
