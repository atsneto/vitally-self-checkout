from sqlalchemy import Column, Integer, String, Date, Time, Text, ForeignKey
from database import Base

class Pessoa(Base):
    __tablename__ = 'pessoa'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    cpf = Column(String(14), unique=True, nullable=False)
    data_nascimento = Column(Date, nullable=False)
    sexo = Column(String(1), nullable=False)
    carteira = Column(String(15), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'pessoa'
    }

class Paciente(Pessoa):
    __tablename__ = 'paciente'

    id = Column(Integer, ForeignKey('pessoa.id'), primary_key=True)
    description = Column(Text, nullable=True)
    risk_level = Column(String(20), nullable=True)
    data_consulta = Column(Date, nullable=True)
    hora_consulta = Column(Time, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'paciente',
    }

class Sintoma(Base):
    __tablename__ = "sintomas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    grau_risco = Column(Integer, nullable=False)  # 1 a 3 (1=baixo, 2=médio, 3=alto)
