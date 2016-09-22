"""Add thread composite sort index

Revision ID: 8183be7e0ff7
Revises: 0d99f31373fd
Create Date: 2016-09-23 02:53:35.363000

"""

# revision identifiers, used by Alembic.
revision = '8183be7e0ff7'
down_revision = '0d99f31373fd'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


def upgrade():
    op.create_index(op.f('ix_forum_thread_sort_index'), 'forum_thread', ['sticky', 'updated_at'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_forum_thread_sort_index'), table_name='forum_thread')
