from fastapi.testclient import TestClient
from main import app
import os
import pytest

client = TestClient(app)

os.environ["APP_USERNAME"] = "admin"
os.environ["APP_PASSWORD"] = "admin123"

@pytest.fixture(autouse=True)
def mock_redis(mocker):
  mock_redis_client = mocker.patch("main.redis_client")
  mock_redis_client.get.return_value = None

def test_autenticacao_usuario_com_sucesso():
    response = client.get(
        "/tarefas",
        auth=("admin", "admin123")
    )
    assert response.status_code == 200

def test_autenticacao_usuario_com_falha():
    response = client.get(
        "/tarefas",
        auth=("usuario_incorreto", "admin123")
    )
    assert response.status_code == 401
    assert response.json()["detail"] ==  "Usuario não autorizado! Credenciais inválidas"

def test_autenticacao_senha_com_falha():
    response = client.get(
        "/tarefas",
        auth=("admin", "senha_incorreta")
    )
    assert response.status_code == 401
    assert response.json()["detail"] ==  "Usuario não autorizado! Credenciais inválidas"