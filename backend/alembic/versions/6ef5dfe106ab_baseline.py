"""baseline

Revision ID: 6ef5dfe106ab
Revises: 
Create Date: 2026-01-19 21:35:49.789018
"""

from alembic import op
import sqlalchemy as sa



revision = '6ef5dfe106ab'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Baseline revision; no schema changes applied.
    pass


def downgrade() -> None:
    # Baseline revision; no schema changes applied.
    pass
