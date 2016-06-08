"""Initial migrations

Revision ID: 656b934ab1a5
Revises: 
Create Date: 2016-06-09 00:16:18.594000
"""

# revision identifiers, used by Alembic.
revision = '656b934ab1a5'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'forum_section',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=64), nullable=True),
        sa.Column('sort_index', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'news_item',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alias', sa.String(length=32), nullable=True),
        sa.Column('post', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=32), nullable=True),
        sa.Column('password', sa.String(length=256), nullable=True),
        sa.Column('alias', sa.String(length=32), nullable=True),
        sa.Column('level', sa.Integer(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_contact', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    op.create_table(
        'forum_board',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('section', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=64), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('min_read_level', sa.Integer(), nullable=True),
        sa.Column('min_write_level', sa.Integer(), nullable=True),
        sa.Column('sort_index', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['section'], ['forum_section.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'session',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_key', sa.String(length=32), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('activity_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_key')
    )
    op.create_table(
        'forum_thread',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('board', sa.Integer(), nullable=True),
        sa.Column('user', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('views', sa.Integer(), nullable=True),
        sa.Column('sticky', sa.Boolean(), nullable=True),
        sa.Column('closed', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['board'], ['forum_board.id'], ),
        sa.ForeignKeyConstraint(['user'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'forum_last_read',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('thread', sa.Integer(), nullable=True),
        sa.Column('user', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['thread'], ['forum_thread.id'], ),
        sa.ForeignKeyConstraint(['user'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'forum_post',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('thread', sa.Integer(), nullable=True),
        sa.Column('user', sa.Integer(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['thread'], ['forum_thread.id'], ),
        sa.ForeignKeyConstraint(['user'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'forum_edit',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post', sa.Integer(), nullable=True),
        sa.Column('user', sa.Integer(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['post'], ['forum_post.id'], ),
        sa.ForeignKeyConstraint(['user'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('forum_edit')
    op.drop_table('forum_post')
    op.drop_table('forum_last_read')
    op.drop_table('forum_thread')
    op.drop_table('session')
    op.drop_table('forum_board')
    op.drop_table('user')
    op.drop_table('newsitem')
    op.drop_table('forum_section')
