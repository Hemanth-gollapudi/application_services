from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from keycloak import KeycloakAdmin

DATABASE_URL = os.getenv("APP_DATABASE_URL", "postgresql://appuser:changeme@localhost:5432/appdb")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Database dependency -------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Keycloak Admin dependency -------------------------------------------

def get_keycloak_admin() -> KeycloakAdmin:
    server_url = os.getenv("KEYCLOAK_URL", "http://keycloak-tenant:8080/")
    username = os.getenv("KEYCLOAK_ADMIN", "admin")
    password = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin")
    realm_name = os.getenv("KEYCLOAK_ADMIN_REALM", "master")

    print(f"Attempting to connect to Keycloak with URL: {server_url}, User: {username}, Realm: {realm_name}")
    try:
        kc_admin = KeycloakAdmin(
            server_url=server_url,
            username=username,
            password=password,
            realm_name=realm_name,
            verify=False,
        )
        print("KeycloakAdmin object created successfully.")
        return kc_admin
    except Exception as e:
        print(f"Error creating KeycloakAdmin object: {e}")
        raise 