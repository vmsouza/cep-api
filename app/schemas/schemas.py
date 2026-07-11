from pydantic import BaseModel


class CepSearchRequest(BaseModel):
    q: str
    limit: int = 30


class CepItem(BaseModel):
    cep: str
    logradouro: str | None = None
    bairro: str | None = None
    cidade_codigo: int | None = None
    cidade: str | None = None
    uf: str | None = None
    display: str | None = None


class CepSearchResponse(BaseModel):
    data: list[CepItem]


class CidadeItem(BaseModel):
    codigo: int
    nome: str
    estado: dict | None = None
    display: str | None = None


class CidadeSearchRequest(BaseModel):
    q: str
    limit: int = 30


class CidadeSearchResponse(BaseModel):
    code: str = "0"
    data: list[CidadeItem]


class CidadeResponse(BaseModel):
    code: str = "0"
    data: CidadeItem | None = None


class EstadoItem(BaseModel):
    codigo: int
    nome: str
    sigla: str | None = None
    pais_codigo: int | None = None


class PaisItem(BaseModel):
    codigo: int
    nome: str
    sigla: str | None = None


class ErrorResponse(BaseModel):
    code: str = "1"
    message: str
    errors: str | None = None
