import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from main import app, Base, get_db

DATABASE_URL_TESTE = "sqlite:///./test_database.db"

engine = create_engine(
    DATABASE_URL_TESTE,
    connect_args={"check_same_thread": False}
)

TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_redis(mocker):
    mock = mocker.patch("main.redis_client")
    mock.get.return_value = None

@pytest.fixture(scope="function")
def db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_get_tarefas():
    response = client.get(
        "/tarefas",
        auth=("admin", "admin123")
    )

    assert response.status_code == 200

    data = response.json()

    assert "tarefas" in data
    assert "page" in data
    assert "limit" in data
    assert "total" in data

