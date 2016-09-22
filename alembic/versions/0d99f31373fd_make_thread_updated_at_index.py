"""Make thread.updated_at index

Revision ID: 0d99f31373fd
Revises: c48b95496caa
Create Date: 2016-09-23 02:27:08.375000

"""

# revision identifiers, used by Alembic.
revision = '0d99f31373fd'
down_revision = 'c48b95496caa'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


def upgrade():
    op.create_index(op.f('ix_forum_thread_updated_at'), 'forum_thread', ['updated_at'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_forum_thread_updated_at'), table_name='forum_thread')
