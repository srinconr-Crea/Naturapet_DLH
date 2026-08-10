#!/usr/bin/env python3
"""Low-cost App status smoke test that performs no model inference."""

from databricks.sdk import WorkspaceClient


APP_NAME = "agent-np-impact-analyzer"
PROFILE = "CREA_DEV"


def _state_value(value: object) -> str:
    state = getattr(value, "value", value)
    return str(state).upper()


def validate_app_status(app: object) -> None:
    """Require the deployed App process and compute to be available."""
    app_state = _state_value(getattr(getattr(app, "app_status", None), "state", None))
    compute_state = _state_value(
        getattr(getattr(app, "compute_status", None), "state", None)
    )
    assert app_state == "RUNNING", f"Expected App state RUNNING, received {app_state}."
    assert compute_state == "ACTIVE", (
        f"Expected compute state ACTIVE, received {compute_state}."
    )


def main() -> None:
    """Read App status with CREA_DEV and avoid any invocation or model cost."""
    app = WorkspaceClient(profile=PROFILE).apps.get(APP_NAME)
    validate_app_status(app)
    print("Short App status smoke passed without model inference.")


if __name__ == "__main__":
    main()
