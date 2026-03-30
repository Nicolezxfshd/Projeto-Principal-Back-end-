from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import secrets

from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session

DATABASE_URL = "sqlite:///./tarefas.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(
    title="API de Tarefas",
    description="API para gerenciar tarefas com autenticação básica, paginação e ordenação.",
    version="1.0.0",
    contact={
        "name": "Nicole",
        "email": "nicole@example.com"
    }
)

Username = "admin"
Password = "admin123"
security = HTTPBasic()

class TarefaDB(Base):
    __tablename__ = "tarefas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True, nullable=False)
    descricao = Column(String, nullable=False)
    concluida = Column(Boolean, default=False)


class TarefaCreate(BaseModel):
    nome: str
    descricao: str
    concluida: bool = False


class TarefaRead(BaseModel):
    id: int
    nome: str
    descricao: str
    concluida: bool

    class Config:
        orm_mode = True


Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#Essa função tem a responsabilidade de autenticar o usuário e a senha.

def autenticar_usuario(credentials: HTTPBasicCredentials = Depends(security)):
    is_username_correct = secrets.compare_digest(credentials.username, Username)
    is_password_correct = secrets.compare_digest(credentials.password, Password)
    if not (is_username_correct and is_password_correct):
        raise HTTPException(
            status_code=401, 
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Basic"})
    return credentials


@app.get("/")

def hello_world():
    return {"message": "Bem-vindo à API de Tarefas!"}

@app.get("/tarefas")

def get_tarefas(page: int = 1, limit: int = 10, db: Session = Depends(get_db), credentials: HTTPBasicCredentials = Depends(autenticar_usuario)):
    if page < 1 or limit < 1:
        raise HTTPException(status_code=400, detail="Page e limit devem ser maiores que 0")
    
    tarefas = db.query(TarefaDB).offset((page - 1) * limit).limit(limit).all()

    total_tarefas = db.query(TarefaDB).count()

    return {
        "page": page,
        "limit": limit,
        "total": total_tarefas,
        "tarefas": [{"id": tarefa.id, "nome": tarefa.nome, "descricao": tarefa.descricao, "concluida": tarefa.concluida} for tarefa in tarefas]
    }


@app.get("/tarefas/{id_tarefa}", response_model=TarefaRead)
def get_tarefa(id_tarefa: int, db: Session = Depends(get_db), credentials: HTTPBasicCredentials = Depends(autenticar_usuario)):
    tarefa_db = db.query(TarefaDB).filter(TarefaDB.id == id_tarefa).first()
    if not tarefa_db:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return tarefa_db


@app.post("/adicionar")
def adicionar_tarefa(tarefa: TarefaCreate, db: Session = Depends(get_db), credentials: HTTPBasicCredentials = Depends(autenticar_usuario)):
    tarefa_existente = db.query(TarefaDB).filter(TarefaDB.nome == tarefa.nome).first()

    if tarefa_existente:
        raise HTTPException(status_code=400, detail="Já existe uma tarefa com esse nome")

    nova_tarefa = TarefaDB(
        nome=tarefa.nome,
        descricao=tarefa.descricao,
        concluida=tarefa.concluida
    )
    db.add(nova_tarefa)
    db.commit()
    db.refresh(nova_tarefa)

    return {
        "mensagem": "Tarefa adicionada com sucesso!",
        "tarefa": {
            "id": nova_tarefa.id,
            "nome": nova_tarefa.nome,
            "descricao": nova_tarefa.descricao,
            "concluida": nova_tarefa.concluida
        }
    }


@app.put("/tarefas/{id_tarefa}")
def atualizar_tarefa(
    id_tarefa: int,
    tarefa: TarefaCreate,
    credentials: HTTPBasicCredentials = Depends(autenticar_usuario),
    db: Session = Depends(get_db)
):
    tarefa_db = db.query(TarefaDB).filter(TarefaDB.id == id_tarefa).first()
    if not tarefa_db:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    tarefa_db.nome = tarefa.nome
    tarefa_db.descricao = tarefa.descricao
    tarefa_db.concluida = tarefa.concluida
    db.commit()
    db.refresh(tarefa_db)

    return {"mensagem": "Tarefa atualizada com sucesso!"}


@app.delete("/tarefas/{id_tarefa}")
def deletar_tarefa(
    id_tarefa: int,
    credentials: HTTPBasicCredentials = Depends(autenticar_usuario),
    db: Session = Depends(get_db)
):
    tarefa_db = db.query(TarefaDB).filter(TarefaDB.id == id_tarefa).first()
    if not tarefa_db:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    db.delete(tarefa_db)
    db.commit()

    return {"mensagem": "Tarefa deletada com sucesso!"}
