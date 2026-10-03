from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, ConfigDict

import asyncio
import json
import os
import redis
import secrets

from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from celery.result import AsyncResult

from task import fatorial, somar
from celery_app import celery_app
from kafka_producer import enviar_evento



from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session

import asyncio

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()

print("USERNAME:", repr(os.getenv("APP_USERNAME")))
print("PASSWORD:", repr(os.getenv("APP_PASSWORD")))
print("DATABASE_URL:", repr(os.getenv("DATABASE_URL")))

DATABASE_URL = os.getenv("DATABASE_URL")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(
    title="API de Tarefas",
    description="API para gerenciar tarefas",
    version="1.0.0",
    contact={
        "name": "Nicole Zimmermann  ",
        "email": "nickfala71@gmail.com"
        })
    
    

# Auth básica
security = HTTPBasic()
USERNAME = os.getenv("APP_USERNAME")
PASSWORD = os.getenv("APP_PASSWORD")


def autenticar_usuario(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, USERNAME)
    correct_password = secrets.compare_digest(credentials.password, PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(status_code=401, detail="Usuario não autorizado! Credenciais inválidas",
        headers={"WWW-Authenticate": "Basic"}
        )
    return credentials

tarefas = {}

@app.get("/")
def hello_world():
    return {"Hello": "World"}

@app.post("/calcular/soma")
def calcular_soma(a:int, b:int):
    tarefa = somar.delay(a,b)
    redis_client.lpush("tarefas_ids", tarefa.id)
    redis_client.ltrim("tarefas_ids", 0, 49)
    return{
        "task_id": tarefa.id,
        "message": "Tarefa de soma enviada para execução!"
    }

@app.post("/calcular/fatorial")
def calcular_fatorial(n:int):
    tarefa = fatorial.delay(n)
    redis_client.lpush("tarefas_ids", tarefa.id)
    redis_client.ltrim("tarefas_ids", 0, 49)
    return{
        "task_id": tarefa.id,
        "message": "Tarefa de fatorial enviada para execução!"
    }
@app.get("/tarefas/recentes")
def tarefas_recentes():
    ids = redis_client.lrange("tarefas_ids", 0, -1)
    tarefas = []

    for task_id in ids:
        resultado = AsyncResult(task_id, app=celery_app)
        tarefas.append({
            "task_id": task_id,
            "status": resultado.status,
            "resultado": resultado.result if resultado.successful() else None
        })
    return {"tarefas": tarefas}


@app.get("/debug/redis")
def ver_tarefas_redis():
    chaves= redis_client.keys("tarefa:*")
    tarefas= []

    for chave in chaves:
        valor = redis_client.get(chave)
        ttl = redis_client.ttl(chave)
        
        tarefas.append({"chave": chave, "valor": json.loads(valor), "ttl": ttl})

    return {"tarefas": tarefas}

async def chamadas_externas_1():
    await asyncio.sleep(2)
    return "Resultado da chamada externa 1"

async def chamadas_externas_2():
    await asyncio.sleep(2)
    return "Resultado da chamada externa 2"

async def chamadas_externas_3():
    await asyncio.sleep(2)
    return "Resultado da chamada externa 3"

@app.get("/chamadas-externas")
async def chamadas_externas():  
    tarefa1 = asyncio.create_task(chamadas_externas_1())
    tarefa2 = asyncio.create_task(chamadas_externas_2())
    tarefa3 = asyncio.create_task(chamadas_externas_3())

    resultado1 = await tarefa1
    resultado2 = await tarefa2
    resultado3 = await tarefa3

    return {
       "mensagem": "Todas as chamadas nas API's externas foram concluídas com sucesso",
         "resultados": [resultado1, resultado2, resultado3]
       }
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

def salvar_tarefa_redis(tarefa_id: int, tarefa: dict):
    redis_client.set(f"tarefa:{tarefa_id}", json.dumps(tarefa))

def deletar_tarefa_redis(tarefa_id: int):
    redis_client.delete(f"tarefa:{tarefa_id}")

# Dependência DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/tarefas")
def get_tarefas(
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db),
    user: str = Depends(autenticar_usuario)
):
    if page < 1 or limit < 1:
        raise HTTPException(
            status_code=400,
            detail="Page ou limit estão com valores inválidos"
        )

    cache_key = f"tarefas:page:{page}:limit:{limit}"

    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    tarefas = (
        db.query(TarefaDB)
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    total_tarefas = db.query(TarefaDB).count()

    resposta = {
        "page": page,
        "limit": limit,
        "total": total_tarefas,
        "tarefas": [
            {
                "id": tarefa.id,
                "nome_tarefa": tarefa.nome_tarefa,
                "descricao": tarefa.descricao_tarefa,
                "concluida": tarefa.concluida_tarefa,
            }
            for tarefa in tarefas
        ],
    }

    redis_client.set(cache_key, json.dumps(resposta), ex=30)

    return resposta


@app.post("/tarefas", response_model=TarefaRead)
async def criar_tarefa(
    tarefa: TarefaCreate,
    db: Session = Depends(get_db),
    user: str = Depends(autenticar_usuario),
):
    db_tarefa = TarefaDB(**tarefa.dict())

    db.add(db_tarefa)
    db.commit()
    db.refresh(db_tarefa)

    tarefa_dict = {
        "id": db_tarefa.id,
        "nome_tarefa": db_tarefa.nome_tarefa,
        "descricao_tarefa": db_tarefa.descricao_tarefa,
        "concluida_tarefa": db_tarefa.concluida_tarefa,
    }

    salvar_tarefa_redis(db_tarefa.id, tarefa_dict)

    enviar_evento(
        "tarefas",
        {
            "acao": "criar_tarefa",
            "tarefa": tarefa_dict,
        },
    )

    return db_tarefa


@app.delete("/tarefas/{tarefa_id}")
async def deletar_tarefa(
    tarefa_id: int,
    db: Session = Depends(get_db),
    user: str = Depends(autenticar_usuario),
):
    tarefa = db.query(TarefaDB).filter(TarefaDB.id == tarefa_id).first()

    if not tarefa:
        raise HTTPException(
            status_code=404,
            detail="Tarefa não encontrada"
        )

    db.delete(tarefa)
    db.commit()

    deletar_tarefa_redis(tarefa_id)

    return {"mensagem": "Tarefa deletada"}