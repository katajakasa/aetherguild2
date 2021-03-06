"""Initial tables

Revision ID: cdc4dab4ac01
Revises: 
Create Date: 2016-12-30 02:25:59.516041

"""

revision = 'cdc4dab4ac01'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'file',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.Unicode(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    op.create_table(
        'forum_section',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.Unicode(length=128), nullable=False),
        sa.Column('sort_index', sa.Integer(), nullable=False),
        sa.Column('deleted', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'news_item',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nickname', sa.Unicode(length=64), nullable=False),
        sa.Column('header', sa.Unicode(length=128), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'forum_board',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('section', sa.Integer(), nullable=False),
        sa.Column('title', sa.Unicode(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('req_level', sa.Integer(), nullable=False),
        sa.Column('sort_index', sa.Integer(), nullable=False),
        sa.Column('deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['section'], ['forum_section.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'new_user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('avatar', sa.Unicode(length=32), nullable=True),
        sa.Column('username', sa.Unicode(length=64), nullable=False),
        sa.Column('password', sa.Unicode(length=256), nullable=True),
        sa.Column('nickname', sa.Unicode(length=64), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_contact', sa.DateTime(timezone=True), nullable=False),
        sa.Column('profile_data', sa.Text(), nullable=False),
        sa.Column('deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['avatar'], ['file.key'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    op.create_table(
        'forum_thread',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('board', sa.Integer(), nullable=False),
        sa.Column('user', sa.Integer(), nullable=False),
        sa.Column('title', sa.Unicode(length=128), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('views', sa.Integer(), nullable=False),
        sa.Column('sticky', sa.Boolean(), nullable=False),
        sa.Column('closed', sa.Boolean(), nullable=False),
        sa.Column('deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['board'], ['forum_board.id'], ),
        sa.ForeignKeyConstraint(['user'], ['new_user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_forum_thread_sticky'), 'forum_thread', ['sticky'], unique=False)
    op.create_index(op.f('ix_forum_thread_updated_at'), 'forum_thread', ['updated_at'], unique=False)
    op.create_index(op.f('ix_forum_thread_sort_index'), 'forum_thread', ['sticky', 'updated_at'], unique=False)
    op.create_table(
        'old_user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user', sa.Integer(), nullable=False),
        sa.Column('password', sa.Binary(), nullable=False),
        sa.ForeignKeyConstraint(['user'], ['new_user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'session',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user', sa.Integer(), nullable=False),
        sa.Column('session_key', sa.Unicode(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('activity_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user'], ['new_user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_key')
    )
    op.create_table(
        'forum_last_read',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('thread', sa.Integer(), nullable=False),
        sa.Column('user', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['thread'], ['forum_thread.id'], ),
        sa.ForeignKeyConstraint(['user'], ['new_user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'forum_post',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('thread', sa.Integer(), nullable=False),
        sa.Column('user', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['thread'], ['forum_thread.id'], ),
        sa.ForeignKeyConstraint(['user'], ['new_user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_forum_post_created_at'), 'forum_post', ['created_at'], unique=False)
    op.create_table(
        'forum_edit',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post', sa.Integer(), nullable=False),
        sa.Column('user', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['post'], ['forum_post.id'], ),
        sa.ForeignKeyConstraint(['user'], ['new_user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('forum_edit')
    op.drop_index(op.f('ix_forum_post_created_at'), table_name='forum_post')
    op.drop_table('forum_post')
    op.drop_table('forum_last_read')
    op.drop_table('session')
    op.drop_table('old_user')
    op.drop_index(op.f('ix_forum_thread_sort_index'), table_name='forum_thread')
    op.drop_index(op.f('ix_forum_thread_updated_at'), table_name='forum_thread')
    op.drop_index(op.f('ix_forum_thread_sticky'), table_name='forum_thread')
    op.drop_table('forum_thread')
    op.drop_table('new_user')
    op.drop_table('forum_board')
    op.drop_table('news_item')
    op.drop_table('forum_section')
    op.drop_table('file')
