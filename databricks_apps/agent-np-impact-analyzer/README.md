# Naturapet NP Impact Analyzer

`agent-np-impact-analyzer` is a read-only Databricks App for evaluating the
impact of proposed engineering changes in the fixed `Naturapet_DLH` Git Folder.
It produces an auditable machine contract for a Supervisor and a derived
Markdown report for people; it does not edit, execute, deploy, or read outside
the authorized repository.

## Fixed repository and access boundary

The App accepts analysis requests only for this repository context:

- Repository ID: `1393361128272538`
- Workspace root: `/Workspace/Naturapet_BI/practica-margen-silver`
- Remote: `https://github.com/srinconr-Crea/Naturapet_DLH.git`
- Provider and branch: `gitHub` / `practica-margen-silver`
- App service principal access: `CAN_READ`

Every analysis verifies the repository identity before reading. The agent has
exactly four bounded read-only tools:

1. `get_repository_context`
2. `list_repository_tree`
3. `read_repository_file`
4. `search_repository_text`

The tools reject traversal and sensitive files, apply file/depth/result limits,
and expose no import, upload, update, delete, deployment, execution, job, or
Git-mutation operation. The deployed App uses its own service-principal
identity; it does not use on-behalf-of-user authorization.

## Runtime model

The App uses the serving endpoint configured by `NP_MODEL_ENDPOINT`, currently
`databricks-claude-sonnet-4-6`.
The bundle declares it as the `llm` resource with `CAN_QUERY` permission for
the App identity. This replaces the unavailable `databricks-gpt-5-2` endpoint,
which returned `ENDPOINT_NOT_FOUND` during live validation; the replacement was
chosen with user approval. The agent does not set `temperature` or `top_p`.

### Structured-output compatibility

Claude 4.6 rejects a request that combines tools with `response_format`
(`INVALID_PARAMETER_VALUE`). The tool-enabled researcher therefore has no
`output_type` and returns only JSON for `ImpactAnalysisDraft`. The App validates
that JSON directly. Only an invalid researcher result triggers a second,
tool-free formatter with `output_type=ImpactAnalysisDraft`; it treats the first
result as untrusted data and must not invent evidence or paths. If formatting
still fails, the App returns the canonical `insufficient_evidence` contract with
a safe warning rather than exposing an exception.

## Response contract

The canonical JSON is returned in `custom_outputs.analysis` and validates as
`ImpactAnalysisResult`. It includes the verified repository context, decision,
risk, cited evidence, target and related files, implementation plan, acceptance
criteria, safety restrictions, assumptions, and warnings.

The first text output is human-facing Markdown. It is deterministically derived
from that JSON, begins with `# Analisis de impacto`, and is not a second source
of truth. A Supervisor should consume the JSON and explicitly ignore the
`human_report_markdown` field:

```python
from agent_server.schemas import ImpactAnalysisResult

payload = response.model_dump(mode="json")
analysis = ImpactAnalysisResult.model_validate(payload["custom_outputs"]["analysis"])
supervisor_input = analysis.model_dump(exclude={"human_report_markdown"})
```

## Local verification

Run these commands from `databricks_apps/agent-np-impact-analyzer/`:

```powershell
uv run pytest -v
uv run preflight
databricks bundle validate --target dev --profile CREA_DEV
```

The reusable role, scope, tool bounds, output contract, identity and approval
gates are recorded in `agent-spec.json`.

`preflight` starts the local server, sends a safe read-only request, validates
`custom_outputs.analysis`, and checks its Markdown output. It can use the
developer's local `CREA_DEV` identity to read the authorized Git Folder.

`uv run discover-tools` is optional and fixes every SDK and CLI lookup to
`CREA_DEV`; it does not accept a caller-selected profile. Do not run it unless
read-only workspace discovery is in scope.

## Approved deployment and smoke-test sequence

Deployment is an approval-gated operation. After human approval, bind the
existing App (once), deploy to `dev`, restart it, then run the read-only smoke
tests. Run the status-only smoke first; it performs no model inference. Run the
functional smoke only when an inference has been approved:

```powershell
databricks bundle deployment bind np_impact_analyzer agent-np-impact-analyzer --auto-approve --target dev --profile CREA_DEV
databricks bundle deploy --target dev --profile CREA_DEV
databricks bundle run np_impact_analyzer --target dev --profile CREA_DEV
uv run smoke-status
uv run python scripts/smoke_test.py
```

`smoke-status` only reads the App and compute states. `smoke_test.py` constructs
`WorkspaceClient(profile="CREA_DEV")` and a
`DatabricksOpenAI` client, invokes `apps/agent-np-impact-analyzer`, validates
the canonical JSON, verified repository ID and branch, nonempty evidence, and
derived Markdown. It never fetches or prints OAuth tokens. Do not run the
deployment commands without explicit human approval, and do not target `qa` or
`prod`.
