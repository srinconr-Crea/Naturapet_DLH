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
