from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import auth, events, guests, meta, public
from app.schemas.common import first_validation_message
from app.security import token_can_write

READONLY_MESSAGE = "Esta es una demo de solo lectura: puedes explorar todo, pero los cambios no se guardan."
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

app = FastAPI(title="Convite API", docs_url="/api/docs", openapi_url="/api/openapi.json")

@app.middleware("http")
async def demo_readonly(request: Request, call_next):
    if (
        get_settings().demo_readonly
        and request.method in WRITE_METHODS
        and request.url.path not in ("/api/auth/login", "/api/auth/demo")
    ):
        header = request.headers.get("authorization", "")
        token = header[7:] if header.lower().startswith("bearer ") else ""
        if not token_can_write(token):
            return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": READONLY_MESSAGE})
    return await call_next(request)


app.include_router(meta.router)
app.include_router(auth.router)
app.include_router(events.router)
app.include_router(guests.router)
app.include_router(public.router)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": first_validation_message(exc.errors())},
    )
