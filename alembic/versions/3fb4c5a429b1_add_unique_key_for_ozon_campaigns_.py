"""Add unique key for ozon_campaigns_products

Revision ID: 3fb4c5a429b1
Revises: 576f8097b45f
Create Date: 2024-10-04 00:33:07.354511

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3fb4c5a429b1'
down_revision: Union[str, None] = '576f8097b45f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('unique_campaign_id_product_id', 'ozon_campaigns_products', ['campaign_id', 'product_id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('unique_campaign_id_product_id', 'ozon_campaigns_products', type_='unique')
    # ### end Alembic commands ###
