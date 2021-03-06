"""Add CpuTag descriptions

Revision ID: bf3a9f636359
Revises: 5a5b3abc7902
Create Date: 2021-08-22 19:00:46.484697

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bf3a9f636359'
down_revision = '5a5b3abc7902'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('cpu_tag',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('direction', sa.Text(), nullable=False),
    sa.Column('family_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['family_id'], ['family.id'], ),
    sa.ForeignKeyConstraint(['id'], ['described_object.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('cpu_tag_field',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('lsb', sa.Integer(), nullable=False),
    sa.Column('size', sa.Integer(), nullable=False),
    sa.Column('cputag_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['cputag_id'], ['cpu_tag.id'], ),
    sa.ForeignKeyConstraint(['id'], ['described_object.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('cputag_id', 'lsb', name='u_cputag_field')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('cpu_tag_field')
    op.drop_table('cpu_tag')
    # ### end Alembic commands ###
