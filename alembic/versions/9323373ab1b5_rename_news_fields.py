"""Rename news fields

Revision ID: 9323373ab1b5
Revises: a707d1357e51
Create Date: 2016-09-10 20:00:53.168000

"""

# revision identifiers, used by Alembic.
revision = '9323373ab1b5'
down_revision = 'a707d1357e51'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


def upgrade():
    op.add_column('news_item', sa.Column('message', sa.Text(), nullable=False))
    op.add_column('news_item', sa.Column('nickname', sa.String(length=32), nullable=False))
    op.drop_column('news_item', 'alias')
    op.drop_column('news_item', 'post')


def downgrade():
    op.add_column('news_item', sa.Column('post', mysql.TEXT(), nullable=False))
    op.add_column('news_item', sa.Column('alias', mysql.VARCHAR(length=32), nullable=False))
    op.drop_column('news_item', 'nickname')
    op.drop_column('news_item', 'message')
