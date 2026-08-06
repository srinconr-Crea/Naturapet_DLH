"""Static guardrail for the repository SDK surface.

The app service principal is intentionally limited to repository reads.  This
test catches a future accidental addition of a mutation endpoint before it can
reach an App deployment.
"""

import ast
from pathlib import Path


FORBIDDEN_CALLS = {
    "upload",
    "upload_from",
    "import_",
    "delete",
    "mkdirs",
    "update",
    "create",
    "run_now",
    "repair_run",
    "deploy",
    "set_permissions",
    "update_permissions",
}

FORBIDDEN_OBO_NAMES = {
    "get_user_workspace_client",
    "get_request_headers",
}


def test_repository_modules_expose_no_mutating_sdk_calls():
    """Reject a repository implementation that gains a mutating SDK call."""
    repository_dir = Path(__file__).parents[1] / "agent_server" / "repository"
    forbidden_calls: list[str] = []

    for source_path in repository_dir.glob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        forbidden_calls.extend(
            f"{source_path.name}:{node.lineno}:{node.attr}"
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in FORBIDDEN_CALLS
        )

    assert forbidden_calls == []


def test_production_modules_do_not_import_or_call_user_authorization_helpers():
    """The App agent cannot reach the legacy OBO helper retained in utils.py."""
    agent_server_dir = Path(__file__).parents[1] / "agent_server"
    violations: list[str] = []

    for source_path in agent_server_dir.rglob("*.py"):
        if source_path.name == "utils.py":
            continue
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "agent_server.utils":
                    violations.append(f"{source_path.name}:{node.lineno}:utils-import")
                for imported_name in node.names:
                    if imported_name.name in FORBIDDEN_OBO_NAMES:
                        violations.append(
                            f"{source_path.name}:{node.lineno}:{imported_name.name}"
                        )
            if isinstance(node, ast.Call):
                called_name = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else node.func.attr
                    if isinstance(node.func, ast.Attribute)
                    else None
                )
                if called_name in FORBIDDEN_OBO_NAMES:
                    violations.append(f"{source_path.name}:{node.lineno}:{called_name}")

    assert violations == []
