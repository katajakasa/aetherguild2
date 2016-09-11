"""Add file table

Revision ID: 587aa8e212fa
Revises: 9323373ab1b5
Create Date: 2016-09-11 00:51:13.339000

"""

# revision identifiers, used by Alembic.
revision = '587aa8e212fa'
down_revision = '9323373ab1b5'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'file',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=24), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('owner', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['owner'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    op.add_column(u'user', sa.Column('avatar', sa.String(length=24), nullable=True))
    op.create_foreign_key(None, 'user', 'file', ['avatar'], ['key'])


def downgrade():
    op.drop_constraint(None, 'user', type='foreignkey')
    op.drop_column(u'user', 'avatar')
    op.drop_table('file')
