"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-03-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"pgcrypto\"")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"pg_trgm\"")

    # Enum types
    hand_type_enum = postgresql.ENUM(
        "official", "community", name="hand_type_enum", create_type=False
    )
    hand_status_enum = postgresql.ENUM(
        "draft", "review", "approved", "live", "suspended", "deprecated",
        name="hand_status_enum", create_type=False,
    )
    hand_category_enum = postgresql.ENUM(
        "intelligence", "research", "growth", "social", "content",
        "automation", "finance", "custom",
        name="hand_category_enum", create_type=False,
    )
    activation_status_enum = postgresql.ENUM(
        "active", "paused", "cancelled", "expired",
        name="activation_status_enum", create_type=False,
    )
    payment_currency_enum = postgresql.ENUM(
        "usd", "usdc", "sol", "fgh",
        name="payment_currency_enum", create_type=False,
    )
    run_tier_enum = postgresql.ENUM(
        "quick", "deep", name="run_tier_enum", create_type=False
    )
    run_status_enum = postgresql.ENUM(
        "queued", "running", "completed", "failed", "cancelled",
        name="run_status_enum", create_type=False,
    )
    payment_type_enum = postgresql.ENUM(
        "subscription", "pay_per_run", "builder_stake", "refund",
        name="payment_type_enum", create_type=False,
    )
    payment_status_enum = postgresql.ENUM(
        "pending", "confirmed", "failed", "refunded",
        name="payment_status_enum", create_type=False,
    )
    payment_currency_type_enum = postgresql.ENUM(
        "usd", "usdc", "sol", "fgh",
        name="payment_currency_type_enum", create_type=False,
    )
    subscription_status_enum = postgresql.ENUM(
        "trialing", "active", "past_due", "cancelled", "paused", "expired",
        name="subscription_status_enum", create_type=False,
    )
    builder_tier_enum = postgresql.ENUM(
        "standard", "verified", "elite",
        name="builder_tier_enum", create_type=False,
    )
    review_status_enum = postgresql.ENUM(
        "pending", "in_review", "approved", "rejected", "revision_requested",
        name="review_status_enum", create_type=False,
    )
    stake_status_enum = postgresql.ENUM(
        "locked", "released", "slashed",
        name="stake_status_enum", create_type=False,
    )

    # Create all enum types
    hand_type_enum.create(op.get_bind(), checkfirst=True)
    hand_status_enum.create(op.get_bind(), checkfirst=True)
    hand_category_enum.create(op.get_bind(), checkfirst=True)
    activation_status_enum.create(op.get_bind(), checkfirst=True)
    payment_currency_enum.create(op.get_bind(), checkfirst=True)
    run_tier_enum.create(op.get_bind(), checkfirst=True)
    run_status_enum.create(op.get_bind(), checkfirst=True)
    payment_type_enum.create(op.get_bind(), checkfirst=True)
    payment_status_enum.create(op.get_bind(), checkfirst=True)
    payment_currency_type_enum.create(op.get_bind(), checkfirst=True)
    subscription_status_enum.create(op.get_bind(), checkfirst=True)
    builder_tier_enum.create(op.get_bind(), checkfirst=True)
    review_status_enum.create(op.get_bind(), checkfirst=True)
    stake_status_enum.create(op.get_bind(), checkfirst=True)

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("username", sa.String(50), unique=True, nullable=True),
        sa.Column("display_name", sa.String(100), nullable=True),
        sa.Column("avatar_url", sa.Text, nullable=True),
        sa.Column("bio", sa.Text, nullable=True),
        sa.Column("wallet_address", sa.String(44), unique=True, nullable=False),
        sa.Column("fgh_balance_cache", sa.BigInteger, server_default="0", nullable=False),
        sa.Column("credit_balance_lamports", sa.BigInteger, server_default="0", nullable=False),
        sa.Column("stripe_customer_id", sa.String(50), unique=True, nullable=True),
        sa.Column("is_builder", sa.Boolean, server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_wallet_address", "users", ["wallet_address"])
    op.create_index("ix_users_username", "users", ["username"])

    # --- hands ---
    op.create_table(
        "hands",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("slug", sa.String(80), unique=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("long_description", sa.Text, nullable=True),
        sa.Column("type", hand_type_enum, server_default="community", nullable=False),
        sa.Column("status", hand_status_enum, server_default="draft", nullable=False),
        sa.Column("category", hand_category_enum, nullable=False),
        sa.Column("tags", postgresql.ARRAY(sa.String), server_default="{}", nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("price_monthly_cents", sa.Integer, nullable=True),
        sa.Column("price_quick_lamports", sa.BigInteger, nullable=True),
        sa.Column("price_deep_lamports", sa.BigInteger, nullable=True),
        sa.Column("free_trial_runs", sa.Integer, server_default="0", nullable=False),
        sa.Column("stripe_price_monthly", sa.String(50), nullable=True),
        sa.Column("openfang_hand_slug", sa.String(100), nullable=True),
        sa.Column("hand_toml_url", sa.Text, nullable=True),
        sa.Column("skill_md_url", sa.Text, nullable=True),
        sa.Column("system_prompt_url", sa.Text, nullable=True),
        sa.Column("min_openfang_version", sa.String(20), nullable=True),
        sa.Column("total_activations", sa.Integer, server_default="0", nullable=False),
        sa.Column("total_runs", sa.Integer, server_default="0", nullable=False),
        sa.Column("avg_rating", sa.Numeric(3, 2), server_default="0", nullable=False),
        sa.Column("review_count", sa.Integer, server_default="0", nullable=False),
        sa.Column("icon_emoji", sa.String(10), nullable=True),
        sa.Column("cover_image_url", sa.Text, nullable=True),
        sa.Column("demo_video_url", sa.Text, nullable=True),
        sa.Column("version", sa.String(20), server_default="0.1.0", nullable=False),
        sa.Column("changelog", postgresql.JSONB, server_default="[]", nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_hands_slug", "hands", ["slug"])
    op.create_index("ix_hands_category", "hands", ["category"])
    op.create_index("ix_hands_status", "hands", ["status"])
    op.create_index("ix_hands_author_id", "hands", ["author_id"])
    op.create_index(
        "ix_hands_name_trgm", "hands", ["name"],
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )

    # --- payments (before runs, since runs FK to payments) ---
    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", payment_type_enum, nullable=False),
        sa.Column("status", payment_status_enum, server_default="pending", nullable=False),
        sa.Column("currency", payment_currency_type_enum, nullable=False),
        sa.Column("amount_cents", sa.BigInteger, nullable=True),
        sa.Column("amount_lamports", sa.BigInteger, nullable=True),
        sa.Column("amount_fgh", sa.BigInteger, nullable=True),
        sa.Column("usd_equivalent_cents", sa.BigInteger, nullable=True),
        sa.Column("hand_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hands.id"), nullable=True),
        sa.Column("activation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("stripe_payment_intent_id", sa.String(50), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(50), nullable=True),
        sa.Column("stripe_invoice_id", sa.String(50), nullable=True),
        sa.Column("solana_tx_signature", sa.String(90), nullable=True),
        sa.Column("solana_confirmed_slot", sa.BigInteger, nullable=True),
        sa.Column("fgh_burned_amount", sa.BigInteger, server_default="0", nullable=False),
        sa.Column("burn_tx_signature", sa.String(90), nullable=True),
        sa.Column("builder_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("builder_amount_cents", sa.BigInteger, nullable=True),
        sa.Column("platform_amount_cents", sa.BigInteger, nullable=True),
        sa.Column("payout_status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("payout_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB, server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_payments_user_id", "payments", ["user_id"])
    op.create_index("ix_payments_hand_id", "payments", ["hand_id"])
    op.create_index("ix_payments_stripe_payment_intent_id", "payments", ["stripe_payment_intent_id"])

    # --- activations ---
    op.create_table(
        "activations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("hand_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hands.id"), nullable=False),
        sa.Column("status", activation_status_enum, server_default="active", nullable=False),
        sa.Column("config", postgresql.JSONB, server_default="{}", nullable=False),
        sa.Column("delivery_channel", sa.String(50), server_default="dashboard", nullable=False),
        sa.Column("delivery_target", sa.Text, nullable=True),
        sa.Column("openfang_agent_id", sa.String(100), nullable=True),
        sa.Column("payment_currency", payment_currency_enum, server_default="usd", nullable=False),
        sa.Column("stripe_subscription_id", sa.String(50), nullable=True),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("discount_pct", sa.Integer, server_default="0", nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("paused_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_activations_user_id", "activations", ["user_id"])
    op.create_index("ix_activations_hand_id", "activations", ["hand_id"])
    op.create_index("ix_activations_status", "activations", ["status"])

    # Add FK from payments.activation_id now that activations table exists
    op.create_foreign_key(
        "fk_payments_activation_id", "payments", "activations",
        ["activation_id"], ["id"],
    )

    # --- runs ---
    op.create_table(
        "runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("hand_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hands.id"), nullable=False),
        sa.Column("activation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("activations.id"), nullable=True),
        sa.Column("tier", run_tier_enum, server_default="quick", nullable=False),
        sa.Column("status", run_status_enum, server_default="queued", nullable=False),
        sa.Column("config", postgresql.JSONB, server_default="{}", nullable=False),
        sa.Column("delivery_channel", sa.String(50), server_default="dashboard", nullable=False),
        sa.Column("delivery_target", sa.Text, nullable=True),
        sa.Column("openfang_run_id", sa.String(100), nullable=True),
        sa.Column("openfang_agent_id", sa.String(100), nullable=True),
        sa.Column("output_url", sa.Text, nullable=True),
        sa.Column("output_preview", sa.Text, nullable=True),
        sa.Column("token_count", sa.Integer, nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("payments.id"), nullable=True),
        sa.Column("lamports_charged", sa.BigInteger, nullable=True),
        sa.Column("fgh_used", sa.Boolean, server_default="false", nullable=False),
        sa.Column("discount_pct", sa.Integer, server_default="0", nullable=False),
        sa.Column("queued_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_runs_user_id", "runs", ["user_id"])
    op.create_index("ix_runs_hand_id", "runs", ["hand_id"])
    op.create_index("ix_runs_status", "runs", ["status"])

    # Add FK from payments.run_id now that runs table exists
    op.create_foreign_key(
        "fk_payments_run_id", "payments", "runs",
        ["run_id"], ["id"],
    )

    # --- subscriptions ---
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("activation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("activations.id"), nullable=False),
        sa.Column("status", subscription_status_enum, server_default="active", nullable=False),
        sa.Column("stripe_subscription_id", sa.String(50), unique=True, nullable=True),
        sa.Column("stripe_price_id", sa.String(50), nullable=True),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cancel_at_period_end", sa.Boolean, server_default="false", nullable=False),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])
    op.create_index("ix_subscriptions_stripe_subscription_id", "subscriptions", ["stripe_subscription_id"])

    # --- builders ---
    op.create_table(
        "builders",
        sa.Column("id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("bio", sa.Text, nullable=True),
        sa.Column("twitter_handle", sa.String(50), nullable=True),
        sa.Column("github_handle", sa.String(50), nullable=True),
        sa.Column("tier", builder_tier_enum, server_default="standard", nullable=False),
        sa.Column("is_verified", sa.Boolean, server_default="false", nullable=False),
        sa.Column("total_hands", sa.Integer, server_default="0", nullable=False),
        sa.Column("total_activations", sa.Integer, server_default="0", nullable=False),
        sa.Column("total_revenue_cents", sa.BigInteger, server_default="0", nullable=False),
        sa.Column("revenue_share_pct", sa.Integer, server_default="80", nullable=False),
        sa.Column("first_cohort", sa.Boolean, server_default="false", nullable=False),
        sa.Column("first_cohort_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payout_usdc_address", sa.String(44), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- hand_reviews ---
    op.create_table(
        "hand_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("hand_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hands.id"), nullable=False),
        sa.Column("builder_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("builders.id"), nullable=False),
        sa.Column("status", review_status_enum, server_default="pending", nullable=False),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("submission_notes", sa.Text, nullable=True),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("review_notes", sa.Text, nullable=True),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column("auto_passed", sa.Boolean, nullable=True),
        sa.Column("auto_errors", postgresql.JSONB, server_default="[]", nullable=False),
        sa.Column("security_passed", sa.Boolean, nullable=True),
        sa.Column("functional_passed", sa.Boolean, nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_hand_reviews_hand_id", "hand_reviews", ["hand_id"])
    op.create_index("ix_hand_reviews_builder_id", "hand_reviews", ["builder_id"])

    # --- builder_stakes ---
    op.create_table(
        "builder_stakes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("builder_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("builders.id"), nullable=False),
        sa.Column("hand_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hands.id"), nullable=False),
        sa.Column("status", stake_status_enum, server_default="locked", nullable=False),
        sa.Column("fgh_amount", sa.BigInteger, nullable=False),
        sa.Column("usd_value_cents", sa.Integer, nullable=False),
        sa.Column("lock_tx_signature", sa.String(90), nullable=True),
        sa.Column("release_tx_signature", sa.String(90), nullable=True),
        sa.Column("slash_pct", sa.Integer, server_default="0", nullable=False),
        sa.Column("slash_reason", sa.Text, nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("release_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("slashed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_builder_stakes_builder_id", "builder_stakes", ["builder_id"])

    # --- fgh_burns ---
    op.create_table(
        "fgh_burns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("trigger_type", sa.String(50), nullable=False),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("payments.id"), nullable=True),
        sa.Column("stake_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("builder_stakes.id"), nullable=True),
        sa.Column("fgh_burned", sa.BigInteger, nullable=False),
        sa.Column("usd_equivalent", sa.Integer, nullable=True),
        sa.Column("tx_signature", sa.String(90), nullable=False),
        sa.Column("confirmed_slot", sa.BigInteger, nullable=True),
        sa.Column("burned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_fgh_burns_tx_signature", "fgh_burns", ["tx_signature"])

    # --- hand_metrics ---
    op.create_table(
        "hand_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("activation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("activations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("metric_key", sa.String(100), nullable=False),
        sa.Column("metric_value", sa.Numeric, nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_hand_metrics_activation_id", "hand_metrics", ["activation_id"])
    op.create_index("ix_hand_metrics_metric_key", "hand_metrics", ["metric_key"])

    # --- credit_transactions ---
    op.create_table(
        "credit_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("lamports", sa.BigInteger, nullable=False),
        sa.Column("balance_after", sa.BigInteger, nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("runs.id"), nullable=True),
        sa.Column("tx_signature", sa.String(90), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_credit_transactions_user_id", "credit_transactions", ["user_id"])

    # --- Row Level Security ---
    rls_tables = [
        "activations", "runs", "payments", "subscriptions",
        "credit_transactions", "hand_metrics",
    ]
    for table in rls_tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")

    # RLS policies: users can only see their own rows
    for table in ["activations", "runs", "payments", "subscriptions", "credit_transactions"]:
        op.execute(
            f"CREATE POLICY {table}_user_isolation ON {table} "
            f"FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid)"
        )

    # hand_metrics: accessible via activation ownership
    op.execute(
        "CREATE POLICY hand_metrics_user_isolation ON hand_metrics "
        "FOR ALL USING (activation_id IN ("
        "  SELECT id FROM activations WHERE user_id = current_setting('app.current_user_id')::uuid"
        "))"
    )


def downgrade() -> None:
    # Drop RLS policies
    for table in ["activations", "runs", "payments", "subscriptions", "credit_transactions"]:
        op.execute(f"DROP POLICY IF EXISTS {table}_user_isolation ON {table}")
    op.execute("DROP POLICY IF EXISTS hand_metrics_user_isolation ON hand_metrics")

    # Disable RLS
    for table in ["activations", "runs", "payments", "subscriptions", "credit_transactions", "hand_metrics"]:
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    # Drop tables in reverse dependency order
    op.drop_table("credit_transactions")
    op.drop_table("hand_metrics")
    op.drop_table("fgh_burns")
    op.drop_table("builder_stakes")
    op.drop_table("hand_reviews")
    op.drop_table("builders")
    op.drop_table("subscriptions")

    # Drop deferred FKs before dropping runs/activations
    op.drop_constraint("fk_payments_run_id", "payments", type_="foreignkey")
    op.drop_constraint("fk_payments_activation_id", "payments", type_="foreignkey")

    op.drop_table("runs")
    op.drop_table("activations")
    op.drop_table("payments")
    op.drop_table("hands")
    op.drop_table("users")

    # Drop enum types
    for enum_name in [
        "stake_status_enum", "review_status_enum", "builder_tier_enum",
        "subscription_status_enum", "payment_currency_type_enum",
        "payment_status_enum", "payment_type_enum", "run_status_enum",
        "run_tier_enum", "payment_currency_enum", "activation_status_enum",
        "hand_category_enum", "hand_status_enum", "hand_type_enum",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")

    # Drop extensions
    op.execute('DROP EXTENSION IF EXISTS "pg_trgm"')
    op.execute('DROP EXTENSION IF EXISTS "pgcrypto"')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
