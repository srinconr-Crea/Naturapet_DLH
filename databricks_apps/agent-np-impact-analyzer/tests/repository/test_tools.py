import json

import pytest
from agents import RunContextWrapper

from agent_server.config import RepositoryConfig
from agent_server.repository.errors import RepositoryAccessError, RepositoryErrorCode
from agent_server.repository.tools import (
    AnalysisRunContext,
    REPOSITORY_TOOLS,
    get_repository_context,
    list_repository_tree,
    read_repository_file,
    safe_tool_error,
    search_repository_text,
    search_text,
)
from agent_server.schemas import (
    RepositoryContext,
    RepositoryEntry,
    RepositoryFile,
    RepositoryTreeResult,
    SearchResult,
)


class FakeRepositoryGateway:
    def __init__(
        self,
        entries: list[RepositoryEntry] | None = None,
        contents: dict[str, str] | None = None,
        tree_limit_reached: bool = False,
    ):
        self.entries = entries or [
            RepositoryEntry(
                relative_path="notebooks/comercial/silver/04_business_derivations.ipynb",
                object_type="FILE",
                size_bytes=80,
            )
        ]
        self.contents = contents or {
            "notebooks/comercial/silver/04_business_derivations.ipynb": (
                "venta_neta = total - descuento\nmargen_pct = margen / venta_neta\n"
            )
        }
        self.read_paths: list[str] = []
        self.tree_limit_reached = tree_limit_reached

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
    ) -> RepositoryTreeResult:
        return RepositoryTreeResult(
            entries=self.entries, limit_reached=self.tree_limit_reached
        )

    def read_file(self, relative_path: str) -> RepositoryFile:
        self.read_paths.append(relative_path)
        return RepositoryFile(
            relative_path=relative_path,
            content=self.contents[relative_path],
            size_bytes=len(self.contents[relative_path]),
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
    fake_gateway.contents[next(iter(fake_gateway.contents))] = (
        "silver one\nsilver two\n"
    )

    result = search_text(
        fake_gateway,
        config.model_copy(update={"max_results": 1}),
        "silver",
        "",
    )

    assert result.limit_reached is True
    assert "SEARCH_LIMIT_REACHED" in result.warnings


def test_search_does_not_report_global_limit_when_result_count_is_exact(
    fake_gateway, config
):
    result = search_text(
        fake_gateway,
        config.model_copy(update={"max_results": 1}),
        "margen_pct",
    )

    assert len(result.matches) == 1
    assert result.limit_reached is False
    assert result.warnings == []


def test_search_reports_file_scan_limit_only_when_extra_files_exist(config):
    gateway = FakeRepositoryGateway(
        entries=[RepositoryEntry(relative_path="first.py", object_type="FILE")],
        contents={"first.py": "needle\n", "second.py": "needle\n"},
        tree_limit_reached=True,
    )

    result = search_text(
        gateway, config.model_copy(update={"max_files": 1}), "needle"
    )

    assert len(result.matches) == 1
    assert result.files_scanned == 1
    assert gateway.read_paths == ["first.py"]
    assert result.limit_reached is True
    assert "SEARCH_LIMIT_REACHED" in result.warnings


def test_search_stops_reading_after_reaching_global_limit(config):
    gateway = FakeRepositoryGateway(
        entries=[
            RepositoryEntry(relative_path="first.py", object_type="FILE"),
            RepositoryEntry(relative_path="second.py", object_type="FILE"),
        ],
        contents={
            "first.py": "needle one\nneedle two\n",
            "second.py": "needle three\n",
        },
    )

    result = search_text(
        gateway,
        config.model_copy(update={"max_results": 1, "max_results_per_file": 1}),
        "needle",
    )

    assert len(result.matches) == 1
    assert gateway.read_paths == ["first.py"]
    assert result.limit_reached is True


def test_search_does_not_report_file_scan_limit_without_extra_files(config):
    gateway = FakeRepositoryGateway(
        entries=[RepositoryEntry(relative_path="only.py", object_type="FILE")],
        contents={"only.py": "needle\n"},
    )

    result = search_text(
        gateway, config.model_copy(update={"max_files": 1}), "needle"
    )

    assert result.limit_reached is False
    assert result.warnings == []


def test_search_reports_per_file_limit_only_when_additional_matches_exist(config):
    gateway = FakeRepositoryGateway(
        entries=[RepositoryEntry(relative_path="module.py", object_type="FILE")],
        contents={"module.py": "needle one\nneedle two\nneedle three\n"},
    )

    result = search_text(
        gateway, config.model_copy(update={"max_results_per_file": 2}), "needle"
    )

    assert len(result.matches) == 2
    assert result.limit_reached is True
    assert "SEARCH_LIMIT_REACHED" in result.warnings
    assert len(result.matches) <= 2


def test_search_never_creates_more_than_the_per_file_limit(config):
    gateway = FakeRepositoryGateway(
        entries=[RepositoryEntry(relative_path="needle.py", object_type="FILE")],
        contents={"needle.py": "needle in content\n"},
    )

    result = search_text(
        gateway, config.model_copy(update={"max_results_per_file": 0}), "needle"
    )

    assert result.matches == []
    assert result.limit_reached is True


def test_search_does_not_report_per_file_limit_when_matches_are_exact(config):
    gateway = FakeRepositoryGateway(
        entries=[RepositoryEntry(relative_path="module.py", object_type="FILE")],
        contents={"module.py": "needle one\nneedle two\n"},
    )

    result = search_text(
        gateway, config.model_copy(update={"max_results_per_file": 2}), "needle"
    )

    assert len(result.matches) == 2
    assert result.limit_reached is False
    assert result.warnings == []


def test_search_truncates_evidence_excerpts(config):
    gateway = FakeRepositoryGateway(
        entries=[RepositoryEntry(relative_path="module.py", object_type="FILE")],
        contents={"module.py": "needle-with-a-long-excerpt\n"},
    )

    result = search_text(
        gateway, config.model_copy(update={"max_excerpt_chars": 8}), "needle"
    )

    assert result.matches[0].excerpt == "needle-w"
    assert len(result.matches[0].excerpt) == 8


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


def test_tool_wrappers_use_the_run_context_and_return_json(fake_gateway, config):
    wrapper = RunContextWrapper(
        context=AnalysisRunContext(repository=fake_gateway, config=config)
    )

    context = json.loads(get_repository_context.__wrapped__(wrapper))
    tree = json.loads(list_repository_tree.__wrapped__(wrapper))
    repository_file = json.loads(
        read_repository_file.__wrapped__(
            wrapper, "notebooks/comercial/silver/04_business_derivations.ipynb"
        )
    )
    search = json.loads(search_repository_text.__wrapped__(wrapper, "margen_pct"))

    assert context["repo_id"] == config.repo_id
    assert tree["entries"][0]["relative_path"].endswith("04_business_derivations.ipynb")
    assert tree["limit_reached"] is False
    assert repository_file["content"].startswith("venta_neta")
    assert search["matches"][0]["line_number"] == 2


def test_tool_result_schemas_and_safe_errors_are_sdk_serializable(
    fake_gateway, config
):
    tree = fake_gateway.list_tree().model_dump_json()
    search = SearchResult.model_validate(
        {
            "query": "margen_pct",
            "matches": [
                {
                    "relative_path": "notebooks/comercial/silver/04_business_derivations.ipynb",
                    "line_number": 2,
                    "excerpt": "margen_pct",
                }
            ],
            "files_scanned": 1,
        }
    ).model_dump_json()
    wrapper = RunContextWrapper(
        context=AnalysisRunContext(repository=fake_gateway, config=config)
    )
    guarded = safe_tool_error(
        wrapper,
        RepositoryAccessError(
            RepositoryErrorCode.PATH_NOT_ALLOWED, "safe path error"
        ),
    )
    generic = safe_tool_error(wrapper, RuntimeError("token=do-not-expose"))

    assert json.loads(tree)["entries"][0]["object_type"] == "FILE"
    assert json.loads(search)["query"] == "margen_pct"
    assert json.loads(guarded) == {
        "error": {"code": "PATH_NOT_ALLOWED", "message": "safe path error"}
    }
    assert json.loads(generic) == {
        "error": {
            "code": "DATABRICKS_READ_ERROR",
            "message": "No fue posible completar la lectura solicitada.",
        }
    }
