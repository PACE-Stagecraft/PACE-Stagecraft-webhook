from fastapi import FastAPI

from app.api.routes.webhooks import router as webhooks_router
from app.core.config import settings

app = FastAPI(
    title="PipelineIQ Webhook Service",
    version="0.1.0",
    description="Receives GitHub webhook events and publishes them to SQS",
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)

app.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok", "service": "webhook-service"}
