"""Add Table.data_width column

Revision ID: 5a5b3abc7902
Revises: b767e0e8b061
Create Date: 2021-04-17 22:22:42.784223

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5a5b3abc7902'
down_revision = 'b767e0e8b061'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('table') as batch_op:
        batch_op.add_column(sa.Column('data_width', sa.Integer(), nullable=False, default=0))
        batch_op.alter_column('data_width', default=False)


def downgrade():
    with op.batch_alter_table('table') as batch_op:
        batch_op.drop_column('table', 'data_width')
