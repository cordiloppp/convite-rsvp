from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.routers import auth, events, guests, meta, public
from app.schemas.common import first_validation_message

app = FastAPI(title="Convite API", docs_url="/api/docs", openapi_url="/api/openapi.json")

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
