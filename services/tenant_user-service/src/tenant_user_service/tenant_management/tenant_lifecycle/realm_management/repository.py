from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from . import models, schemas


class RealmRepository:
    """Data access layer for realm objects."""

    def __init__(self, db: Session):
        self.db = db

    # READ
    def get(self, realm_name: str) -> Optional[models.Realm]:
        return (
            self.db.query(models.Realm)
            .filter(models.Realm.realm == realm_name)
            .first()
        )

    def list(
        self,
        customer_type: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> List[models.Realm]:
        query = self.db.query(models.Realm)
        if customer_type:
            query = query.filter(models.Realm.customer_type == customer_type)
        if enabled is not None:
            query = query.filter(models.Realm.enabled == enabled)
        return query.all()

    # CUD
    def create(self, data: schemas.RealmCreate) -> models.Realm:
        realm = models.Realm(**data.dict(exclude_unset=True))
        self.db.add(realm)
        self.db.commit()
        self.db.refresh(realm)
        return realm

    def update(
        self, realm_obj: models.Realm, data: schemas.RealmUpdate
    ) -> models.Realm:
        for field, value in data.dict(exclude_unset=True).items():
            setattr(realm_obj, field, value)
        self.db.commit()
        self.db.refresh(realm_obj)
        return realm_obj

    def delete(self, realm_obj: models.Realm) -> None:
        self.db.delete(realm_obj)
        self.db.commit() 