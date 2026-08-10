from types import SimpleNamespace

import pytest

from scripts.smoke_status import validate_app_status


def test_short_smoke_accepts_running_active_app():
    app = SimpleNamespace(
        app_status=SimpleNamespace(state=SimpleNamespace(value="RUNNING")),
        compute_status=SimpleNamespace(state=SimpleNamespace(value="ACTIVE")),
    )

    validate_app_status(app)


def test_short_smoke_rejects_non_running_app():
    app = SimpleNamespace(
        app_status=SimpleNamespace(state=SimpleNamespace(value="UNAVAILABLE")),
        compute_status=SimpleNamespace(state=SimpleNamespace(value="ACTIVE")),
    )

    with pytest.raises(AssertionError, match="RUNNING"):
        validate_app_status(app)
