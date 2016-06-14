"""Initial

Revision ID: 4becb26bb41d
Revises: 
Create Date: 2016-06-15 00:56:45.030000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '4becb26bb41d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'forum_section',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=64), nullable=False),
        sa.Column('sort_index', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'news_item',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alias', sa.String(length=32), nullable=False),
        sa.Column('post', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=32), nullable=False),
        sa.Column('password', sa.String(length=256), nullable=False),
        sa.Column('nickname', sa.String(length=32), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_contact', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    op.create_table(
        'forum_board',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('section', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=64), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('req_level', sa.Integer(), nullable=False),
        sa.Column('sort_index', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['section'], ['forum_section.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'session',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user', sa.Integer(), nullable=False),
        sa.Column('session_key', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('activity_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_key')
    )
    op.create_table(
        'forum_thread',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('board', sa.Integer(), nullable=False),
        sa.Column('user', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('views', sa.Integer(), nullable=False),
        sa.Column('sticky', sa.Boolean(), nullable=False),
        sa.Column('closed', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['board'], ['forum_board.id'], ),
        sa.ForeignKeyConstraint(['user'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'forum_last_read',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('thread', sa.Integer(), nullable=False),
        sa.Column('user', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['thread'], ['forum_thread.id'], ),
        sa.ForeignKeyConstraint(['user'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'forum_post',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('thread', sa.Integer(), nullable=False),
        sa.Column('user', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['thread'], ['forum_thread.id'], ),
        sa.ForeignKeyConstraint(['user'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'forum_edit',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post', sa.Integer(), nullable=False),
        sa.Column('user', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
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
    op.drop_table('news_item')
    op.drop_table('forum_section')
