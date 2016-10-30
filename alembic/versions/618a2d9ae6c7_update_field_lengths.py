"""Update field lengths

Revision ID: 618a2d9ae6c7
Revises: 8183be7e0ff7
Create Date: 2016-10-30 03:44:22.082180

"""

# revision identifiers, used by Alembic.
revision = '618a2d9ae6c7'
down_revision = '8183be7e0ff7'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


def upgrade():
    op.alter_column('file', 'key',
                    existing_type=mysql.VARCHAR(length=24),
                    type_=sa.String(length=32),
                    existing_nullable=False)
    op.alter_column('forum_board', 'title',
                    existing_type=mysql.VARCHAR(length=64),
                    type_=sa.String(length=128),
                    existing_nullable=False)
    op.alter_column('forum_section', 'title',
                    existing_type=mysql.VARCHAR(length=64),
                    type_=sa.String(length=128),
                    existing_nullable=False)
    op.alter_column('forum_thread', 'title',
                    existing_type=mysql.VARCHAR(length=64),
                    type_=sa.String(length=128),
                    existing_nullable=False)
    op.alter_column('new_user', 'avatar',
                    existing_type=mysql.VARCHAR(length=24),
                    type_=sa.String(length=32),
                    existing_nullable=True)
    op.alter_column('new_user', 'nickname',
                    existing_type=mysql.VARCHAR(length=32),
                    type_=sa.String(length=64),
                    existing_nullable=False)
    op.alter_column('new_user', 'username',
                    existing_type=mysql.VARCHAR(length=32),
                    type_=sa.String(length=64),
                    existing_nullable=False)
    op.alter_column('news_item', 'header',
                    existing_type=mysql.VARCHAR(length=64),
                    type_=sa.String(length=128),
                    existing_nullable=False)
    op.alter_column('news_item', 'nickname',
                    existing_type=mysql.VARCHAR(length=32),
                    type_=sa.String(length=64),
                    existing_nullable=False)
    op.alter_column('session', 'session_key',
                    existing_type=mysql.VARCHAR(length=32),
                    type_=sa.String(length=64),
                    existing_nullable=False)


def downgrade():
    op.alter_column('session', 'session_key',
                    existing_type=sa.String(length=64),
                    type_=mysql.VARCHAR(length=32),
                    existing_nullable=False)
    op.alter_column('news_item', 'nickname',
                    existing_type=sa.String(length=64),
                    type_=mysql.VARCHAR(length=32),
                    existing_nullable=False)
    op.alter_column('news_item', 'header',
                    existing_type=sa.String(length=128),
                    type_=mysql.VARCHAR(length=64),
                    existing_nullable=False)
    op.alter_column('new_user', 'username',
                    existing_type=sa.String(length=64),
                    type_=mysql.VARCHAR(length=32),
                    existing_nullable=False)
    op.alter_column('new_user', 'nickname',
                    existing_type=sa.String(length=64),
                    type_=mysql.VARCHAR(length=32),
                    existing_nullable=False)
    op.alter_column('new_user', 'avatar',
                    existing_type=sa.String(length=32),
                    type_=mysql.VARCHAR(length=24),
                    existing_nullable=True)
    op.alter_column('forum_thread', 'title',
                    existing_type=sa.String(length=128),
                    type_=mysql.VARCHAR(length=64),
                    existing_nullable=False)
    op.alter_column('forum_section', 'title',
                    existing_type=sa.String(length=128),
                    type_=mysql.VARCHAR(length=64),
                    existing_nullable=False)
    op.alter_column('forum_board', 'title',
                    existing_type=sa.String(length=128),
                    type_=mysql.VARCHAR(length=64),
                    existing_nullable=False)
    op.alter_column('file', 'key',
                    existing_type=sa.String(length=32),
                    type_=mysql.VARCHAR(length=24),
                    existing_nullable=False)
