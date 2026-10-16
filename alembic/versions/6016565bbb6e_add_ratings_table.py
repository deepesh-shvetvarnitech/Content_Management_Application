"""add ratings table

Revision ID: 6016565bbb6e
Revises: f9a347a41953
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6016565bbb6e"
down_revision: Union[str, Sequence[str], None] = "f9a347a41953"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ratings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("blog_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "value >= 1 AND value <= 5",
            name="ck_rating_value_range",
        ),
        sa.ForeignKeyConstraint(
            ["blog_id"], ["blogs.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "blog_id", "user_id", name="uq_rating_blog_user"
        ),
    )

    op.create_index("ix_ratings_id", "ratings", ["id"], unique=False)
    op.create_index(
        "ix_ratings_blog_id", "ratings", ["blog_id"], unique=False
    )
    op.create_index(
        "ix_ratings_user_id", "ratings", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_ratings_user_id", table_name="ratings")
    op.drop_index("ix_ratings_blog_id", table_name="ratings")
    op.drop_index("ix_ratings_id", table_name="ratings")
    op.drop_table("ratings")
