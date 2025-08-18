"""chat type

Revision ID: a577da2a22eb
Revises: 94145ef4ef7e
Create Date: 2025-07-21 14:46:58.872750

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a577da2a22eb'
down_revision: Union[str, Sequence[str], None] = '94145ef4ef7e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

chattype_enum = sa.Enum('CHANNEL', 'SUPERGROUP', 'BASIC_GROUP', name='chattype')

def upgrade() -> None:
    # 2. Create the ENUM type in the database FIRST.
    chattype_enum.create(op.get_bind(), checkfirst=True)
    
    # 3. NOW, add the column that USES the newly created type.
    op.add_column('channels', sa.Column('type', chattype_enum, nullable=True))


def downgrade() -> None:
    # For a downgrade, we do the reverse: drop the column, then drop the type.
    op.drop_column('channels', 'type')
    chattype_enum.drop(op.get_bind(), checkfirst=True)
