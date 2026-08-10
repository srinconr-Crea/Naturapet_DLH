#!/usr/bin/env python3
"""Read-only smoke test for the deployed Naturapet impact-analyzer App.

Run only after an approved deployment.  Authentication is delegated to the
local CREA_DEV profile; this script never requests, prints, or persists tokens.
"""

from databricks.sdk import WorkspaceClient
from databricks_openai import DatabricksOpenAI

from agent_server.schemas import ImpactAnalysisResult

APP_MODEL = "apps/agent-np-impact-analyzer"
REPOSITORY_ID = 1393361128272538
REPOSITORY_BRANCH = "practica-margen-silver"
SMOKE_PROMPT = (
    "Analiza donde se calcula margen_pct y que pruebas deberian revisarse. "
    "No modifiques nada."
)


def _response_data(response: object) -> dict:
    """Return the SDK response as a JSON-compatible mapping without logging it."""
    model_dump = getattr(response, "model_dump", None)
    if not callable(model_dump):
        raise AssertionError("La respuesta de la App no tiene el formato esperado.")
    data = model_dump(mode="json")
    if not isinstance(data, dict):
        raise AssertionError("La respuesta de la App no tiene el formato esperado.")
    return data


def main() -> None:
    """Invoke the deployed App and enforce its read-only response contract."""
    workspace_client = WorkspaceClient(profile="CREA_DEV")
    client = DatabricksOpenAI(workspace_client=workspace_client)
    response = client.responses.create(
        model=APP_MODEL,
        input=[{"role": "user", "content": SMOKE_PROMPT}],
    )
    data = _response_data(response)
    result = ImpactAnalysisResult.model_validate(
        data.get("custom_outputs", {}).get("analysis")
    )
    markdown = data["output"][0]["content"][0]["text"]

    assert result.repository_context.repo_id == REPOSITORY_ID
    assert result.repository_context.branch == REPOSITORY_BRANCH
    assert result.evidence, "La prueba de humo requiere evidencia no vacia."
    assert markdown.startswith("# Analisis de impacto")
    assert markdown == result.human_report_markdown
    print("Smoke test read-only contract passed.")


if __name__ == "__main__":
    main()
