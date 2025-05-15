from __future__ import annotations

from typing import Optional, List, Dict

from pydantic import BaseModel, Field


class RealmBase(BaseModel):
    customer_type: str = Field(..., description="Customer size segment (Large, Medium, Small)")
    realm: str = Field(..., description="Keycloak realm name")
    enabled: Optional[bool] = True

    display_name: Optional[str]
    display_name_html: Optional[str]
    login_theme: Optional[str]
    account_theme: Optional[str]

    ssl_required: Optional[str]
    password_policy: Optional[str]
    browser_security_headers: Optional[Dict[str, str]]

    login_with_email_allowed: Optional[bool]
    registration_allowed: Optional[bool]
    remember_me: Optional[bool]
    reset_password_allowed: Optional[bool]
    verify_email: Optional[bool]
    duplicate_emails_allowed: Optional[bool]

    internationalization_enabled: Optional[bool]
    supported_locales: Optional[List[str]]
    default_locale: Optional[str]

    smtp_server: Optional[Dict[str, str]]

    access_token_lifespan: Optional[int]
    access_code_lifespan_login: Optional[int]
    sso_session_idle_timeout: Optional[int]
    sso_session_max_lifespan: Optional[int]

    revoke_refresh_token: Optional[bool]
    refresh_token_max_reuse: Optional[int]

    events_enabled: Optional[bool]
    events_listeners: Optional[List[str]]

    class Config:
        orm_mode = True


class RealmCreate(RealmBase):
    pass


class RealmUpdate(BaseModel):
    enabled: Optional[bool]
    display_name: Optional[str]
    display_name_html: Optional[str]
    login_theme: Optional[str]
    account_theme: Optional[str]
    password_policy: Optional[str]
    browser_security_headers: Optional[Dict[str, str]]
    events_enabled: Optional[bool]
    events_listeners: Optional[List[str]]
    # Include any other mutable fields as optional


class RealmRead(RealmBase):
    id: int 