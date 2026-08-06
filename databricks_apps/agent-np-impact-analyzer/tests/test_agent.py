from types import SimpleNamespace

import pytest
from mlflow.types.responses import ResponsesAgentRequest

from agent_server.repository.errors import RepositoryAccessError, RepositoryErrorCode
from agent_server.schemas import (
    Decision,
    ImpactAnalysisDraft,
    ImpactAnalysisResult,
    RiskAssessment,
    RiskLevel,
)


EXPECTED_TOOL_NAMES = {
    "get_repository_context",
    "list_repository_tree",
    "read_repository_file",
    "search_repository_text",
}


@pytest.fixture(autouse=True)
def stub_databricks_auth(monkeypatch):
    """Allow import-time client setup without contacting Databricks in unit tests."""
    monkeypatch.setenv(
        "DATABRICKS_HOST", "https://adb-7405606739630987.7.azuredatabricks.net"
    )
    monkeypatch.setenv("DATABRICKS_TOKEN", "unit-test-token")
    monkeypatch.setenv("DATABRICKS_AUTH_TYPE", "pat")


@pytest.fixture
def analysis_request() -> ResponsesAgentRequest:
    return ResponsesAgentRequest(
        input=[{"role": "user", "content": "Analiza el impacto de margen_pct."}]
    )


@pytest.fixture
def analysis_draft() -> ImpactAnalysisDraft:
    return ImpactAnalysisDraft(
        request_summary="Analizar margen_pct.",
        decision=Decision.INSUFFICIENT_EVIDENCE,
        risk=RiskAssessment(level=RiskLevel.LOW, reasons=["No se leyó ningún archivo."]),
        target_files=[],
        related_files=[],
        evidence=[],
        implementation_plan=[],
        acceptance_criteria=[],
        prohibited_actions=["No modificar archivos."],
        assumptions=[],
        warnings=["Se requiere evidencia adicional."],
    )


def test_create_agent_is_np_impact_analyzer():
    from agent_server.agent import create_agent

    agent = create_agent()

    assert agent.name == "Naturapet Impact Analyzer"
    assert agent.model == "databricks-claude-sonnet-4-6"
    assert agent.output_type is ImpactAnalysisDraft
    assert {tool.name for tool in agent.tools} == EXPECTED_TOOL_NAMES


@pytest.mark.asyncio
async def test_invoke_returns_json_for_machine_and_markdown_for_human(
    monkeypatch, analysis_request, analysis_draft, fake_workspace_client
):
    import agent_server.agent as agent_module

    monkeypatch.setattr(agent_module, "WorkspaceClient", lambda: fake_workspace_client)

    async def fake_run(*_args, **_kwargs):
        return SimpleNamespace(final_output=analysis_draft.model_dump(mode="json"))

    monkeypatch.setattr(agent_module.Runner, "run", fake_run)

    response = await agent_module.invoke_handler(analysis_request)

    result = ImpactAnalysisResult.model_validate(response.custom_outputs["analysis"])
    assert response.output[0].content[0]["text"] == result.human_report_markdown
    assert response.output[0].content[0]["text"].startswith("# Análisis de impacto")


@pytest.mark.asyncio
async def test_runner_uses_app_identity_and_verified_context_before_model(
    monkeypatch, analysis_request, analysis_draft, fake_workspace_client
):
    import agent_server.agent as agent_module

    received = {}

    def workspace_client_factory(*args, **kwargs):
        received["workspace_client_args"] = args
        received["workspace_client_kwargs"] = kwargs
        return fake_workspace_client

    async def fake_run(*args, **kwargs):
        received["run_context"] = kwargs["context"]
        return SimpleNamespace(final_output=analysis_draft.model_dump(mode="json"))

    monkeypatch.setattr(agent_module, "WorkspaceClient", workspace_client_factory)
    monkeypatch.setattr(agent_module.Runner, "run", fake_run)

    result = await agent_module.run_analysis(analysis_request)

    assert received["workspace_client_args"] == ()
    assert received["workspace_client_kwargs"] == {}
    assert received["run_context"].repository.workspace_client is fake_workspace_client
    assert result.repository_context.repo_id == 1393361128272538
    fake_workspace_client.repos.get.assert_called_once_with(1393361128272538)


@pytest.mark.asyncio
async def test_stream_finishes_with_the_same_canonical_response(
    monkeypatch, analysis_request, analysis_draft, fake_workspace_client
):
    import agent_server.agent as agent_module

    monkeypatch.setattr(agent_module, "WorkspaceClient", lambda: fake_workspace_client)

    async def fake_run(*_args, **_kwargs):
        return SimpleNamespace(final_output=analysis_draft.model_dump(mode="json"))

    monkeypatch.setattr(agent_module.Runner, "run", fake_run)

    async def no_stream_events():
        if False:
            yield None

    monkeypatch.setattr(
        agent_module.Runner,
        "run_streamed",
        lambda *_args, **_kwargs: SimpleNamespace(stream_events=no_stream_events),
    )

    events = [event async for event in agent_module.stream_handler(analysis_request)]

    assert [event.type for event in events] == [
        "response.output_item.done",
        "response.completed",
    ]
    ImpactAnalysisResult.model_validate(events[1].response["custom_outputs"]["analysis"])


def test_agent_source_has_no_template_or_user_authorization_surface():
    source = (
        __import__("pathlib").Path(__file__).parents[1]
        / "agent_server"
        / "agent.py"
    ).read_text(encoding="utf-8")

    for forbidden in ("get_current_time", "McpServer", "get_user_workspace_client"):
        assert forbidden not in source


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error_code",
    [
        RepositoryErrorCode.REPOSITORY_CONTEXT_MISMATCH,
        RepositoryErrorCode.BRANCH_NOT_ALLOWED,
        RepositoryErrorCode.DATABRICKS_READ_ERROR,
    ],
)
@pytest.mark.parametrize("handler", ["invoke", "stream"])
async def test_preflight_repository_errors_return_safe_canonical_analysis_without_running_model(
    monkeypatch, analysis_request, error_code, handler
):
    import agent_server.agent as agent_module

    def failing_repository_factory(*_args, **_kwargs):
        return SimpleNamespace(
            get_context=lambda: (_ for _ in ()).throw(
                RepositoryAccessError(error_code, "internal credential details must not leak")
            )
        )

    runner_called = False

    async def forbidden_runner(*_args, **_kwargs):
        nonlocal runner_called
        runner_called = True
        raise AssertionError("Runner.run must not execute after a failed preflight")

    monkeypatch.setattr(agent_module, "DatabricksRepositoryClient", failing_repository_factory)
    monkeypatch.setattr(agent_module.Runner, "run", forbidden_runner)

    if handler == "invoke":
        response = await agent_module.invoke_handler(analysis_request)
    else:
        events = [event async for event in agent_module.stream_handler(analysis_request)]
        assert [event.type for event in events] == [
            "response.output_item.done",
            "response.completed",
        ]
        response = events[1].response

    result = ImpactAnalysisResult.model_validate(
        response.custom_outputs["analysis"]
        if handler == "invoke"
        else response["custom_outputs"]["analysis"]
    )
    markdown = (
        response.output[0].content[0]["text"]
        if handler == "invoke"
        else response["output"][0]["content"][0]["text"]
    )

    assert runner_called is False
    assert result.status == "completed"
    assert result.decision is Decision.INSUFFICIENT_EVIDENCE
    assert result.warnings == [error_code.value]
    assert error_code.value in markdown
    assert "internal credential details" not in markdown
    assert "internal credential details" not in result.model_dump_json()
