import json
from pathlib import Path


def test_agent_spec_captures_the_deployed_single_agent_contract():
    spec_path = Path(__file__).parents[1] / "agent-spec.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))

    assert spec["schema_version"] == "1.0"
    assert spec["mode"] == "single-agent"
    assert spec["agent"] == {
        "name": "agent-np-impact-analyzer",
        "role": "impact-analyst",
        "purpose": (
            "Produce an evidence-backed, read-only impact analysis for the "
            "authorized Naturapet_DLH branch."
        ),
        "existing_app": True,
        "model_endpoint": "databricks-claude-sonnet-4-6",
        "identity_mode": "app-service-principal",
    }
    assert spec["scope"]["branch"] == "practica-margen-silver"
    assert spec["capabilities"] == ["repository-read"]
    assert spec["contract"]["canonical_output"] == "json"
    assert spec["contract"]["failure_status"] == "insufficient_evidence"
    assert spec["approvals"]["allow_deploy"] is False
