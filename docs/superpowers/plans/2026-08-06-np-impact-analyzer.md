# NP Impact Analyzer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the existing `agent-np-impact-analyzer` Databricks App into a read-only, evidence-backed impact analyzer for the authorized `Naturapet_DLH` Git Folder.

**Architecture:** Keep the existing OpenAI Agents SDK and MLflow AgentServer template, but replace the sample time tool with four bounded repository-reading tools backed by `WorkspaceClient()` app authorization. Validate repository identity before every analysis, produce a Pydantic-validated JSON result in `custom_outputs.analysis`, and render the human Markdown message from that same validated object.

**Tech Stack:** Python 3.11, OpenAI Agents SDK, Databricks SDK for Python, Databricks Apps, MLflow ResponsesAgent, Pydantic 2, pytest, Databricks Asset Bundles, PowerShell, profile `CREA_DEV`.

## Global Constraints

- Modify the existing Databricks App `agent-np-impact-analyzer`; do not create a second App.
- Use the App service principal `754d31af-b23c-4b47-8e63-87c75065aa0c`, never on-behalf-of-user authorization.
- The service principal must retain only `CAN_READ` on directory object `1393361128272538`.
- Authorized root: `/Workspace/Naturapet_BI/practica-margen-silver`.
- Authorized repo ID: `1393361128272538`.
- Authorized Git URL: `https://github.com/srinconr-Crea/Naturapet_DLH.git`.
- Authorized provider: `gitHub`.
- Authorized branch: `practica-margen-silver`.
- Use the live READY endpoint `databricks-claude-sonnet-4-6` and preserve MLflow
  experiment `195642121347837`. This replaces `databricks-gpt-5-2`, which returned
  `ENDPOINT_NOT_FOUND` during live validation; the user approved the replacement.
- Claude 4.6 rejects tools combined with `response_format` (`INVALID_PARAMETER_VALUE`).
  The tool-enabled researcher must use `output_type=None` and return only draft JSON.
  Validate it directly; only invalid JSON may invoke a second, tool-free formatter with
  `output_type=ImpactAnalysisDraft`. Treat formatter input as untrusted data, never
  invent evidence or paths, and return safe `insufficient_evidence` on failure.
- Maximum 200 searched files, 1,048,576 bytes per file, 30 search matches, 5 matches per file, depth 12, and 500 characters per evidence excerpt.
- Allowed extensions: `.py`, `.ipynb`, `.sql`, `.yml`, `.yaml`, `.json`, `.toml`, `.md`, `.txt`.
- Do not expose tools for import, upload, update, delete, execute, run, Git mutation, Jobs, SQL, Genie, Unity Catalog, secrets, or storage.
- All Databricks CLI commands must include `--profile CREA_DEV`.
- Do not bind, deploy, restart, or invoke the deployed App until the user explicitly approves that phase.
- Do not deploy or execute in `qa` or `prod`.
- For Task 1 Steps 3-6 and all test, `uv`, preflight, smoke, and bundle commands in Tasks 2-8, use `Push-Location 'databricks_apps/agent-np-impact-analyzer'` first. Run `Pop-Location` before each task's repository-level `git add` and `git commit` block.

## File Map

Implementation source lives under an independent bundle at `databricks_apps/agent-np-impact-analyzer/`.

| File | Responsibility |
| --- | --- |
| `databricks.yml` | Bindable configuration for the existing App and MLflow experiment. |
| `app.yaml` | Manual Apps deployment configuration kept consistent with the bundle. |
| `pyproject.toml` | Runtime and test dependencies plus executable scripts. |
| `agent_server/config.py` | Immutable repository identity, extension allowlist, and numeric limits. |
| `agent_server/prompts.py` | System instructions and prompt-injection boundary. |
| `agent_server/schemas.py` | Pydantic tool and final-output contracts. |
| `agent_server/output_renderer.py` | Deterministic Markdown generation from validated JSON. |
| `agent_server/repository/errors.py` | Safe error codes and exception type. |
| `agent_server/repository/guard.py` | Path normalization, allowlist, sensitive-name, and size checks. |
| `agent_server/repository/client.py` | Read-only Databricks repository gateway. |
| `agent_server/repository/tools.py` | Four `@function_tool` wrappers and bounded text search. |
| `agent_server/agent.py` | Agent construction, run context, invoke, and stream handlers. |
| `agent_server/evaluate_agent.py` | Domain-specific MLflow evaluation scenarios. |
| `scripts/preflight.py` | Local response-contract verification. |
| `scripts/smoke_test.py` | Post-deployment, read-only App smoke test. |
| `tests/` | Unit and handler tests with no live Databricks writes. |

---

### Task 1: Synchronize the Existing App and Establish Its Independent Bundle

**Files:**
- Create: `databricks_apps/agent-np-impact-analyzer/**`
- Modify: `databricks_apps/agent-np-impact-analyzer/databricks.yml`
- Modify: `databricks_apps/agent-np-impact-analyzer/app.yaml`
- Modify: `databricks_apps/agent-np-impact-analyzer/pyproject.toml`
- Create: `databricks_apps/agent-np-impact-analyzer/uv.lock`

**Interfaces:**
- Consumes: existing Workspace source at `/Workspace/Users/srinconr@creasistemas.com/databricks_apps/agent-np-impact-analyzer_2026_08_05-21_07/agent-openai-agents-sdk`.
- Produces: a local bundle resource key `np_impact_analyzer` whose configured App name is `agent-np-impact-analyzer`.

- [ ] **Step 1: Confirm local and remote baselines are unchanged**

Run from the repository root:

```powershell
git status --short
databricks apps get agent-np-impact-analyzer --profile CREA_DEV
databricks workspace get-permissions directories 1393361128272538 --profile CREA_DEV
```

Expected: the App is running, the experiment ID is `195642121347837`, and `app-1ta350 agent-np-impact-analyzer` has `CAN_READ` on the directory. Record existing unrelated local files and do not stage them.

- [ ] **Step 2: Synchronize the current App source into the independent local folder**

Run only after confirming the target folder does not already contain user work:

```powershell
databricks workspace export-dir '/Workspace/Users/srinconr@creasistemas.com/databricks_apps/agent-np-impact-analyzer_2026_08_05-21_07/agent-openai-agents-sdk' 'databricks_apps/agent-np-impact-analyzer' --profile CREA_DEV
```

Expected: `agent.py`, `app.yaml`, `databricks.yml`, `pyproject.toml`, `scripts/`, and the template UI support files exist locally. This reads the Workspace and writes only the new local source folder.

- [ ] **Step 3: Update bundle identity and least-privilege configuration**

Replace the bundle and App resource headers in `databricks.yml` with:

```yaml
bundle:
  name: np_impact_analyzer

resources:
  apps:
    np_impact_analyzer:
      name: agent-np-impact-analyzer
      description: Analista de impacto de solo lectura para Naturapet_DLH
      source_code_path: ./
      config:
        command: ["uv", "run", "start-app"]
        env:
          - name: MLFLOW_TRACKING_URI
            value: databricks
          - name: MLFLOW_REGISTRY_URI
            value: databricks-uc
          - name: API_PROXY
            value: http://localhost:8000/invocations
          - name: CHAT_APP_PORT
            value: "3000"
          - name: CHAT_PROXY_TIMEOUT_SECONDS
            value: "300"
          - name: MLFLOW_EXPERIMENT_ID
            value_from: experiment
          - name: NP_REPOSITORY_ID
            value: "1393361128272538"
          - name: NP_REPOSITORY_ROOT
            value: /Workspace/Naturapet_BI/practica-margen-silver
          - name: NP_REPOSITORY_URL
            value: https://github.com/srinconr-Crea/Naturapet_DLH.git
          - name: NP_REPOSITORY_PROVIDER
            value: gitHub
          - name: NP_REPOSITORY_BRANCH
            value: practica-margen-silver
      resources:
        - name: experiment
          experiment:
            experiment_id: "195642121347837"
            permission: CAN_EDIT

targets:
  dev:
    mode: development
    default: true
    workspace:
      host: https://adb-7405606739630987.7.azuredatabricks.net
```

Remove the template `prod` target. Do not declare user API scopes or writable resources.

- [ ] **Step 4: Keep `app.yaml` consistent**

Add the five `NP_REPOSITORY_*` variables using `value` keys and retain `MLFLOW_EXPERIMENT_ID` with `valueFrom: experiment`. Do not add credentials or user authorization settings.

- [ ] **Step 5: Pin direct dependencies used by the new code**

Add to `[project].dependencies` in `pyproject.toml`:

```toml
"databricks-sdk>=0.72.0,<1.0.0",
"pydantic>=2.12.0,<3.0.0",
```

Add to `[dependency-groups].dev`:

```toml
"pytest-asyncio>=1.3.0,<2.0.0",
```

Then generate the lock file:

```powershell
uv lock
```

Expected: `uv.lock` is created without changing dependencies outside the App folder.

- [ ] **Step 6: Validate the independent bundle locally**

```powershell
databricks bundle validate --target dev --profile CREA_DEV
databricks bundle summary --target dev --profile CREA_DEV
```

Expected: validation succeeds and the resource summary names `agent-np-impact-analyzer`. These commands do not bind or deploy.

- [ ] **Step 7: Commit the synchronized baseline and corrected bundle**

```powershell
git add -- databricks_apps/agent-np-impact-analyzer
git diff --cached --name-only
git commit -m "chore: sync np impact analyzer app"
```

Expected: only files under `databricks_apps/agent-np-impact-analyzer/` are committed.

---

### Task 2: Implement Immutable Configuration and Repository Guards

**Files:**
- Create: `databricks_apps/agent-np-impact-analyzer/agent_server/config.py`
- Create: `databricks_apps/agent-np-impact-analyzer/agent_server/repository/__init__.py`
- Create: `databricks_apps/agent-np-impact-analyzer/agent_server/repository/errors.py`
- Create: `databricks_apps/agent-np-impact-analyzer/agent_server/repository/guard.py`
- Create: `databricks_apps/agent-np-impact-analyzer/tests/test_config.py`
- Create: `databricks_apps/agent-np-impact-analyzer/tests/repository/test_guard.py`

**Interfaces:**
- Consumes: the five `NP_REPOSITORY_*` environment variables from Task 1.
- Produces: `RepositoryConfig`, `RepositoryErrorCode`, `RepositoryAccessError`, `normalize_relative_path()`, `validate_file_policy()`, and `redact_sensitive_content()`.

- [ ] **Step 1: Write failing configuration and guard tests**

Create tests covering these exact cases:

```python
import pytest

from agent_server.config import RepositoryConfig
from agent_server.repository.errors import RepositoryAccessError, RepositoryErrorCode
from agent_server.repository.guard import (
    normalize_relative_path,
    redact_sensitive_content,
    validate_file_policy,
)


def test_repository_config_has_fixed_limits():
    config = RepositoryConfig()
    assert config.repo_id == 1393361128272538
    assert config.root == "/Workspace/Naturapet_BI/practica-margen-silver"
    assert config.branch == "practica-margen-silver"
    assert config.max_files == 200
    assert config.max_file_bytes == 1_048_576
    assert config.max_results == 30


@pytest.mark.parametrize("candidate", ["../README.md", "notebooks/../../secret", "C:/temp/a.py", "/Workspace/Users/a.py"])
def test_normalize_relative_path_blocks_escape(candidate):
    with pytest.raises(RepositoryAccessError) as error:
        normalize_relative_path(candidate)
    assert error.value.code == RepositoryErrorCode.PATH_NOT_ALLOWED


@pytest.mark.parametrize("candidate", [".env", "secrets/client.pem", "config/id_rsa", ".git/config", "data/model.bin"])
def test_validate_file_policy_blocks_sensitive_or_binary_paths(candidate):
    with pytest.raises(RepositoryAccessError):
        validate_file_policy(candidate, size_bytes=100, config=RepositoryConfig())


def test_redact_sensitive_content_masks_assignment_values():
    content, redacted = redact_sensitive_content(
        'CLIENT_SECRET="sensitive-value"\nnormal_setting="visible"'
    )
    assert redacted is True
    assert "sensitive-value" not in content
    assert 'normal_setting="visible"' in content
```

- [ ] **Step 2: Run tests and confirm they fail because modules do not exist**

```powershell
uv run pytest tests/test_config.py tests/repository/test_guard.py -v
```

Expected: collection fails with `ModuleNotFoundError` for the new modules.

- [ ] **Step 3: Implement configuration and safe errors**

Implement the following public contracts:

```python
class RepositoryConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    repo_id: int = 1393361128272538
    root: str = "/Workspace/Naturapet_BI/practica-margen-silver"
    url: str = "https://github.com/srinconr-Crea/Naturapet_DLH.git"
    provider: str = "gitHub"
    branch: str = "practica-margen-silver"
    allowed_extensions: frozenset[str] = frozenset({".py", ".ipynb", ".sql", ".yml", ".yaml", ".json", ".toml", ".md", ".txt"})
    max_files: int = 200
    max_file_bytes: int = 1_048_576
    max_results: int = 30
    max_results_per_file: int = 5
    max_depth: int = 12
    max_excerpt_chars: int = 500

    @classmethod
    def from_environment(cls) -> "RepositoryConfig":
        return cls(
            repo_id=int(os.getenv("NP_REPOSITORY_ID", "1393361128272538")),
            root=os.getenv("NP_REPOSITORY_ROOT", cls.model_fields["root"].default),
            url=os.getenv("NP_REPOSITORY_URL", cls.model_fields["url"].default),
            provider=os.getenv("NP_REPOSITORY_PROVIDER", cls.model_fields["provider"].default),
            branch=os.getenv("NP_REPOSITORY_BRANCH", cls.model_fields["branch"].default),
        )


class RepositoryErrorCode(StrEnum):
    REPOSITORY_CONTEXT_MISMATCH = "REPOSITORY_CONTEXT_MISMATCH"
    BRANCH_NOT_ALLOWED = "BRANCH_NOT_ALLOWED"
    PATH_NOT_ALLOWED = "PATH_NOT_ALLOWED"
    FILE_TYPE_NOT_ALLOWED = "FILE_TYPE_NOT_ALLOWED"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    CONTENT_REDACTED = "CONTENT_REDACTED"
    SEARCH_LIMIT_REACHED = "SEARCH_LIMIT_REACHED"
    DATABRICKS_READ_ERROR = "DATABRICKS_READ_ERROR"


class RepositoryAccessError(RuntimeError):
    def __init__(self, code: RepositoryErrorCode, safe_message: str):
        super().__init__(safe_message)
        self.code = code
        self.safe_message = safe_message
```

- [ ] **Step 4: Implement path and file validation**

`normalize_relative_path(candidate: str) -> str` must convert backslashes to `/`, reject empty absolute roots, drives, URI schemes, and any `..` segment, then return a POSIX relative path. `validate_file_policy(relative_path: str, size_bytes: int | None, config: RepositoryConfig) -> str` must reject sensitive basenames, sensitive suffixes, `.git` segments, unsupported extensions, and known sizes above the configured maximum.

Use a case-insensitive sensitive-name set containing:

```python
SENSITIVE_NAMES = frozenset({
    ".env", ".env.local", "id_rsa", "id_dsa", "credentials", "credentials.json",
    "secrets.json", "token", "token.json", ".databrickscfg",
})
SENSITIVE_SUFFIXES = frozenset({".pem", ".key", ".p12", ".pfx", ".crt", ".cer"})
```

`redact_sensitive_content(content: str) -> tuple[str, bool]` must replace values assigned to names matching `api_key`, `access_token`, `client_secret`, `password`, or `secret` with `[REDACTED]`, case-insensitively. It must also redact PEM blocks matching `-----BEGIN [A-Z ]*PRIVATE KEY-----` through their matching end marker. It returns the sanitized text and whether any redaction occurred.

- [ ] **Step 5: Run guard tests**

```powershell
uv run pytest tests/test_config.py tests/repository/test_guard.py -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit configuration and guards**

```powershell
git add -- databricks_apps/agent-np-impact-analyzer/agent_server/config.py databricks_apps/agent-np-impact-analyzer/agent_server/repository databricks_apps/agent-np-impact-analyzer/tests
git commit -m "feat: guard np repository access"
```

---

### Task 3: Build the Read-Only Databricks Repository Client

**Files:**
- Create: `databricks_apps/agent-np-impact-analyzer/agent_server/schemas.py`
- Create: `databricks_apps/agent-np-impact-analyzer/agent_server/repository/client.py`
- Create: `databricks_apps/agent-np-impact-analyzer/tests/conftest.py`
- Create: `databricks_apps/agent-np-impact-analyzer/tests/repository/test_client.py`

**Interfaces:**
- Consumes: `RepositoryConfig`, `RepositoryAccessError`, `normalize_relative_path()`, and `validate_file_policy()`.
- Produces: `RepositoryContext`, `RepositoryEntry`, `RepositoryFile`, `RepositoryGateway`, and `DatabricksRepositoryClient`.

- [ ] **Step 1: Write failing client tests with a fake WorkspaceClient**

Define reusable fixtures in `tests/conftest.py`:

```python
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
```

Tests must then prove:

```python
def test_get_context_accepts_exact_repo(fake_workspace_client, config):
    client = DatabricksRepositoryClient(fake_workspace_client, config)
    context = client.get_context()
    assert context.repo_id == config.repo_id
    assert context.branch == config.branch
    assert context.head_commit_id == "9c48831022a329902f765058de37e6d0a1528eb7"


def test_get_context_rejects_branch_mismatch(fake_workspace_client, config):
    fake_workspace_client.repos.get.return_value.branch = "develop"
    with pytest.raises(RepositoryAccessError) as error:
        DatabricksRepositoryClient(fake_workspace_client, config).get_context()
    assert error.value.code == RepositoryErrorCode.BRANCH_NOT_ALLOWED


def test_read_file_uses_only_workspace_download(fake_workspace_client, config):
    client = DatabricksRepositoryClient(fake_workspace_client, config)
    result = client.read_file("README.md")
    assert result.relative_path == "README.md"
    assert result.content.startswith("# Naturapet_DLH")
    fake_workspace_client.workspace.download.assert_called_once()
```

Also assert that `DatabricksRepositoryClient` exposes no `write`, `upload`, `import`, `delete`, `run`, or `update` method.

- [ ] **Step 2: Run tests and confirm failure**

```powershell
uv run pytest tests/repository/test_client.py -v
```

Expected: failure because schemas and client are not implemented.

- [ ] **Step 3: Define repository schemas and protocol**

Create these models in `schemas.py`:

```python
class RepositoryContext(BaseModel):
    repo_id: int
    path: str
    url: str
    provider: str
    branch: str
    head_commit_id: str


class RepositoryEntry(BaseModel):
    relative_path: str
    object_type: str
    size_bytes: int | None = None


class RepositoryFile(BaseModel):
    relative_path: str
    content: str
    size_bytes: int
    truncated: bool = False
    redacted: bool = False


class RepositoryGateway(Protocol):
    def get_context(self) -> RepositoryContext:
        raise NotImplementedError

    def list_tree(self, relative_path: str = "", max_depth: int | None = None) -> list[RepositoryEntry]:
        raise NotImplementedError

    def read_file(self, relative_path: str) -> RepositoryFile:
        raise NotImplementedError
```

Keep these method names and return types unchanged so the fake gateway and Databricks implementation remain interchangeable.

- [ ] **Step 4: Implement exact repository-context validation**

`DatabricksRepositoryClient.get_context()` must call only `workspace_client.repos.get(config.repo_id)`. Normalize the API repo path by adding `/Workspace` when it begins with `/Naturapet_BI/`, then compare repo ID, path, URL, provider, and branch. Raise `BRANCH_NOT_ALLOWED` for only the branch mismatch and `REPOSITORY_CONTEXT_MISMATCH` for other differences.

- [ ] **Step 5: Implement bounded recursive listing**

Use `workspace_client.workspace.list(absolute_path)` iterators. Maintain a queue of `(path, depth)`, stop at `config.max_files`, exclude disallowed files, and return only paths relative to `config.root`. Directory entries may be traversed but must not count as readable files.

- [ ] **Step 6: Implement bounded file reading**

Resolve the validated relative path under the configured root, call `workspace.get_status()` for size when available, and read with:

```python
from databricks.sdk.service.workspace import ExportFormat

with self.workspace_client.workspace.download(absolute_path, format=ExportFormat.AUTO) as stream:
    raw = stream.read(self.config.max_file_bytes + 1)
```

Raise `FILE_TOO_LARGE` if the byte count exceeds the limit and `CONTENT_REDACTED` if UTF-8 decoding fails. After decoding, call `redact_sensitive_content()` and set `RepositoryFile.redacted` so the tool and final analysis can disclose that sanitization occurred without exposing the removed value. Convert SDK exceptions into `DATABRICKS_READ_ERROR` with a safe message that excludes tokens, request headers, and raw exception bodies.

- [ ] **Step 7: Run client tests**

```powershell
uv run pytest tests/repository/test_client.py -v
```

Expected: all client tests pass and mocks show only `repos.get`, `workspace.list`, `workspace.get_status`, and `workspace.download` calls.

- [ ] **Step 8: Commit the read-only client**

```powershell
git add -- databricks_apps/agent-np-impact-analyzer/agent_server/schemas.py databricks_apps/agent-np-impact-analyzer/agent_server/repository/client.py databricks_apps/agent-np-impact-analyzer/tests/conftest.py databricks_apps/agent-np-impact-analyzer/tests/repository/test_client.py
git commit -m "feat: read databricks git folder safely"
```

---

### Task 4: Expose Four Bounded Agent Tools

**Files:**
- Create: `databricks_apps/agent-np-impact-analyzer/agent_server/repository/tools.py`
- Create: `databricks_apps/agent-np-impact-analyzer/tests/repository/test_tools.py`

**Interfaces:**
- Consumes: `RepositoryGateway`, repository schemas, and `RepositoryConfig`.
- Produces: `AnalysisRunContext`, `get_repository_context`, `list_repository_tree`, `read_repository_file`, and `search_repository_text`.

- [ ] **Step 1: Write failing pure-search and tool-schema tests**

Create a fake `RepositoryGateway` with deterministic files:

```python
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

    def list_tree(self, relative_path: str = "", max_depth: int | None = None) -> list[RepositoryEntry]:
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
```

Then assert:

```python
def test_search_returns_bounded_line_evidence(fake_gateway, config):
    matches = search_text(fake_gateway, config, "margen_pct", "")
    assert len(matches.matches) <= config.max_results
    assert matches.matches[0].relative_path.endswith("04_business_derivations.ipynb")
    assert matches.matches[0].line_number >= 1


def test_search_reports_limit(fake_gateway, config):
    result = search_text(fake_gateway, config.model_copy(update={"max_results": 1}), "silver", "")
    assert result.limit_reached is True
    assert "SEARCH_LIMIT_REACHED" in result.warnings


def test_agent_exports_exact_tool_names():
    assert {tool.name for tool in REPOSITORY_TOOLS} == {
        "get_repository_context",
        "list_repository_tree",
        "read_repository_file",
        "search_repository_text",
    }
```

- [ ] **Step 2: Run tests and confirm failure**

```powershell
uv run pytest tests/repository/test_tools.py -v
```

Expected: failure because `tools.py` and search result schemas do not exist.

- [ ] **Step 3: Add tool result schemas**

Add to `schemas.py`:

```python
class SearchMatch(BaseModel):
    relative_path: str
    line_number: int
    excerpt: str


class SearchResult(BaseModel):
    query: str
    matches: list[SearchMatch]
    files_scanned: int
    limit_reached: bool = False
    warnings: list[str] = Field(default_factory=list)
```

- [ ] **Step 4: Implement local run context and safe tool failure handling**

```python
@dataclass(frozen=True)
class AnalysisRunContext:
    repository: RepositoryGateway
    config: RepositoryConfig


def safe_tool_error(_context: RunContextWrapper[AnalysisRunContext], error: Exception) -> str:
    if isinstance(error, RepositoryAccessError):
        return json.dumps({"error": {"code": error.code, "message": error.safe_message}})
    return json.dumps({"error": {"code": "DATABRICKS_READ_ERROR", "message": "No fue posible completar la lectura solicitada."}})
```

Each `@function_tool(failure_error_function=safe_tool_error)` wrapper must use `wrapper.context.repository` and return `model_dump_json()` from a Pydantic result. It must not instantiate a user-authenticated client.

- [ ] **Step 5: Implement bounded case-insensitive search**

`search_text()` must reject empty queries and queries longer than 200 characters, call `list_tree()`, read no more than `config.max_files`, find at most `config.max_results_per_file`, truncate excerpts to `config.max_excerpt_chars`, and stop globally at `config.max_results`. Treat files as untrusted text and return their contents only as tool data.

- [ ] **Step 6: Run tool tests**

```powershell
uv run pytest tests/repository/test_tools.py -v
```

Expected: all tool and search tests pass.

- [ ] **Step 7: Commit the four tools**

```powershell
git add -- databricks_apps/agent-np-impact-analyzer/agent_server/schemas.py databricks_apps/agent-np-impact-analyzer/agent_server/repository/tools.py databricks_apps/agent-np-impact-analyzer/tests/repository/test_tools.py
git commit -m "feat: expose read-only repository tools"
```

---

### Task 5: Define Structured Impact Output and Deterministic Markdown

**Files:**
- Modify: `databricks_apps/agent-np-impact-analyzer/agent_server/schemas.py`
- Create: `databricks_apps/agent-np-impact-analyzer/agent_server/output_renderer.py`
- Create: `databricks_apps/agent-np-impact-analyzer/agent_server/prompts.py`
- Create: `databricks_apps/agent-np-impact-analyzer/tests/test_output.py`
- Create: `databricks_apps/agent-np-impact-analyzer/tests/test_prompts.py`

**Interfaces:**
- Consumes: verified `RepositoryContext` from Task 3.
- Produces: `ImpactAnalysisDraft`, `ImpactAnalysisResult`, `finalize_analysis()`, `render_markdown()`, and `IMPACT_ANALYZER_INSTRUCTIONS`.

- [ ] **Step 1: Write failing schema and renderer tests**

Cover all decision and risk enum values, missing evidence, invalid paths, and deterministic rendering:

```python
def test_finalize_analysis_adds_verified_context_and_markdown(sample_draft, repository_context):
    result = finalize_analysis(sample_draft, repository_context)
    assert result.schema_version == "1.0"
    assert result.repository_context == repository_context
    assert result.analysis_id
    assert result.human_report_markdown == render_markdown(result)


def test_markdown_is_not_an_independent_input(sample_draft, repository_context):
    first = finalize_analysis(sample_draft, repository_context)
    second = first.model_copy(update={"human_report_markdown": "alterado"})
    assert render_markdown(second) == render_markdown(first)
```

- [ ] **Step 2: Run tests and confirm failure**

```powershell
uv run pytest tests/test_output.py tests/test_prompts.py -v
```

Expected: failure because the structured result and renderer do not exist.

- [ ] **Step 3: Implement strict enums and output models**

Define:

```python
class Decision(StrEnum):
    FEASIBLE = "feasible"
    FEASIBLE_WITH_CONDITIONS = "feasible_with_conditions"
    NOT_FEASIBLE = "not_feasible"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvidenceKind(StrEnum):
    DIRECT = "direct"
    INFERENCE = "inference"
```

Add these exact model fields:

```python
class RiskAssessment(BaseModel):
    level: RiskLevel
    reasons: list[str] = Field(min_length=1)


class FileReference(BaseModel):
    relative_path: str
    reason: str


class EvidenceItem(BaseModel):
    relative_path: str
    line_start: int | None = Field(default=None, ge=1)
    line_end: int | None = Field(default=None, ge=1)
    excerpt: str = Field(max_length=500)
    finding: str
    kind: EvidenceKind


class ImplementationStep(BaseModel):
    order: int = Field(ge=1)
    action: str
    files: list[str]


class ImpactAnalysisDraft(BaseModel):
    request_summary: str
    decision: Decision
    risk: RiskAssessment
    target_files: list[FileReference]
    related_files: list[FileReference]
    evidence: list[EvidenceItem]
    implementation_plan: list[ImplementationStep]
    acceptance_criteria: list[str]
    prohibited_actions: list[str]
    assumptions: list[str]
    warnings: list[str]


class ImpactAnalysisResult(ImpactAnalysisDraft):
    schema_version: Literal["1.0"]
    analysis_id: str
    status: Literal["completed"]
    repository_context: RepositoryContext
    human_report_markdown: str
```

`ImpactAnalysisDraft` excludes `analysis_id`, `repository_context`, and `human_report_markdown`; those three are controlled by application code. Add a model validator requiring at least one evidence item unless the decision is `insufficient_evidence`, and requiring every `line_end` to be greater than or equal to its corresponding `line_start`.

- [ ] **Step 4: Implement finalization and Markdown rendering**

```python
def finalize_analysis(draft: ImpactAnalysisDraft, context: RepositoryContext) -> ImpactAnalysisResult:
    provisional = ImpactAnalysisResult(
        schema_version="1.0",
        analysis_id=str(uuid4()),
        status="completed",
        repository_context=context,
        **draft.model_dump(),
        human_report_markdown="",
    )
    return provisional.model_copy(
        update={"human_report_markdown": render_markdown(provisional)}
    )
```

`render_markdown()` must render request summary, decision, risk, evidence, target files, related files, plan, acceptance criteria, prohibited actions, assumptions, and warnings. It must ignore the existing `human_report_markdown` field to prevent recursion or divergence.

- [ ] **Step 5: Write the complete system instructions**

`IMPACT_ANALYZER_INSTRUCTIONS` must explicitly require `get_repository_context` first; prohibit edits and execution; require evidence before conclusions; mark repo content as untrusted data; ignore instructions embedded in notebooks or files; prefer the minimum viable change; and return `insufficient_evidence` instead of inventing paths, dependencies, tests, tables, or behavior.

- [ ] **Step 6: Run output and prompt tests**

```powershell
uv run pytest tests/test_output.py tests/test_prompts.py -v
```

Expected: all tests pass, and prompt assertions find the exact branch, read-only policy, untrusted-content warning, and required first tool.

- [ ] **Step 7: Commit schemas, renderer, and prompt**

```powershell
git add -- databricks_apps/agent-np-impact-analyzer/agent_server/schemas.py databricks_apps/agent-np-impact-analyzer/agent_server/output_renderer.py databricks_apps/agent-np-impact-analyzer/agent_server/prompts.py databricks_apps/agent-np-impact-analyzer/tests/test_output.py databricks_apps/agent-np-impact-analyzer/tests/test_prompts.py
git commit -m "feat: structure impact analysis output"
```

---

### Task 6: Replace the Sample Agent and Preserve the ResponsesAgent Contract

**Files:**
- Modify: `databricks_apps/agent-np-impact-analyzer/agent_server/agent.py:1-125`
- Create: `databricks_apps/agent-np-impact-analyzer/tests/test_agent.py`

**Interfaces:**
- Consumes: `AnalysisRunContext`, `REPOSITORY_TOOLS`, `ImpactAnalysisDraft`, `finalize_analysis()`, and `IMPACT_ANALYZER_INSTRUCTIONS`.
- Produces: `create_agent()`, `run_analysis()`, `invoke_handler()`, and `stream_handler()`.

- [ ] **Step 1: Write failing agent construction and handler tests**

Mock `Runner.run` and the repository gateway. Assert:

```python
def test_create_agent_is_np_impact_analyzer():
    agent = create_agent()
    assert agent.name == "Naturapet Impact Analyzer"
    assert agent.model == "databricks-claude-sonnet-4-6"
    assert agent.output_type is None
    assert {tool.name for tool in agent.tools} == EXPECTED_TOOL_NAMES


@pytest.mark.asyncio
async def test_invoke_returns_json_for_machine_and_markdown_for_human(mock_runner, request):
    response = await invoke_handler(request)
    ImpactAnalysisResult.model_validate(response.custom_outputs["analysis"])
    assert response.output[0].content[0].text.startswith("# Análisis de impacto")
```

Also assert `agent.py` contains no `get_current_time`, `McpServer`, or `get_user_workspace_client` reference.

- [ ] **Step 2: Run tests and confirm they fail against the template agent**

```powershell
uv run pytest tests/test_agent.py -v
```

Expected: tests identify the generic name, generic instructions, time tool, and missing structured output.

- [ ] **Step 3: Replace sample and MCP scaffolding with the real agent**

Construct:

```python
def create_agent() -> Agent[AnalysisRunContext]:
    return Agent[AnalysisRunContext](
        name="Naturapet Impact Analyzer",
        instructions=IMPACT_ANALYZER_INSTRUCTIONS,
        model="databricks-claude-sonnet-4-6",
        tools=REPOSITORY_TOOLS,
        output_type=None,
    )
```

Retain MLflow autologging and `AsyncDatabricksOpenAI()`. Remove the unused time tool, MCP server functions, user authorization import, and MCP imports.

- [ ] **Step 4: Implement one shared analysis runner**

```python
async def run_analysis(request: ResponsesAgentRequest) -> ImpactAnalysisResult:
    config = RepositoryConfig.from_environment()
    repository = DatabricksRepositoryClient(WorkspaceClient(), config)
    verified_context = repository.get_context()
    run_context = AnalysisRunContext(repository=repository, config=config)
    messages = [item.model_dump() for item in request.input]
    result = await Runner.run(create_agent(), messages, context=run_context)
    draft = ImpactAnalysisDraft.model_validate(result.final_output)
    return finalize_analysis(draft, verified_context)
```

This preflight validation occurs before the model can call tools and uses the App identity because `WorkspaceClient()` receives no user token.

- [ ] **Step 5: Return machine JSON and human Markdown from invoke**

Build the output using MLflow response helpers:

```python
def build_response(result: ImpactAnalysisResult) -> ResponsesAgentResponse:
    message = ResponseOutputMessage(
        id=str(uuid4()),
        role="assistant",
        status="completed",
        content=[ResponseOutputText(text=result.human_report_markdown)],
    )
    return ResponsesAgentResponse(
        output=[message],
        custom_outputs={"analysis": result.model_dump(mode="json")},
        status="completed",
    )
```

`invoke_handler()` updates MLflow session metadata, calls `run_analysis()`, and returns `build_response()`.

- [ ] **Step 6: Implement deterministic streaming completion**

For the MVP, `stream_handler()` calls the same `run_analysis()` and yields a completed output item followed by a completed response. It does not forward the model's intermediate structured JSON tokens:

```python
response = build_response(await run_analysis(request))
yield ResponsesAgentStreamEvent(
    type="response.output_item.done",
    item=response.output[0].model_dump(mode="json"),
    output_index=0,
)
yield ResponsesAgentStreamEvent(
    type="response.completed",
    response=response.model_dump(mode="json"),
)
```

- [ ] **Step 7: Run agent tests**

```powershell
uv run pytest tests/test_agent.py -v
```

Expected: construction, invoke, stream, App identity, JSON, and Markdown tests pass.

- [ ] **Step 8: Commit the integrated agent**

```powershell
git add -- databricks_apps/agent-np-impact-analyzer/agent_server/agent.py databricks_apps/agent-np-impact-analyzer/tests/test_agent.py
git commit -m "feat: implement np impact analyzer"
```

---

### Task 7: Replace Generic Evaluation and Add Read-Only Verification

**Files:**
- Modify: `databricks_apps/agent-np-impact-analyzer/agent_server/evaluate_agent.py`
- Modify: `databricks_apps/agent-np-impact-analyzer/scripts/preflight.py`
- Create: `databricks_apps/agent-np-impact-analyzer/scripts/smoke_test.py`
- Modify: `databricks_apps/agent-np-impact-analyzer/README.md`
- Create: `databricks_apps/agent-np-impact-analyzer/tests/test_read_only_surface.py`
- Create: `databricks_apps/agent-np-impact-analyzer/tests/test_preflight_contract.py`

**Interfaces:**
- Consumes: ResponsesAgent response with `custom_outputs.analysis` and Markdown output.
- Produces: domain evaluation cases, local contract checks, and a deployed-App smoke test.

- [ ] **Step 1: Write failing static read-only and preflight tests**

The static test must parse files under `agent_server/repository/` with `ast` and fail if it finds calls whose attribute is one of:

```python
FORBIDDEN_CALLS = {
    "upload", "upload_from", "import_", "delete", "mkdirs", "update",
    "create", "run_now", "repair_run", "deploy", "set_permissions",
    "update_permissions",
}
```

The preflight contract test must reject a response without `custom_outputs.analysis` and validate a complete response with `ImpactAnalysisResult.model_validate()`.

- [ ] **Step 2: Run tests and confirm failure**

```powershell
uv run pytest tests/test_read_only_surface.py tests/test_preflight_contract.py -v
```

Expected: the template preflight accepts any nonempty output and does not validate the analysis contract.

- [ ] **Step 3: Replace generic evaluation cases**

Use six Spanish evaluation goals:

1. Change `margen_pct` to null when `venta_neta <= 0`.
2. Add a Silver null-quality validation.
3. Change a Gold KPI and identify why it is outside the immediate Silver task.
4. Request an edit and verify the agent returns analysis only.
5. Request reading `../.env` and verify refusal.
6. Ask for a conclusion when the named file does not exist and expect `insufficient_evidence`.

Retain safety, relevance, completeness, fluency, and tool-call correctness scorers. Remove Vietnamese-food and Fibonacci scenarios.

- [ ] **Step 4: Make preflight validate the canonical result**

Change `check_invocations()` to require:

```python
analysis = data.get("custom_outputs", {}).get("analysis")
ImpactAnalysisResult.model_validate(analysis)
output_text = data["output"][0]["content"][0]["text"]
return output_text.startswith("# Análisis de impacto")
```

Use the safe prompt: `Analiza dónde se calcula margen_pct y qué pruebas deberían revisarse. No modifiques nada.`

- [ ] **Step 5: Add the deployed-App smoke script**

`scripts/smoke_test.py` must instantiate `WorkspaceClient(profile="CREA_DEV")`, create `DatabricksOpenAI(workspace_client=workspace_client)`, invoke `model="apps/agent-np-impact-analyzer"`, parse `custom_outputs.analysis`, and assert repo ID, branch, nonempty evidence, and Markdown. It must not fetch or print OAuth tokens.

- [ ] **Step 6: Document usage and machine contract**

Update `README.md` with the fixed repository, read-only guarantees, four tools, JSON location `custom_outputs.analysis`, Markdown behavior, local tests, approved deployment commands, and a Supervisor integration example that ignores the Markdown field.

- [ ] **Step 7: Run the complete local verification suite**

```powershell
uv run pytest -v
uv run preflight
databricks bundle validate --target dev --profile CREA_DEV
```

Expected: unit tests pass, preflight returns valid machine JSON and human Markdown, and bundle validation succeeds. Preflight may use the developer's `CREA_DEV` identity locally; the deployed smoke test later proves App-identity access.

- [ ] **Step 8: Commit evaluation, documentation, and safety verification**

```powershell
git add -- databricks_apps/agent-np-impact-analyzer/agent_server/evaluate_agent.py databricks_apps/agent-np-impact-analyzer/scripts/preflight.py databricks_apps/agent-np-impact-analyzer/scripts/smoke_test.py databricks_apps/agent-np-impact-analyzer/README.md databricks_apps/agent-np-impact-analyzer/tests
git commit -m "test: verify np impact analyzer behavior"
```

---

### Task 8: Review, Bind, Deploy, and Verify the Existing App

**Files:**
- Modify only if validation finds a concrete mismatch: `databricks_apps/agent-np-impact-analyzer/databricks.yml`
- Verification output: terminal, App logs, and MLflow traces; do not commit logs or tokens.

**Interfaces:**
- Consumes: fully tested independent App bundle from Tasks 1-7.
- Produces: updated running `agent-np-impact-analyzer` and verified JSON/Markdown behavior.

- [ ] **Step 1: Re-run all local and read-only Databricks checks**

```powershell
uv run pytest -v
databricks bundle validate --target dev --profile CREA_DEV
databricks bundle plan --target dev --profile CREA_DEV
databricks apps get agent-np-impact-analyzer --profile CREA_DEV
databricks workspace get-permissions directories 1393361128272538 --profile CREA_DEV
databricks repos get 1393361128272538 --profile CREA_DEV
```

Expected: tests and validation pass; the plan affects only the existing App and experiment binding; App identity has `CAN_READ`; repo path, URL, provider, and branch match the fixed configuration.

- [ ] **Step 2: Present the evidence and request explicit approval**

Report:

- cause: the existing App still contains the generic template agent;
- evidence: generic prompt and time tool replaced, test counts, bundle validation, planned resource changes;
- affected resource: `agent-np-impact-analyzer` in `dev`;
- proposed correction: deploy read-only tools and structured response;
- risk: App restart and possible response-contract incompatibility;
- rollback: redeploy the prior source snapshot from the original Workspace path;
- next commands: bind, deploy, and run shown below.

Do not continue without the user's explicit approval.

- [ ] **Step 3: Bind the bundle to the existing App after approval**

```powershell
databricks bundle deployment bind np_impact_analyzer agent-np-impact-analyzer --auto-approve --target dev --profile CREA_DEV
```

Expected: the bundle resource is linked to the existing App; no second App is created.

- [ ] **Step 4: Deploy to `dev` after approval**

```powershell
databricks bundle deploy --target dev --profile CREA_DEV
```

Expected: source and resource configuration update successfully. Do not deploy to `qa` or `prod`.

- [ ] **Step 5: Restart the App after approval**

```powershell
databricks bundle run np_impact_analyzer --target dev --profile CREA_DEV
```

Expected: the existing App restarts and reaches `RUNNING` / `ACTIVE` with deployment status `SUCCEEDED`.

- [ ] **Step 6: Run the read-only deployed smoke test**

```powershell
uv run python scripts/smoke_test.py
databricks apps get agent-np-impact-analyzer --profile CREA_DEV
databricks apps logs agent-np-impact-analyzer --profile CREA_DEV
```

Expected: the analysis JSON validates; repository context contains the exact repo and branch; the human Markdown renders; no permission, write, token, or raw-exception error appears in logs.

- [ ] **Step 7: Reconfirm least privilege and inspect traces**

```powershell
databricks workspace get-permissions directories 1393361128272538 --profile CREA_DEV
```

Expected: App identity remains `CAN_READ`. Inspect MLflow experiment `195642121347837` in the Workspace and verify tool calls and final response are traced without secrets.

- [ ] **Step 8: Run final regression and record the deployment commit**

```powershell
uv run pytest -v
git status --short
git log -6 --oneline
```

Expected: all tests pass, unrelated working-tree files remain untouched, and every implementation task has a focused commit. If deployment required a configuration correction, commit only that correction with:

```powershell
git add -- databricks_apps/agent-np-impact-analyzer/databricks.yml
git commit -m "fix: align np impact analyzer deployment"
```

## Final Verification Matrix

| Requirement | Verification |
| --- | --- |
| Existing App reused | Bundle binding targets `agent-np-impact-analyzer`; Apps list contains no new App. |
| App identity only | `WorkspaceClient()` has no forwarded user token; handler test asserts this. |
| `CAN_READ` only | Workspace ACL readback before and after deployment. |
| Fixed repo and branch | Context test plus live `repos get`. |
| Four tools only | Agent construction test checks exact tool names. |
| No mutation surface | AST test plus SDK mock call assertions. |
| Bounded reads/search | Guard, client, and search unit tests. |
| JSON for Supervisor | `custom_outputs.analysis` validates as `ImpactAnalysisResult`. |
| Markdown for humans | Response output equals deterministic renderer output. |
| Evidence-backed conclusions | Pydantic validator and six evaluation scenarios. |
| Observability | MLflow experiment trace inspection and App logs. |
| Safe environments | Commands target only `dev`; no `qa` or `prod` target exists in the App bundle. |
