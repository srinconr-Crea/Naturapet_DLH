from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from agent_server.config import RepositoryConfig


@pytest.fixture
def config() -> RepositoryConfig:
    return RepositoryConfig()


@pytest.fixture
def fake_workspace_client():
    client = MagicMock()
    client.repos.get.return_value = SimpleNamespace(
        id=1393361128272538,
        path="/Naturapet_BI/practica-margen-silver",
        url="https://github.com/srinconr-Crea/Naturapet_DLH.git",
        provider="gitHub",
        branch="practica-margen-silver",
        head_commit_id="9c48831022a329902f765058de37e6d0a1528eb7",
    )
    client.workspace.get_status.return_value = SimpleNamespace(size=18, object_type="FILE")
    client.workspace.download.return_value = BytesIO(b"# Naturapet_DLH\n")
    client.workspace.list.return_value = []
    return client
