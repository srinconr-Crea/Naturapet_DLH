import pytest

from agent_server.config import RepositoryConfig
from agent_server.repository.tools import REPOSITORY_TOOLS, search_text
from agent_server.schemas import RepositoryContext, RepositoryEntry, RepositoryFile


class FakeRepositoryGateway:
    def get_context(self) -> RepositoryContext:
        return RepositoryContext(
            repo_id=1393361128272538,
            path="/Workspace/Naturapet_BI/practica-margen-silver",
            url="https://github.com/srinconr-Crea/Naturapet_DLH.git",
            provider="gitHub",
            branch="practica-margen-silver",
            head_commit_id="9c48831022a329902f765058de37e6d0a1528eb7",
        )

    def list_tree(
        self, relative_path: str = "", max_depth: int | None = None
    ) -> list[RepositoryEntry]:
        return [
            RepositoryEntry(
                relative_path="notebooks/comercial/silver/04_business_derivations.ipynb",
                object_type="FILE",
                size_bytes=80,
            )
        ]

    def read_file(self, relative_path: str) -> RepositoryFile:
        return RepositoryFile(
            relative_path=relative_path,
            content="venta_neta = total - descuento\nmargen_pct = margen / venta_neta\n",
            size_bytes=67,
        )


@pytest.fixture
def fake_gateway() -> FakeRepositoryGateway:
    return FakeRepositoryGateway()


def test_search_returns_bounded_line_evidence(fake_gateway, config):
    matches = search_text(fake_gateway, config, "margen_pct", "")

    assert len(matches.matches) <= config.max_results
    assert matches.matches[0].relative_path.endswith("04_business_derivations.ipynb")
    assert matches.matches[0].line_number >= 1


def test_search_reports_limit(fake_gateway, config):
    result = search_text(
        fake_gateway,
        config.model_copy(update={"max_results": 1}),
        "silver",
        "",
    )

    assert result.limit_reached is True
    assert "SEARCH_LIMIT_REACHED" in result.warnings


def test_search_rejects_empty_and_oversized_queries(fake_gateway, config):
    with pytest.raises(ValueError, match="query"):
        search_text(fake_gateway, config, "", "")
    with pytest.raises(ValueError, match="200"):
        search_text(fake_gateway, config, "x" * 201, "")


def test_agent_exports_exact_tool_names():
    assert {tool.name for tool in REPOSITORY_TOOLS} == {
        "get_repository_context",
        "list_repository_tree",
        "read_repository_file",
        "search_repository_text",
    }
