from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from keycloak import KeycloakAdmin

from . import service, schemas
from ....dependencies import get_db, get_keycloak_admin  # to be implemented at higher level

router = APIRouter(prefix="/realms", tags=["realms"])


@router.post("/", response_model=schemas.RealmRead, status_code=status.HTTP_201_CREATED)
def create_realm(
    payload: schemas.RealmCreate,
    db: Session = Depends(get_db),
    kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
):
    print("Inside /create-realm/ endpoint")
    print(f"Received payload: {payload}")
    print(f"kc_admin object: {kc_admin}")
    try:
        svc = service.RealmService(db, kc_admin)
        realm = svc.create(payload)
        return realm
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/", response_model=List[schemas.RealmRead])
def list_realms(
    customer_type: Optional[str] = None,
    enabled: Optional[bool] = None,
    db: Session = Depends(get_db),
    kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
):
    svc = service.RealmService(db, kc_admin)
    return svc.list(customer_type, enabled)


@router.get("/{realm_name}", response_model=schemas.RealmRead)
def get_realm(
    realm_name: str,
    db: Session = Depends(get_db),
    kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
):
    svc = service.RealmService(db, kc_admin)
    realm = svc.get(realm_name)
    if not realm:
        raise HTTPException(status_code=404, detail="Realm not found")
    return realm


@router.put("/{realm_name}", response_model=schemas.RealmRead)
def update_realm(
    realm_name: str,
    payload: schemas.RealmUpdate,
    db: Session = Depends(get_db),
    kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
):
    svc = service.RealmService(db, kc_admin)
    try:
        return svc.update(realm_name, payload)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve)) from ve


@router.delete("/{realm_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_realm(
    realm_name: str,
    db: Session = Depends(get_db),
    kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
):
    svc = service.RealmService(db, kc_admin)
    svc.delete(realm_name)


@router.get("/test-kc-dependency/", status_code=status.HTTP_200_OK)
def test_keycloak_dependency(
    kc_admin: KeycloakAdmin = Depends(get_keycloak_admin),
):
    print("Inside /test-kc-dependency/ endpoint")
    if kc_admin:
        print("kc_admin object received in test endpoint")
        return {"message": "KeycloakAdmin dependency resolved successfully", "kc_server_url": kc_admin.server_url}
    else:
        print("kc_admin object is None in test endpoint")
        return {"message": "KeycloakAdmin dependency was None (this shouldn't happen if no error)"} 