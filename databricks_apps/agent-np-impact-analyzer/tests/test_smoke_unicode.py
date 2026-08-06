"""Unicode contract between the deployed smoke test and human report renderer."""

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


def test_smoke_heading_matches_the_renderer_unicode_heading():
    """A valid human report must not fail smoke because of mojibake codepoints."""
    app_root = Path(__file__).parents[1]
    smoke_heading = _markdown_heading(app_root / "scripts" / "smoke_test.py")
    renderer_heading = _markdown_heading(
        app_root / "agent_server" / "output_renderer.py"
    )

    assert smoke_heading == renderer_heading == "# Análisis de impacto"
