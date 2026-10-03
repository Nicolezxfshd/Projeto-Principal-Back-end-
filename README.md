# API de Tarefas com FastAPI

API REST desenvolvida com Python utilizando FastAPI, SQLAlchemy e Docker para gerenciamento de tarefas.

## Tecnologias utilizadas

- Python 3.11
- FastAPI
- SQLAlchemy
- SQLite
- Docker
- Docker Compose

---

# Como executar o projeto

## 1. Clonar o repositório

```bash
git clone https://github.com/seuusuario/seurepositorio.git
```

## 2. Entrar na pasta do projeto

```bash
cd seurepositorio
```

## Configurar variáveis de ambiente

Copie o arquivo `.env.example` para `.env`:

```bash
cp .env.example .env
```

Depois preencha os valores no arquivo `.env`.

## 4. Construir e iniciar os containers

Execute o comando abaixo para construir a imagem e iniciar os containers em segundo plano:

```bash
docker-compose up --build -d
```

## 5. Acessar a aplicação

A API estará disponível em:

```txt
http://localhost:8000
```

Documentação Swagger:

```txt
http://localhost:8000/docs
```

## 6. Parar os containers

Para parar os containers execute:

```bash
docker-compose down
```

---

# Endpoints principais

## Criar tarefa

```http
POST /tarefas
```

## Listar tarefas

```http
GET /tarefas
```

## Deletar tarefa

```http
DELETE /tarefas/{id}
```

---

# Autenticação

A API utiliza autenticação HTTP Basic.

| Usuário | Senha |
|---|---|
| admin | 1234 |

---

# Estrutura do projeto

```bash
.
├── main.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env
```

---

# Autor

Nicole Zimmerman