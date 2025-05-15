"""create realms table

Revision ID: 0001_create_realm_table
Revises: 
Create Date: 2025-05-14
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_create_realm_table"
down_revision = None
branch_labels = None
depends_on = None

SCHEMA_NAME = "tenant"

def upgrade():
    # create schema if not exists
    op.execute(sa.text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME}"))

    op.create_table(
        "realms",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("realm", sa.String, nullable=False, unique=True),
        sa.Column("customer_type", sa.String, nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.sql.expression.true()),
        sa.Column("display_name", sa.String),
        sa.Column("display_name_html", sa.String),
        sa.Column("login_theme", sa.String),
        sa.Column("account_theme", sa.String),
        sa.Column("ssl_required", sa.String),
        sa.Column("password_policy", sa.String),
        sa.Column("browser_security_headers", sa.JSON),
        sa.Column("login_with_email_allowed", sa.Boolean),
        sa.Column("registration_allowed", sa.Boolean),
        sa.Column("remember_me", sa.Boolean),
        sa.Column("reset_password_allowed", sa.Boolean),
        sa.Column("verify_email", sa.Boolean),
        sa.Column("duplicate_emails_allowed", sa.Boolean),
        sa.Column("internationalization_enabled", sa.Boolean),
        sa.Column("supported_locales", sa.ARRAY(sa.String)),
        sa.Column("default_locale", sa.String),
        sa.Column("smtp_server", sa.JSON),
        sa.Column("access_token_lifespan", sa.Integer),
        sa.Column("access_code_lifespan_login", sa.Integer),
        sa.Column("sso_session_idle_timeout", sa.Integer),
        sa.Column("sso_session_max_lifespan", sa.Integer),
        sa.Column("revoke_refresh_token", sa.Boolean),
        sa.Column("refresh_token_max_reuse", sa.Integer),
        sa.Column("events_enabled", sa.Boolean),
        sa.Column("events_listeners", sa.ARRAY(sa.String)),
        schema=SCHEMA_NAME
    )


def downgrade():
    op.drop_table("realms", schema=SCHEMA_NAME) 