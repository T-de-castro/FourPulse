from sqlalchemy import Column, ForeignKey, Integer, String

from app.database import Base


class ClienteConta(Base):
    __tablename__ = "cliente_contas"

    id_conta = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(
        Integer,
        ForeignKey("clientes.id_cliente", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    email = Column(String(150), nullable=False, unique=True, index=True)
    senha_hash = Column(String, nullable=False)
