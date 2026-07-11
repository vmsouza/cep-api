from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_401_UNAUTHORIZED

from app.database import async_session
from app.models.models import ClienteApi


class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ("/docs", "/openapi.json", "/redoc", "/api/health"):
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return JSONResponse(
                status_code=HTTP_401_UNAUTHORIZED,
                content={"code": "1", "message": "X-API-Key header is required"},
            )

        async with async_session() as session:
            result = await session.execute(
                select(ClienteApi).where(
                    ClienteApi.api_key == api_key,
                    ClienteApi.ativo == 1,
                )
            )
            cliente = result.scalar_one_or_none()

        if not cliente:
            return JSONResponse(
                status_code=HTTP_401_UNAUTHORIZED,
                content={"code": "1", "message": "Invalid or inactive API key"},
            )

        request.state.cliente = cliente
        return await call_next(request)
