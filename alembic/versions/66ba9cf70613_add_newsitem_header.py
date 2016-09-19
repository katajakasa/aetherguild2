"""Add newsitem header

Revision ID: 66ba9cf70613
Revises: c5bf69604f54
Create Date: 2016-09-19 22:59:52.187000

"""

# revision identifiers, used by Alembic.
revision = '66ba9cf70613'
down_revision = 'c5bf69604f54'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('news_item', sa.Column('header', sa.String(length=32), nullable=False))


def downgrade():
    op.drop_column('news_item', 'header')
