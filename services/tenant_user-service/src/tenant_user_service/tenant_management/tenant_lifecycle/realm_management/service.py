from __future__ import annotations

from typing import List, Optional

from keycloak import KeycloakAdmin
from sqlalchemy.orm import Session

from . import repository, schemas, models


class RealmService:
    """Business logic for realm management across Keycloak and Postgres."""

    def __init__(self, db: Session, kc_admin: KeycloakAdmin):
        self.repo = repository.RealmRepository(db)
        self.kc_admin = kc_admin

    # Utility to transform pydantic model to Keycloak realm payload.
    @staticmethod
    def _to_keycloak_payload(data: schemas.RealmBase) -> dict:
        # Start with a clean slate, only adding fields Keycloak understands.
        # Field names here should match what python-keycloak client expects,
        # which then translates to Keycloak server's RealmRepresentation.
        # Common fields: realm, enabled, displayName, loginTheme, accountTheme, etc.
        # The python-keycloak library often uses the same names as Keycloak's REST API (camelCase)
        # or allows snake_case and converts them. For safety, let's check a few common ones.
        # The `keycloak-python` library is generally good about accepting snake_case for known attributes.

        kc_payload = {}

        # Mandatory or core fields
        kc_payload["realm"] = data.realm
        if data.enabled is not None:
            kc_payload["enabled"] = data.enabled
        else:
            kc_payload["enabled"] = True # Default if not provided

        # Optional fields (add more as needed, ensuring names are Keycloak-compatible)
        if data.display_name is not None:
            kc_payload["displayName"] = data.display_name # Keycloak often uses camelCase
        if data.display_name_html is not None:
            kc_payload["displayNameHtml"] = data.display_name_html
        if data.login_theme is not None:
            kc_payload["loginTheme"] = data.login_theme
        if data.account_theme is not None:
            kc_payload["accountTheme"] = data.account_theme
        
        if data.ssl_required is not None:
            kc_payload["sslRequired"] = data.ssl_required
        if data.password_policy is not None:
            # Password policy is a string, but complex ones can be set via API.
            # This assumes it's a simple policy string name.
            kc_payload["passwordPolicy"] = data.password_policy
        if data.browser_security_headers is not None:
            kc_payload["browserSecurityHeaders"] = data.browser_security_headers

        if data.login_with_email_allowed is not None:
            kc_payload["loginWithEmailAllowed"] = data.login_with_email_allowed
        if data.registration_allowed is not None:
            kc_payload["registrationAllowed"] = data.registration_allowed
        if data.remember_me is not None:
            kc_payload["rememberMe"] = data.remember_me
        if data.reset_password_allowed is not None:
            kc_payload["resetPasswordAllowed"] = data.reset_password_allowed
        if data.verify_email is not None:
            kc_payload["verifyEmail"] = data.verify_email
        if data.duplicate_emails_allowed is not None:
            kc_payload["duplicateEmailsAllowed"] = data.duplicate_emails_allowed

        if data.internationalization_enabled is not None:
            kc_payload["internationalizationEnabled"] = data.internationalization_enabled
        if data.supported_locales is not None:
            kc_payload["supportedLocales"] = data.supported_locales
        if data.default_locale is not None:
            kc_payload["defaultLocale"] = data.default_locale

        if data.smtp_server is not None: # smtpServer is a complex object (dict)
            kc_payload["smtpServer"] = data.smtp_server
        
        if data.access_token_lifespan is not None:
            kc_payload["accessTokenLifespan"] = data.access_token_lifespan
        # Add other lifespan properties similarly if needed:
        # accessCodeLifespanUserAction, accessCodeLifespanLogin, ssoSessionIdleTimeout, ssoSessionMaxLifespan etc.
        if data.access_code_lifespan_login is not None:
            kc_payload["accessCodeLifespanLogin"] = data.access_code_lifespan_login
        if data.sso_session_idle_timeout is not None:
            kc_payload["ssoSessionIdleTimeout"] = data.sso_session_idle_timeout
        if data.sso_session_max_lifespan is not None:
            kc_payload["ssoSessionMaxLifespan"] = data.sso_session_max_lifespan
            
        if data.revoke_refresh_token is not None:
            kc_payload["revokeRefreshToken"] = data.revoke_refresh_token
        if data.refresh_token_max_reuse is not None: # This might not be a direct field, often part of token settings object
             pass # Placeholder - check KC docs for refresh token max reuse setting path
        
        if data.events_enabled is not None:
            kc_payload["eventsEnabled"] = data.events_enabled
        if data.events_listeners is not None:
            kc_payload["eventsListeners"] = data.events_listeners
            
        # Exclude any fields that are purely for your app's DB and not for Keycloak
        # e.g., 'customer_type' is not sent.

        print(f"Constructed Keycloak payload: {kc_payload}") # For debugging
        return kc_payload

    # CRUD -------------------------------------------------------------
    def create(self, data: schemas.RealmCreate) -> models.Realm:
        # Call Keycloak first
        self.kc_admin.create_realm(payload=self._to_keycloak_payload(data))
        # Persist in DB
        return self.repo.create(data)

    def list(
        self, customer_type: Optional[str] = None, enabled: Optional[bool] = None
    ) -> List[models.Realm]:
        return self.repo.list(customer_type=customer_type, enabled=enabled)

    def get(self, realm_name: str) -> Optional[models.Realm]:
        return self.repo.get(realm_name)

    def update(self, realm_name: str, data: schemas.RealmUpdate) -> models.Realm:
        # Update Keycloak first
        self.kc_admin.update_realm(realm_name=realm_name, payload=self._to_keycloak_payload(data))
        obj = self.repo.get(realm_name)
        if not obj:
            raise ValueError("Realm not found")
        return self.repo.update(obj, data)

    def delete(self, realm_name: str) -> None:
        # Delete in Keycloak
        self.kc_admin.delete_realm(realm_name=realm_name)
        obj = self.repo.get(realm_name)
        if obj:
            self.repo.delete(obj) 