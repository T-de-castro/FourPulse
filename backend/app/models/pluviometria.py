from sqlalchemy import Column, Date, Integer, Numeric, String

from app.database import Base


class Pluviometria(Base):
    __tablename__ = "pluviometria"

    id_medicao = Column(Integer, primary_key=True, index=True)
    estacao = Column(String(100), nullable=False, default="INMET - Concórdia/Oeste SC")
    data_medicao = Column(Date, nullable=False, index=True)
    hora = Column(String(5), nullable=True)
    precipitacao_mm = Column(Numeric(6, 2), nullable=False, default=0.00)
    temperatura_c = Column(Numeric(4, 1), nullable=True)
    umidade_pct = Column(Numeric(4, 1), nullable=True)
    nivel_alerta = Column(String(50), nullable=False, default="Normal")
    origem = Column(String(100), nullable=False, default="INMET / Defesa Civil SC")
