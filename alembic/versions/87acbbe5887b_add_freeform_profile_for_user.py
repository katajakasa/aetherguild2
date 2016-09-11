"""Add freeform profile for user

Revision ID: 87acbbe5887b
Revises: f2a71c7b93b6
Create Date: 2016-09-11 21:39:20.753000

"""

# revision identifiers, used by Alembic.
revision = '87acbbe5887b'
down_revision = 'f2a71c7b93b6'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('profile_data', sa.Text(), nullable=False, server_default=u'{}'))


def downgrade():
    op.drop_column('user', 'profile_data')
