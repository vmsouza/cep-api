from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.schemas import (
    CidadeItem,
    CidadeResponse,
    CidadeSearchRequest,
    CidadeSearchResponse,
    ErrorResponse,
)

router = APIRouter(prefix="/cidades", tags=["Cidades"])


@router.post("/search", response_model=CidadeSearchResponse)
async def search_cidades(
    body: CidadeSearchRequest,
    session: AsyncSession = Depends(get_session),
):
    q = body.q.strip()
    limit = body.limit

    if len(q) < 3:
        return CidadeSearchResponse(data=[])

    sql = text("""
        SELECT
            ic.codigo,
            ic.nome,
            ie.sigla AS uf_sigla,
            ie.nome AS estado_nome
        FROM ibge_cidades ic
        JOIN ibge_estados ie ON ie.codigo = ic.estado_codigo
        WHERE ic.nome_busca LIKE lower(unaccent(:q)) || '%'
        ORDER BY ic.nome
        LIMIT :lim
    """)
    result = await session.execute(sql, {"q": q, "lim": limit})
    rows = result.fetchall()

    data = [
        CidadeItem(
            codigo=row.codigo,
            nome=row.nome,
            estado={"sigla": row.uf_sigla, "nome": row.estado_nome},
            display=f"{row.nome} / {row.uf_sigla}",
        )
        for row in rows
    ]

    return CidadeSearchResponse(data=data)


@router.get("/{codigo}", response_model=CidadeResponse, responses={404: {"model": ErrorResponse}})
async def get_cidade(
    codigo: int,
    session: AsyncSession = Depends(get_session),
):
    sql = text("""
        SELECT
            ic.codigo,
            ic.nome,
            ie.sigla AS uf_sigla,
            ie.nome AS estado_nome
        FROM ibge_cidades ic
        JOIN ibge_estados ie ON ie.codigo = ic.estado_codigo
        WHERE ic.codigo = :codigo
    """)
    result = await session.execute(sql, {"codigo": codigo})
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail={"code": "1", "message": "Cidade não encontrada"})

    return CidadeResponse(
        data=CidadeItem(
            codigo=row.codigo,
            nome=row.nome,
            estado={"sigla": row.uf_sigla, "nome": row.estado_nome},
            display=f"{row.nome} / {row.uf_sigla}",
        )
    )
