"""initial schema

Revision ID: 03e5cb1dcca6
Revises:
Create Date: 2026-10-12

Replaces the ``init_db()`` CREATE TABLE IF NOT EXISTS calls that previously ran
at application import time:

- UNIQUE constraints on users.username / users.email
- indexes for URL listing and click analytics queries
- clicks.url_id now ON DELETE CASCADE: deleting a URL that already has recorded
  clicks removes its click events instead of failing with an IntegrityError
  (the old schema turned DELETE /urls/{id} into a 500 for any clicked link)
- no separate index on clicks(url_id): the composite
  (url_id, clicked_at) index is used for url_id-only lookups via leftmost
  prefix, so a second index would only add write overhead on the hot
  insert-at-redirect path
- no separate index on urls(short_code): UNIQUE(short_code) already creates the
  btree index used by the redirect lookup

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import INET

# revision identifiers, used by Alembic.
revision = "03e5cb1dcca6"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("username", name="uq_users_username"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "urls",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("original_url", sa.Text(), nullable=False),
        sa.Column("short_code", sa.String(length=20), nullable=False),
        sa.Column("click_count", sa.Integer(), server_default=sa.text("0")),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("short_code", name="uq_urls_short_code"),
    )
    op.create_index("ix_urls_user_id", "urls", ["user_id"])

    op.create_table(
        "clicks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("url_id", sa.Integer(), sa.ForeignKey("urls.id", ondelete="CASCADE")),
        sa.Column(
            "clicked_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("user_agent", sa.Text()),
        sa.Column("ip_address", INET()),
    )
    op.create_index("ix_clicks_url_id_clicked_at", "clicks", ["url_id", "clicked_at"])
    op.create_index("ix_clicks_clicked_at", "clicks", ["clicked_at"])


def downgrade() -> None:
    op.drop_index("ix_clicks_clicked_at", table_name="clicks")
    op.drop_index("ix_clicks_url_id_clicked_at", table_name="clicks")
    op.drop_table("clicks")
    op.drop_index("ix_urls_user_id", table_name="urls")
    op.drop_table("urls")
    op.drop_table("users")
