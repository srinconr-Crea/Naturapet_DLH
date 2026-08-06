"""Deterministic human report rendering for canonical impact-analysis JSON."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent_server.schemas import ImpactAnalysisResult


def _bullet_list(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] or ["- Ninguno."]


def render_markdown(result: "ImpactAnalysisResult") -> str:
    """Render the human report solely from validated structured analysis fields."""
    lines = [
        "# Análisis de impacto",
        "",
        "## Solicitud",
        result.request_summary,
        "",
        "## Decisión",
        result.decision.value,
        "",
        "## Riesgo",
        f"Nivel: {result.risk.level.value}",
        *_bullet_list(result.risk.reasons),
        "",
        "## Evidencia",
    ]
    for evidence in result.evidence:
        location = evidence.relative_path
        if evidence.line_start is not None:
            location = f"{location}:{evidence.line_start}"
            if evidence.line_end is not None and evidence.line_end != evidence.line_start:
                location = f"{location}-{evidence.line_end}"
        lines.extend(
            [
                f"- `{location}` ({evidence.kind.value}): {evidence.finding}",
                f"  - Extracto: {evidence.excerpt}",
            ]
        )
    if not result.evidence:
        lines.append("- Ninguna.")

    lines.extend(["", "## Archivos objetivo"])
    lines.extend(
        [f"- `{item.relative_path}`: {item.reason}" for item in result.target_files]
        or ["- Ninguno."]
    )
    lines.extend(["", "## Archivos relacionados"])
    lines.extend(
        [f"- `{item.relative_path}`: {item.reason}" for item in result.related_files]
        or ["- Ninguno."]
    )
    lines.extend(["", "## Plan de implementación"])
    lines.extend(
        [
            f"{step.order}. {step.action} (`{', '.join(step.files)}`)"
            for step in result.implementation_plan
        ]
        or ["- Ninguno."]
    )
    for heading, items in (
        ("Criterios de aceptación", result.acceptance_criteria),
        ("Acciones prohibidas", result.prohibited_actions),
        ("Supuestos", result.assumptions),
        ("Advertencias", result.warnings),
    ):
        lines.extend(["", f"## {heading}", *_bullet_list(items)])
    return "\n".join(lines) + "\n"
