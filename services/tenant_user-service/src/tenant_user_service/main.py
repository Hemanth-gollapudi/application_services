from fastapi import FastAPI

from .tenant_management.tenant_lifecycle.realm_management import api as realm_api

app = FastAPI(title="Tenant User Service")

# Routers
app.include_router(realm_api.router)


@app.get("/healthz")
async def health_check() -> dict[str, str]:
    return {"status": "ok"} 