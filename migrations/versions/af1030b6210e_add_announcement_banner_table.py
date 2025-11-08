"""Add announcement banner table

Revision ID: af1030b6210e
Revises: 5292fb690208
Create Date: 2025-11-07 10:16:25.108171

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'af1030b6210e'
down_revision = '5292fb690208'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('announcement_banners',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('text', sa.String(), nullable=False),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('bg_color', sa.String(), nullable=True),
    sa.Column('text_color', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('announcement_banners')
