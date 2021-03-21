"""Initial migration

Create the necessary models to track registers and their fields

Revision ID: 58fe24dc22a3
Revises: 
Create Date: 2021-03-19 18:32:07.405912

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '58fe24dc22a3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('family',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('feature',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('family_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['family_id'], ['family.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('family_id', 'name', name='u_family_feature')
    )
    op.create_table('register',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('offset', sa.Integer(), nullable=False),
    sa.Column('port_idx_min', sa.Integer(), nullable=False),
    sa.Column('port_idx_max', sa.Integer(), nullable=False),
    sa.Column('array_idx_min', sa.Integer(), nullable=False),
    sa.Column('array_idx_max', sa.Integer(), nullable=False),
    sa.Column('portlist_idx', sa.Integer(), nullable=False),
    sa.Column('bit_offset', sa.Integer(), nullable=False),
    sa.Column('family_id', sa.Integer(), nullable=False),
    sa.Column('feature_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['family_id'], ['family.id'], ),
    sa.ForeignKeyConstraint(['feature_id'], ['feature.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('family_id', 'name', name='u_family_register')
    )
    op.create_table('field',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('lsb', sa.Integer(), nullable=False),
    sa.Column('size', sa.Integer(), nullable=False),
    sa.Column('register_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['register_id'], ['register.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('register_id', 'lsb', name='u_register_field')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('field')
    op.drop_table('register')
    op.drop_table('feature')
    op.drop_table('family')
    # ### end Alembic commands ###