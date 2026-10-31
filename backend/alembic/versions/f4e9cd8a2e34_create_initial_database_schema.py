"""create initial database schema

Revision ID: f4e9cd8a2e34
Revises:
Create Date: 2026-10-31
"""

from typing import Sequence, Union

from alembic import op

from app.core.database import Base
import app.models


revision: str = "f4e9cd8a2e34"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())