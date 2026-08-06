"""Contract tests for the local preflight invocation response."""

import json
from contextlib import contextmanager

from agent_server.schemas import ImpactAnalysisResult
from scripts import preflight


@contextmanager
def _json_response(payload: dict):
    class Response:
        def read(self) -> bytes:
            return json.dumps(payload).encode("utf-8")

    yield Response()


def _complete_response() -> dict:
    analysis = ImpactAnalysisResult.model_validate(
        {
            "schema_version": "1.0",
            "analysis_id": "ce76e4a1-3f65-4f92-a77d-08fc8ec7ee49",
            "status": "completed",
            "repository_context": {
                "repo_id": 1393361128272538,
                "path": "/Workspace/Naturapet_BI/practica-margen-silver",
                "url": "https://github.com/srinconr-Crea/Naturapet_DLH.git",
                "provider": "gitHub",
                "branch": "practica-margen-silver",
                "head_commit_id": "abc123",
            },
            "request_summary": "Analizar margen_pct.",
            "decision": "insufficient_evidence",
            "risk": {"level": "low", "reasons": ["No hay evidencia suficiente."]},
            "target_files": [],
            "related_files": [],
            "evidence": [],
            "implementation_plan": [],
            "acceptance_criteria": [],
            "prohibited_actions": ["No modificar recursos."],
            "assumptions": [],
            "warnings": ["Se requiere una lectura autorizada."],
            "human_report_markdown": "# AnÃ¡lisis de impacto\n",
        }
    )
    return {
        "output": [{"content": [{"text": "# AnÃ¡lisis de impacto\n"}]}],
        "custom_outputs": {"analysis": analysis.model_dump(mode="json")},
    }


def test_preflight_rejects_output_without_canonical_analysis(monkeypatch):
    """A response with only Markdown cannot satisfy the Supervisor contract."""
    monkeypatch.setattr(
        preflight.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: _json_response(
            {"output": [{"content": [{"text": "# AnÃ¡lisis de impacto\n"}]}]}
        ),
    )

    assert preflight.check_invocations("http://localhost:8000", retries=0) is False


def test_preflight_accepts_valid_canonical_analysis_and_markdown(monkeypatch):
    """A complete response validates before preflight accepts it."""
    monkeypatch.setattr(
        preflight.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: _json_response(_complete_response()),
    )

    assert preflight.check_invocations("http://localhost:8000", retries=0) is True
