"""Add basic User class

Revision ID: 7145d5e7a458
Revises: 3a9e5c60f9a7
Create Date: 2021-03-21 14:31:17.620021

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7145d5e7a458'
down_revision = '3a9e5c60f9a7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user')
    # ### end Alembic commands ###
