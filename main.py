from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, ConfigDict
import secrets

from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session

DATABASE_URL = "sqlite:///./tarefas.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(
    title="API de Tarefas",
    description="API para gerenciar tarefas",
    version="1.0.0"
)

# Auth básica
USERNAME = "admin"
PASSWORD = "admin123"
security = HTTPBasic()

def verificar_usuario(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, USERNAME)
    correct_password = secrets.compare_digest(credentials.password, PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    return credentials.username

# Banco
class TarefaDB(Base):
    __tablename__ = "tarefas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True, nullable=False)
    descricao = Column(String, nullable=False)
    concluida = Column(Boolean, default=False)

# Schemas
class TarefaCreate(BaseModel):
    nome: str
    descricao: str
    concluida: bool = False

class TarefaRead(BaseModel):
    id: int
    nome: str
    descricao: str
    concluida: bool

    model_config = ConfigDict(from_attributes=True)

Base.metadata.create_all(bind=engine)

# Dependência DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Rotas
@app.post("/tarefas", response_model=TarefaRead)
def criar_tarefa(tarefa: TarefaCreate, db: Session = Depends(get_db), user: str = Depends(verificar_usuario)):
    db_tarefa = TarefaDB(**tarefa.dict())
    db.add(db_tarefa)
    db.commit()
    db.refresh(db_tarefa)
    return db_tarefa

@app.get("/tarefas", response_model=list[TarefaRead])
def listar_tarefas(db: Session = Depends(get_db), user: str = Depends(verificar_usuario)):
    return db.query(TarefaDB).all()

@app.delete("/tarefas/{tarefa_id}")
def deletar_tarefa(tarefa_id: int, db: Session = Depends(get_db), user: str = Depends(verificar_usuario)):
    tarefa = db.query(TarefaDB).filter(TarefaDB.id == tarefa_id).first()
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    db.delete(tarefa)
    db.commit()
    return {"msg": "Tarefa deletada"}