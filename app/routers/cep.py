import re

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.schemas import CepItem, CepSearchRequest, CepSearchResponse, ErrorResponse

router = APIRouter(prefix="/cep", tags=["CEP"])


def _format_cep_like(cep: str) -> str:
    cep = re.sub(r"\D", "", cep)
    if len(cep) <= 5:
        return cep
    return cep[:5] + "-" + cep[5:]


@router.post("/search", response_model=CepSearchResponse)
async def search_cep(
    body: CepSearchRequest,
    session: AsyncSession = Depends(get_session),
):
    q_original = body.q.strip()
    q_numeric = re.sub(r"\D", "", q_original)
    q_texto = q_original.lower()
    limit = body.limit

    if len(q_original) < 3:
        return CepSearchResponse(data=[])

    if q_numeric:
        cep_busca = _format_cep_like(q_numeric)
        sql = text("""
            SELECT
                c.cep,
                COALESCE(NULLIF(tl.sigla, ''), tl.nome) AS tipo_logradouro,
                c.logradouro,
                c.bairro,
                c.cidade_codigo,
                ic.nome AS cidade_nome,
                ie.sigla AS uf_sigla
            FROM correios_ceps c
            LEFT JOIN tipos_logradouros tl ON tl.codigo = c.tipo_logradouro_codigo
            JOIN ibge_cidades ic ON ic.codigo = c.cidade_codigo
            JOIN ibge_estados ie ON ie.codigo = c.uf_codigo
            WHERE c.cep LIKE :cep_prefix
            ORDER BY c.logradouro
            LIMIT :lim
        """)
        result = await session.execute(sql, {"cep_prefix": cep_busca + "%", "lim": limit})
    else:
        sql = text("""
            SELECT
                c.cep,
                COALESCE(NULLIF(tl.sigla, ''), tl.nome) AS tipo_logradouro,
                c.logradouro,
                c.bairro,
                c.cidade_codigo,
                ic.nome AS cidade_nome,
                ie.sigla AS uf_sigla
            FROM correios_ceps c
            LEFT JOIN tipos_logradouros tl ON tl.codigo = c.tipo_logradouro_codigo
            JOIN ibge_cidades ic ON ic.codigo = c.cidade_codigo
            JOIN ibge_estados ie ON ie.codigo = c.uf_codigo
            WHERE c.logradouro_busca LIKE :q_texto
            ORDER BY c.logradouro
            LIMIT :lim
        """)
        result = await session.execute(sql, {"q_texto": f"%{q_texto}%", "lim": limit})

    rows = result.fetchall()
    data = []
    for row in rows:
        tipo = row.tipo_logradouro or ""
        logradouro = row.logradouro or ""
        logradouro_completo = (tipo + " " + logradouro).strip()
        data.append(
            CepItem(
                cep=row.cep,
                logradouro=logradouro_completo,
                bairro=row.bairro,
                cidade_codigo=row.cidade_codigo,
                cidade=row.cidade_nome,
                uf=row.uf_sigla,
                display=f"{row.cep} - {logradouro_completo} - {row.bairro} - {row.cidade_nome} - {row.uf_sigla}",
            )
        )

    return CepSearchResponse(data=data)


@router.get("/{cep}", response_model=CepSearchResponse, responses={404: {"model": ErrorResponse}})
async def get_cep(
    cep: str,
    session: AsyncSession = Depends(get_session),
):
    cep_clean = re.sub(r"\D", "", cep)
    if len(cep_clean) == 8:
        cep_formatado = cep_clean[:5] + "-" + cep_clean[5:]
    else:
        cep_formatado = cep

    sql = text("""
        SELECT
            c.cep,
            COALESCE(NULLIF(tl.sigla, ''), tl.nome) AS tipo_logradouro,
            c.logradouro,
            c.bairro,
            c.cidade_codigo,
            ic.nome AS cidade_nome,
            ie.sigla AS uf_sigla
        FROM correios_ceps c
        LEFT JOIN tipos_logradouros tl ON tl.codigo = c.tipo_logradouro_codigo
        JOIN ibge_cidades ic ON ic.codigo = c.cidade_codigo
        JOIN ibge_estados ie ON ie.codigo = c.uf_codigo
        WHERE c.cep = :cep
        LIMIT 1
    """)
    result = await session.execute(sql, {"cep": cep_formatado})
    row = result.fetchone()

    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail={"code": "1", "message": "CEP não encontrado"})

    tipo = row.tipo_logradouro or ""
    logradouro = row.logradouro or ""
    logradouro_completo = (tipo + " " + logradouro).strip()
    item = CepItem(
        cep=row.cep,
        logradouro=logradouro_completo,
        bairro=row.bairro,
        cidade_codigo=row.cidade_codigo,
        cidade=row.cidade_nome,
        uf=row.uf_sigla,
        display=f"{row.cep} - {logradouro_completo} - {row.bairro} - {row.cidade_nome} - {row.uf_sigla}",
    )
    return CepSearchResponse(data=[item])
