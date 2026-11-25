from fastapi import APIRouter
from sqlalchemy import text

from app.config import get_settings
from app.deps import DbSession

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/health")
def health(db: DbSession) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@router.get("/config")
def public_config() -> dict[str, str | bool]:
    settings = get_settings()
    return {
        "brand_name": settings.brand_name,
        "brand_url": settings.brand_url,
        "timezone": settings.app_timezone,
        "demo_readonly": settings.demo_readonly,
    }
