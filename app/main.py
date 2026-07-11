from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middleware.api_key import ApiKeyMiddleware
from app.routers import cep, cidades, estados, paises

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(ApiKeyMiddleware)

app.include_router(cep.router, prefix="/api")
app.include_router(cidades.router, prefix="/api")
app.include_router(estados.router, prefix="/api")
app.include_router(paises.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}
