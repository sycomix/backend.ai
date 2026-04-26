"""add app_config_fragments table

Adds the per-scope raw fragment table keyed by
`(scope_type, scope_id, name)`. `name` is a FK to
`app_config_policies.config_name` with default NO ACTION enforcing the
required-policy invariant.

Stacks on top of `5df264862995_add_app_config_policies.py`; the
policy table must exist before the FK can be created.

Revision ID: a662131d5603
Revises: 5df264862995
Create Date: 2026-04-24

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

from ai.backend.manager.models.base import IDColumn

# revision identifiers, used by Alembic.
revision = "a662131d5603"
down_revision = "5df264862995"
# Part of: 26.5.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_config_fragments",
        IDColumn(),
        sa.Column(
            "scope_type",
            sa.String(length=32),
            nullable=False,
            index=True,
        ),
        sa.Column("scope_id", sa.String(length=255), nullable=False),
        sa.Column(
            "name",
            sa.String(length=128),
            sa.ForeignKey(
                # No ON DELETE / ON UPDATE — Postgres default NO ACTION
                # enforces the required-policy invariant: a policy
                # cannot be dropped while fragments reference it, and
                # config_name is immutable so ON UPDATE never fires.
                "app_config_policies.config_name",
                name="fk_app_config_fragments_name_app_config_policies_config_name",
            ),
            nullable=False,
        ),
        sa.Column(
            "config",
            pgsql.JSONB(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.UniqueConstraint(
            "scope_type",
            "scope_id",
            "name",
            name="uq_app_config_fragments_scope_name",
        ),
    )


def downgrade() -> None:
    op.drop_table("app_config_fragments")
