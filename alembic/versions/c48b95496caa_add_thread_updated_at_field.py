"""Add thread.updated_at field

Revision ID: c48b95496caa
Revises: 80c974fb9b96
Create Date: 2016-09-23 02:05:08.697000

"""

# revision identifiers, used by Alembic.
revision = 'c48b95496caa'
down_revision = '80c974fb9b96'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import arrow


def upgrade():
    op.add_column('forum_thread', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                                            server_default=text('now()')))


def downgrade():
    op.drop_column('forum_thread', 'updated_at')
