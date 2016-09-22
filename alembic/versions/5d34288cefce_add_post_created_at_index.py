"""Add post.created_at index

Revision ID: 5d34288cefce
Revises: 797648a35816
Create Date: 2016-09-22 23:17:56.571000

"""

# revision identifiers, used by Alembic.
revision = '5d34288cefce'
down_revision = '797648a35816'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


def upgrade():
    op.create_index(op.f('ix_forum_post_created_at'), 'forum_post', ['created_at'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_forum_post_created_at'), table_name='forum_post')
