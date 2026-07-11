from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class IbgePaises(Base):
    __tablename__ = "ibge_paises"

    codigo = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)
    sigla = Column(String(3), nullable=True)


class IbgeEstados(Base):
    __tablename__ = "ibge_estados"

    codigo = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)
    sigla = Column(String(2), nullable=True)
    pais_codigo = Column(Integer, ForeignKey("ibge_paises.codigo"), nullable=False)

    pais = relationship("IbgePaises", backref="estados")


class IbgeCidades(Base):
    __tablename__ = "ibge_cidades"

    codigo = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)
    estado_codigo = Column(Integer, ForeignKey("ibge_estados.codigo"), nullable=False)
    codigocorreios = Column(Integer, nullable=True)

    estado = relationship("IbgeEstados", backref="cidades")


class TiposLogradouros(Base):
    __tablename__ = "tipos_logradouros"

    codigo = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=True)
    sigla = Column(String, nullable=True)


class CorreiosCeps(Base):
    __tablename__ = "correios_ceps"

    cep = Column(String(9), primary_key=True)
    tipo_logradouro_codigo = Column(Integer, ForeignKey("tipos_logradouros.codigo"), nullable=True)
    logradouro = Column(String, nullable=True)
    numero = Column(Integer, nullable=True)
    complemento = Column(String, nullable=True)
    bairro = Column(String, nullable=True)
    cidade_codigo = Column(Integer, ForeignKey("ibge_cidades.codigo"), nullable=True)
    uf_codigo = Column(Integer, ForeignKey("ibge_estados.codigo"), nullable=True)
    pais_codigo = Column(Integer, ForeignKey("ibge_paises.codigo"), nullable=True)

    tipo_logradouro = relationship("TiposLogradouros")
    cidade = relationship("IbgeCidades")
    estado = relationship("IbgeEstados")
    pais = relationship("IbgePaises")


class ClienteApi(Base):
    __tablename__ = "clientes_api"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)
    api_key = Column(String, unique=True, nullable=False, index=True)
    ativo = Column(Integer, default=1)
