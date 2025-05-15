from sqlalchemy import Column, String, Boolean, Integer, JSON, ARRAY, MetaData
from sqlalchemy.orm import declarative_base

SCHEMA_NAME = "tenant"

# Use MetaData with schema for all tables
metadata = MetaData(schema=SCHEMA_NAME)

Base = declarative_base(metadata=metadata)


class Realm(Base):
    """SQLAlchemy model for a Keycloak Realm representation stored in Postgres."""

    __tablename__ = "realms"

    id: int = Column(Integer, primary_key=True, index=True)
    realm: str = Column(String, unique=True, nullable=False)
    customer_type: str = Column(String, nullable=False)
    enabled: bool = Column(Boolean, default=True)

    display_name: str | None = Column(String)
    display_name_html: str | None = Column(String)
    login_theme: str | None = Column(String)
    account_theme: str | None = Column(String)

    ssl_required: str | None = Column(String)
    password_policy: str | None = Column(String)
    browser_security_headers = Column(JSON)

    login_with_email_allowed: bool | None = Column(Boolean)
    registration_allowed: bool | None = Column(Boolean)
    remember_me: bool | None = Column(Boolean)
    reset_password_allowed: bool | None = Column(Boolean)
    verify_email: bool | None = Column(Boolean)
    duplicate_emails_allowed: bool | None = Column(Boolean)

    internationalization_enabled: bool | None = Column(Boolean)
    supported_locales = Column(ARRAY(String))
    default_locale: str | None = Column(String)

    smtp_server = Column(JSON)

    access_token_lifespan: int | None = Column(Integer)
    access_code_lifespan_login: int | None = Column(Integer)
    sso_session_idle_timeout: int | None = Column(Integer)
    sso_session_max_lifespan: int | None = Column(Integer)

    revoke_refresh_token: bool | None = Column(Boolean)
    refresh_token_max_reuse: int | None = Column(Integer)

    events_enabled: bool | None = Column(Boolean)
    events_listeners = Column(ARRAY(String)) 