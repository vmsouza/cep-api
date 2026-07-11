from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.schemas import ErrorResponse, PaisItem

router = APIRouter(prefix="/paises", tags=["Países"])


@router.get("")
async def list_paises(
    session: AsyncSession = Depends(get_session),
):
    sql = text("""
        SELECT codigo, nome, sigla
        FROM ibge_paises
        ORDER BY nome
    """)
    result = await session.execute(sql)
    rows = result.fetchall()

    return {
        "code": "0",
        "data": [PaisItem(codigo=r.codigo, nome=r.nome, sigla=r.sigla) for r in rows],
    }


@router.get("/{codigo}", responses={404: {"model": ErrorResponse}})
async def get_pais(
    codigo: int,
    session: AsyncSession = Depends(get_session),
):
    sql = text("""
        SELECT codigo, nome, sigla
        FROM ibge_paises
        WHERE codigo = :codigo
    """)
    result = await session.execute(sql, {"codigo": codigo})
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail={"code": "1", "message": "País não encontrado"})

    return {
        "code": "0",
        "data": PaisItem(codigo=row.codigo, nome=row.nome, sigla=row.sigla),
    }
