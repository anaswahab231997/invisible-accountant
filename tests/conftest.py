import pytest
import os
import sys
from unittest.mock import patch, AsyncMock

os.environ["WEBHOOK_SECRET"] = "dummy_secret"
os.environ["API_KEY"] = "super-secret-key"
os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost/mockdb"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from fastapi.testclient import TestClient

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture
def mock_db_init():
    with patch("main.init_db", new_callable=AsyncMock) as mock_init, \
         patch("db.init_pool", new_callable=AsyncMock), \
         patch("db.close_pool", new_callable=AsyncMock):
        yield mock_init

@pytest.fixture
def test_client(mock_db_init):
    with patch("main.process_hmrc_queue", new_callable=AsyncMock), \
         patch("main.process_ttl_sweeper", new_callable=AsyncMock), \
         patch("main.intake_worker", new_callable=AsyncMock):
        with TestClient(app) as client:
            yield client
