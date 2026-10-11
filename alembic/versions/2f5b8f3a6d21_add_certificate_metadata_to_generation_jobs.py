"""add certificate metadata to generation jobs

Revision ID: 2f5b8f3a6d21
Revises: e605a95e8ceb
Create Date: 2026-10-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2f5b8f3a6d21"
down_revision: Union[str, Sequence[str], None] = "e605a95e8ceb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the metadata required when creating a generation job."""
    op.add_column(
        "generation_jobs",
        sa.Column(
            "certificate_title",
            sa.String(length=255),
            nullable=False,
            server_default="",
        ),
    )
    op.add_column(
        "generation_jobs",
        sa.Column(
            "issuer",
            sa.String(length=255),
            nullable=False,
            server_default="",
        ),
    )
    op.alter_column(
        "generation_jobs",
        "certificate_title",
        server_default=None,
    )
    op.alter_column(
        "generation_jobs",
        "issuer",
        server_default=None,
    )


def downgrade() -> None:
    """Remove the generation job certificate metadata."""
    op.drop_column("generation_jobs", "issuer")
    op.drop_column("generation_jobs", "certificate_title")
