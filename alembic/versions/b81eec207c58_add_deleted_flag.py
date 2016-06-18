"""Add deleted flag

Revision ID: b81eec207c58
Revises: 4becb26bb41d
Create Date: 2016-06-18 02:11:51.835000

"""

# revision identifiers, used by Alembic.
revision = 'b81eec207c58'
down_revision = '4becb26bb41d'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


def upgrade():
    op.add_column('forum_board', sa.Column('deleted', sa.Boolean(), nullable=False))
    op.add_column('forum_post', sa.Column('deleted', sa.Boolean(), nullable=False))
    op.add_column('forum_section', sa.Column('deleted', sa.Boolean(), nullable=False))
    op.add_column('forum_thread', sa.Column('deleted', sa.Boolean(), nullable=False))
    op.add_column('news_item', sa.Column('deleted', sa.Boolean(), nullable=False))
    op.add_column('user', sa.Column('deleted', sa.Boolean(), nullable=False))
    op.drop_column('user', 'active')


def downgrade():
    op.add_column('user', sa.Column('active', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False))
    op.drop_column('user', 'deleted')
    op.drop_column('news_item', 'deleted')
    op.drop_column('forum_thread', 'deleted')
    op.drop_column('forum_section', 'deleted')
    op.drop_column('forum_post', 'deleted')
    op.drop_column('forum_board', 'deleted')
