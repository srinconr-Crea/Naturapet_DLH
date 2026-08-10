from uuid import UUID

import pytest
from pydantic import ValidationError

from agent_server.output_renderer import render_markdown
from agent_server.schemas import (
    Decision,
    EvidenceItem,
    EvidenceKind,
    FileReference,
    ImpactAnalysisDraft,
    ImplementationStep,
    RiskAssessment,
    RiskLevel,
    finalize_analysis,
)


@pytest.fixture
def repository_context():
    return {
        "repo_id": 1393361128272538,
        "path": "/Workspace/Naturapet_BI/practica-margen-silver",
        "url": "https://github.com/srinconr-Crea/Naturapet_DLH.git",
        "provider": "gitHub",
        "branch": "practica-margen-silver",
        "head_commit_id": "abc123",
    }


@pytest.fixture
def sample_draft():
    return ImpactAnalysisDraft(
        request_summary="Agregar una columna de margen.",
        decision=Decision.FEASIBLE_WITH_CONDITIONS,
        risk=RiskAssessment(level=RiskLevel.MEDIUM, reasons=["Requiere backfill."]),
        target_files=[FileReference(relative_path="src/margin.py", reason="Transformación")],
        related_files=[FileReference(relative_path="tests/test_margin.py", reason="Cobertura")],
        evidence=[
            EvidenceItem(
                relative_path="src/margin.py",
                line_start=12,
                line_end=16,
                excerpt="def calculate_margin(...)",
                finding="La transformación ya calcula ingresos.",
                kind=EvidenceKind.DIRECT,
            )
        ],
        implementation_plan=[
            ImplementationStep(order=1, action="Agregar la columna.", files=["src/margin.py"])
        ],
        acceptance_criteria=["La columna se calcula para cada fila."],
        prohibited_actions=["No ejecutar notebooks."],
        assumptions=["Los ingresos están disponibles."],
        warnings=["Validar el backfill."],
    )


@pytest.mark.parametrize("decision", list(Decision))
@pytest.mark.parametrize("risk_level", list(RiskLevel))
def test_draft_accepts_every_documented_decision_and_risk_level(decision, risk_level):
    draft = ImpactAnalysisDraft(
        request_summary="Cambio solicitado",
        decision=decision,
        risk=RiskAssessment(level=risk_level, reasons=["Motivo comprobable"]),
        target_files=[],
        related_files=[],
        evidence=[] if decision is Decision.INSUFFICIENT_EVIDENCE else [
            EvidenceItem(
                relative_path="src/module.py",
                excerpt="constante",
                finding="Hallazgo",
                kind=EvidenceKind.INFERENCE,
            )
        ],
        implementation_plan=[],
        acceptance_criteria=[],
        prohibited_actions=[],
        assumptions=[],
        warnings=[],
    )

    assert draft.decision is decision
    assert draft.risk.level is risk_level


def test_draft_rejects_missing_evidence_for_supported_conclusion():
    with pytest.raises(ValidationError, match="evidence"):
        ImpactAnalysisDraft(
            request_summary="Cambio solicitado",
            decision=Decision.FEASIBLE,
            risk=RiskAssessment(level=RiskLevel.LOW, reasons=["Motivo"]),
            target_files=[],
            related_files=[],
            evidence=[],
            implementation_plan=[],
            acceptance_criteria=[],
            prohibited_actions=[],
            assumptions=[],
            warnings=[],
        )


@pytest.mark.parametrize("invalid_path", ["/src/module.py", "../secreto.py", "src/../../secreto.py"])
def test_output_rejects_paths_outside_repository(invalid_path):
    with pytest.raises(ValidationError, match="relative path"):
        FileReference(relative_path=invalid_path, reason="No permitido")


@pytest.mark.parametrize("invalid_path", ["src\\module.py", "C:/src/module.py", ""])
def test_output_rejects_nonportable_paths_in_every_cited_file_field(invalid_path):
    with pytest.raises(ValidationError, match="relative path"):
        FileReference(relative_path=invalid_path, reason="No permitido")
    with pytest.raises(ValidationError, match="relative path"):
        ImplementationStep(order=1, action="Cambio", files=[invalid_path])


def test_evidence_rejects_line_end_before_line_start():
    with pytest.raises(ValidationError, match="line_end"):
        EvidenceItem(
            relative_path="src/module.py",
            line_start=8,
            line_end=7,
            excerpt="contenido",
            finding="Hallazgo",
            kind=EvidenceKind.DIRECT,
        )


def test_evidence_rejects_line_end_without_line_start():
    with pytest.raises(ValidationError, match="line_start"):
        EvidenceItem(
            relative_path="src/module.py",
            line_end=8,
            excerpt="contenido",
            finding="Hallazgo",
            kind=EvidenceKind.DIRECT,
        )


def test_finalize_analysis_adds_verified_context_and_markdown(sample_draft, repository_context):
    result = finalize_analysis(sample_draft, repository_context)

    assert result.schema_version == "1.0"
    assert result.repository_context.model_dump() == repository_context
    assert UUID(result.analysis_id).version == 4
    assert result.status == "completed"
    assert result.human_report_markdown == render_markdown(result)


def test_markdown_is_not_an_independent_input(sample_draft, repository_context):
    first = finalize_analysis(sample_draft, repository_context)
    second = first.model_copy(update={"human_report_markdown": "alterado"})

    assert render_markdown(second) == render_markdown(first)


def test_markdown_renders_every_human_facing_analysis_section(sample_draft, repository_context):
    markdown = render_markdown(finalize_analysis(sample_draft, repository_context))

    for heading in (
        "Solicitud",
        "Decision",
        "Riesgo",
        "Evidencia",
        "Archivos objetivo",
        "Archivos relacionados",
        "Plan de implementacion",
        "Criterios de aceptacion",
        "Acciones prohibidas",
        "Supuestos",
        "Advertencias",
    ):
        assert heading in markdown
