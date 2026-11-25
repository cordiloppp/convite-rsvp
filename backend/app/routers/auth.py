from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.deps import CurrentPlanner, DbSession
from app.models import Planner
from app.schemas.auth import LoginRequest, PlannerOut, TokenResponse
from app.config import get_settings
from app.security import create_access_token, owner_password_matches, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: DbSession) -> TokenResponse:
    email = data.email.strip().lower()
    planner = db.scalar(select(Planner).where(Planner.email == email))
    # The owner's private password opens the same account with write access.
    if planner is not None and owner_password_matches(data.password):
        return TokenResponse(access_token=create_access_token(planner.id, can_write=True))
    if not verify_password(data.password, planner.password_hash if planner else None):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Email o contraseña incorrectos")
    can_write = not get_settings().demo_readonly
    return TokenResponse(access_token=create_access_token(planner.id, can_write=can_write))


@router.get("/me", response_model=PlannerOut)
def me(planner: CurrentPlanner) -> Planner:
    return planner
