from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.deps import CurrentPlanner, DbSession
from app.models import Planner
from app.schemas.auth import LoginRequest, PlannerOut, TokenResponse
from app.security import create_access_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: DbSession) -> TokenResponse:
    email = data.email.strip().lower()
    planner = db.scalar(select(Planner).where(Planner.email == email))
    if not verify_password(data.password, planner.password_hash if planner else None):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Email o contraseña incorrectos")
    return TokenResponse(access_token=create_access_token(planner.id))


@router.get("/me", response_model=PlannerOut)
def me(planner: CurrentPlanner) -> Planner:
    return planner
