"""ASCII heading contract shared by local and deployed checks."""

import ast
from pathlib import Path


def _markdown_heading(source_path: Path) -> str:
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    return next(
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.startswith("#")
    )


def test_operational_checks_match_the_ascii_renderer_heading():
    """Operational checks use one ASCII-only heading to avoid encoding drift."""
    app_root = Path(__file__).parents[1]
    smoke_heading = _markdown_heading(app_root / "scripts" / "smoke_test.py")
    preflight_heading = _markdown_heading(app_root / "scripts" / "preflight.py")
    renderer_heading = _markdown_heading(
        app_root / "agent_server" / "output_renderer.py"
    )

    assert smoke_heading == preflight_heading == renderer_heading
    assert renderer_heading == "# Analisis de impacto"
    assert renderer_heading.isascii()


def test_agent_owned_operational_sources_are_ascii():
    app_root = Path(__file__).parents[1]
    paths = [
        app_root / "agent_server" / "agent.py",
        app_root / "agent_server" / "evaluate_agent.py",
        app_root / "agent_server" / "output_renderer.py",
        app_root / "scripts" / "preflight.py",
        app_root / "scripts" / "smoke_status.py",
        app_root / "scripts" / "smoke_test.py",
        app_root / "README.md",
        app_root / "agent-spec.json",
    ]

    assert all(path.read_text(encoding="utf-8").isascii() for path in paths)
