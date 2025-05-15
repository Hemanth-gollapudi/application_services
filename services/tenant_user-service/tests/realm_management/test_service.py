from unittest.mock import MagicMock

import pytest

from sqlalchemy.orm import Session

from tenant_user_service.tenant_management.tenant_lifecycle.realm_management import (
    schemas, service, models,
)


@pytest.fixture()
def fake_db_session():
    """Provides an in-memory fake session using SQLAlchemy's ORM events. Here, we
    just use a MagicMock since full DB integration is out-of-scope for unit tests."""
    return MagicMock(spec=Session)


@pytest.fixture()
def fake_kc_admin():
    return MagicMock()


def test_create_realm(fake_db_session, fake_kc_admin):
    realm_in = schemas.RealmCreate(customer_type="Large", realm="acme")
    svc = service.RealmService(fake_db_session, fake_kc_admin)

    # Mock repository create return
    fake_obj = models.Realm(realm="acme", customer_type="Large")  # type: ignore[arg-type]
    svc.repo.create = MagicMock(return_value=fake_obj)

    result = svc.create(realm_in)

    fake_kc_admin.create_realm.assert_called_once()
    svc.repo.create.assert_called_once()
    assert result.realm == "acme" 