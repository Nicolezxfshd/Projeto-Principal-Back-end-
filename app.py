
from fastapi import FastAPI

app = FastAPI()

tarefas = []

@app.post("/tarefas")
def adicionar_tarefa(tarefa: dict):

    nova_tarefa = {
        "nome": tarefa["nome"],
        "descricao": tarefa["descricao"],
        "concluida": False
    }

    tarefas.append(nova_tarefa)

    return {"mensagem": "Tarefa adicionada com sucesso!"}


@app.get("/tarefas")
def listar_tarefas():
    return tarefas


@app.put("/tarefas/{nome}")
def concluir_tarefa(nome: str):

    for tarefa in tarefas:
        if tarefa["nome"] == nome:
            tarefa["concluida"] = True
            return {"mensagem": "Tarefa marcada como concluída!"}

    return {"mensagem": "Tarefa não encontrada!"}


@app.delete("/tarefas/{nome}")
def remover_tarefa(nome: str):

    for tarefa in tarefas:
        if tarefa["nome"] == nome:
            tarefas.remove(tarefa)
            return {"mensagem": "Tarefa removida com sucesso!"}

    return {"mensagem": "Tarefa não encontrada!"}


