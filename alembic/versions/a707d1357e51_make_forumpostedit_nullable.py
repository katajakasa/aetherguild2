"""Make ForumPostEdit nullable

Revision ID: a707d1357e51
Revises: b81eec207c58
Create Date: 2016-06-22 23:47:34.200000

"""

# revision identifiers, used by Alembic.
revision = 'a707d1357e51'
down_revision = 'b81eec207c58'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


def upgrade():
    op.alter_column('forum_edit', 'message', existing_type=mysql.TEXT(), nullable=True)


def downgrade():
    op.alter_column('forum_edit', 'message', existing_type=mysql.TEXT(), nullable=False)
