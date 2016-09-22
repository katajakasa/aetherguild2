"""Add thread.sticky index

Revision ID: 80c974fb9b96
Revises: 399c5e3a5e1b
Create Date: 2016-09-23 01:33:14.153000

"""

# revision identifiers, used by Alembic.
revision = '80c974fb9b96'
down_revision = '399c5e3a5e1b'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


def upgrade():
    op.create_index(op.f('ix_forum_thread_sticky'), 'forum_thread', ['sticky'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_forum_thread_sticky'), table_name='forum_thread')
