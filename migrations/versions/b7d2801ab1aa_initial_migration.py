"""Initial migration

Revision ID: b7d2801ab1aa
Revises: 
Create Date: 2024-12-29 17:10:42.691157

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7d2801ab1aa'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('technician_login', schema=None) as batch_op:
        batch_op.add_column(sa.Column('email', sa.String(length=120), nullable=False))
        batch_op.create_unique_constraint(None, ['email'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('technician_login', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')
        batch_op.drop_column('email')

    # ### end Alembic commands ###
