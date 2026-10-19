#!/usr/bin/env python3
"""Validate the reusable Databricks agent specification using only stdlib."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ALLOWED_MODES = {"single-agent", "sdd-flow"}
ALLOWED_IDENTITIES = {"app-service-principal", "on-behalf-of-user"}
ALLOWED_OUTPUTS = {"json", "text"}


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate(spec: Any) -> list[str]:
    if not isinstance(spec, dict):
        return ["The root must be a JSON object."]

    errors: list[str] = []
    if spec.get("schema_version") != "1.0":
        errors.append("schema_version must be '1.0'.")
    if spec.get("mode") not in ALLOWED_MODES:
        errors.append("mode must be 'single-agent' or 'sdd-flow'.")

    agent = spec.get("agent")
    if not isinstance(agent, dict):
        errors.append("agent must be an object.")
    else:
        for field in ("name", "role", "purpose", "model_endpoint"):
            if not _non_empty_string(agent.get(field)):
                errors.append(f"agent.{field} must be a non-empty string.")
        if agent.get("identity_mode") not in ALLOWED_IDENTITIES:
            errors.append("agent.identity_mode is unsupported.")
        if not isinstance(agent.get("existing_app"), bool):
            errors.append("agent.existing_app must be boolean.")

    scope = spec.get("scope")
    if not isinstance(scope, dict):
        errors.append("scope must be an object.")
    else:
        for field in ("environment", "databricks_profile", "bundle_target"):
            if not _non_empty_string(scope.get(field)):
                errors.append(f"scope.{field} must be a non-empty string.")
        allowed_paths = scope.get("allowed_paths")
        if not isinstance(allowed_paths, list) or not all(
            _non_empty_string(item) for item in allowed_paths
        ):
            errors.append("scope.allowed_paths must be a non-empty string list.")

    capabilities = spec.get("capabilities")
    if not isinstance(capabilities, list) or not all(
        _non_empty_string(item) for item in capabilities
    ):
        errors.append("capabilities must be a string list.")

    contract = spec.get("contract")
    if not isinstance(contract, dict):
        errors.append("contract must be an object.")
    else:
        if contract.get("canonical_output") not in ALLOWED_OUTPUTS:
            errors.append("contract.canonical_output must be 'json' or 'text'.")
        if not _non_empty_string(contract.get("failure_status")):
            errors.append("contract.failure_status must be a non-empty string.")

    approvals = spec.get("approvals")
    required_approvals = {
        "allow_model_probe",
        "allow_local_changes",
        "allow_permission_changes",
        "allow_deploy",
        "allow_run",
    }
    if not isinstance(approvals, dict):
        errors.append("approvals must be an object.")
    else:
        for field in sorted(required_approvals):
            if not isinstance(approvals.get(field), bool):
                errors.append(f"approvals.{field} must be boolean.")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="Path to agent-spec.json")
    args = parser.parse_args()

    try:
        spec = json.loads(args.spec.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2

    errors = validate(spec)
    if errors:
        for error in errors:
            print(f"INVALID: {error}", file=sys.stderr)
        return 1

    print("VALID: Databricks agent specification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
