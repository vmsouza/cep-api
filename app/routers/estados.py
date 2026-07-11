from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.schemas import ErrorResponse, EstadoItem

router = APIRouter(prefix="/estados", tags=["Estados"])


@router.get("")
async def list_estados(
    session: AsyncSession = Depends(get_session),
):
    sql = text("""
        SELECT codigo, nome, sigla, pais_codigo
        FROM ibge_estados
        ORDER BY nome
    """)
    result = await session.execute(sql)
    rows = result.fetchall()

    return {
        "code": "0",
        "data": [
            EstadoItem(codigo=r.codigo, nome=r.nome, sigla=r.sigla, pais_codigo=r.pais_codigo)
            for r in rows
        ],
    }


@router.get("/{codigo}", responses={404: {"model": ErrorResponse}})
async def get_estado(
    codigo: int,
    session: AsyncSession = Depends(get_session),
):
    sql = text("""
        SELECT codigo, nome, sigla, pais_codigo
        FROM ibge_estados
        WHERE codigo = :codigo
    """)
    result = await session.execute(sql, {"codigo": codigo})
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail={"code": "1", "message": "Estado não encontrado"})

    return {
        "code": "0",
        "data": EstadoItem(codigo=row.codigo, nome=row.nome, sigla=row.sigla, pais_codigo=row.pais_codigo),
    }
