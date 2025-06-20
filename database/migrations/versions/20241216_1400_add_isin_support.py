"""Add ISIN support to assets and create ISIN mapping table

Revision ID: add_isin_support
Revises: 08230f29a0db
Create Date: 2024-12-16 14:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_isin_support"
down_revision = "08230f29a0db"
branch_labels = None
depends_on = None


def upgrade():
    """Add ISIN support to the database."""

    # Add ISIN field to assets table
    op.add_column("assets", sa.Column("isin", sa.String(12), nullable=True))

    # Add constraint to validate ISIN format (2 letters + 9 alphanumeric + 1 digit)
    op.create_check_constraint(
        "assets_isin_format_check",
        "assets",
        "isin IS NULL OR isin ~ '^[A-Z]{2}[A-Z0-9]{9}[0-9]$'",
    )

    # Create index on ISIN for fast lookups
    op.create_index("idx_assets_isin", "assets", ["isin"])

    # Create ISIN to ticker mapping table
    op.create_table(
        "isin_ticker_mappings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("isin", sa.String(12), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("exchange_code", sa.String(10), nullable=True),
        sa.Column("exchange_name", sa.String(100), nullable=True),
        sa.Column("security_name", sa.String(200), nullable=True),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "last_updated",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Add constraint to validate ISIN format in mapping table
    op.create_check_constraint(
        "isin_ticker_mappings_isin_format_check",
        "isin_ticker_mappings",
        "isin ~ '^[A-Z]{2}[A-Z0-9]{9}[0-9]$'",
    )

    # Add constraint to validate confidence score
    op.create_check_constraint(
        "isin_ticker_mappings_confidence_check",
        "isin_ticker_mappings",
        "confidence >= 0.0 AND confidence <= 1.0",
    )

    # Create indexes for the mapping table
    op.create_index("idx_isin_mappings_isin", "isin_ticker_mappings", ["isin"])
    op.create_index("idx_isin_mappings_ticker", "isin_ticker_mappings", ["ticker"])
    op.create_index(
        "idx_isin_mappings_exchange", "isin_ticker_mappings", ["exchange_code"]
    )
    op.create_index("idx_isin_mappings_active", "isin_ticker_mappings", ["is_active"])
    op.create_index("idx_isin_mappings_source", "isin_ticker_mappings", ["source"])

    # Create unique constraint for active mappings (handled by application logic for now)
    # Note: Partial unique constraints require direct SQL for proper cross-database compatibility

    # Create ISIN validation cache table for performance
    op.create_table(
        "isin_validation_cache",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("isin", sa.String(12), nullable=False),
        sa.Column("is_valid", sa.Boolean(), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=True),
        sa.Column("country_name", sa.String(100), nullable=True),
        sa.Column("national_code", sa.String(9), nullable=True),
        sa.Column("check_digit", sa.String(1), nullable=True),
        sa.Column("validation_error", sa.Text(), nullable=True),
        sa.Column(
            "cached_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Add constraint to validate ISIN format in cache table
    op.create_check_constraint(
        "isin_validation_cache_isin_format_check",
        "isin_validation_cache",
        "isin ~ '^[A-Z]{2}[A-Z0-9]{9}[0-9]$'",
    )

    # Create unique index on ISIN for validation cache
    op.create_unique_constraint(
        "uq_isin_validation_cache_isin", "isin_validation_cache", ["isin"]
    )
    op.create_index(
        "idx_isin_validation_cache_valid", "isin_validation_cache", ["is_valid"]
    )
    op.create_index(
        "idx_isin_validation_cache_country", "isin_validation_cache", ["country_code"]
    )


def downgrade():
    """Remove ISIN support from the database."""

    # Drop ISIN validation cache table
    op.drop_table("isin_validation_cache")

    # Drop ISIN ticker mappings table
    op.drop_table("isin_ticker_mappings")

    # Drop ISIN index from assets table
    op.drop_index("idx_assets_isin", table_name="assets")

    # Drop ISIN constraint from assets table
    op.drop_constraint("assets_isin_format_check", "assets", type_="check")

    # Drop ISIN column from assets table
    op.drop_column("assets", "isin")
