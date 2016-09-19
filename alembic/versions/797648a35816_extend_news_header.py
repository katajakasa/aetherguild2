"""Extend news header

Revision ID: 797648a35816
Revises: 66ba9cf70613
Create Date: 2016-09-20 00:22:15.445000

"""

# revision identifiers, used by Alembic.
revision = '797648a35816'
down_revision = '66ba9cf70613'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


def upgrade():
    op.alter_column(
        'news_item',
        'header',
        existing_type=mysql.VARCHAR(length=32),
        type_=sa.String(length=64),
        existing_nullable=False)


def downgrade():
    op.alter_column(
        'news_item',
        'header',
        existing_type=sa.String(length=64),
        type_=mysql.VARCHAR(length=32),
        existing_nullable=False)
