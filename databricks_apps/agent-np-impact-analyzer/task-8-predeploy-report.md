# Task 8: provider-compatible App scope configuration

## Cause probable

The deployment provider cannot reconcile an explicitly empty App
`user_api_scopes` list. The authorized deployment failed because the planned
value was `[]` while the provider read back `null`:

```text
.user_api_scopes was [] but now null
```

This is a provider consistency issue, not an indication that the App needs
user authorization or that its service-principal identity changed.

## Evidence found

- Databricks documentation confirms that, when no user API scopes are
  selected, Apps receive the default scopes `iam.access-control:read` and
  `iam.current-user:read`.
- Those defaults are IAM metadata reads only; they do not grant data or
  compute access.
- The live App retains those default effective scopes.
- `README.md` documents that the deployed App uses its own service-principal
  identity, without on-behalf-of-user authorization.
- `tests/test_read_only_surface.py` continues to reject OBO helpers from all
  production modules (apart from the quarantined legacy helper itself).

## Workaround applied

`resources.apps.np_impact_analyzer.user_api_scopes` is deliberately absent
from `databricks.yml`. Omitting the unsupported empty-list declaration avoids
the provider's `[]` versus `null` inconsistency while preserving Databricks'
safe default IAM scopes.

`tests/test_config.py` now asserts that the field is absent. The existing
production OBO guard remains in place, so the bundle configuration and code
continue to express the same App-only, non-OBO boundary.

## TDD evidence

1. **RED** — after changing the test to require omission, the focused test
   failed against the previous `user_api_scopes: []` declaration with:
   `AssertionError: assert 'user_api_scopes' not in ...`.
2. **GREEN** — after removing only that declaration, the focused no-cache
   command `uv run pytest tests/test_config.py -p no:cacheprovider` passed:
   `2 passed`.

## Verification

| Check | Result |
| --- | --- |
| Focused configuration test: `uv run pytest tests/test_config.py -p no:cacheprovider` | Passed: 2 tests |
| Productive non-OBO guard: `uv run pytest tests/test_read_only_surface.py::test_production_modules_do_not_import_or_call_user_authorization_helpers -p no:cacheprovider` | Passed: 1 test |
| Full no-cache suite: `uv run pytest -p no:cacheprovider` | 103 passed; 1 environment error. Pytest cannot access its Windows `tmp_path` directory. The failure is unrelated to this configuration change. |
| `databricks bundle validate --target dev --profile CREA_DEV` | Passed, with two warnings because the excluded `.pytest_cache` patterns match no local files. |
| `databricks bundle plan --target dev --profile CREA_DEV` | Succeeded: 0 to add, 0 to change, 0 to delete, 1 unchanged. |

No bind, deploy, run, or smoke test is part of this workaround.

## Risk

The effective default IAM scopes will remain visible after deployment; this
workaround does not and must not claim to remove them. Their presence is safe
for this App-only implementation and does not enable OBO, data access, or
compute access. The relevant residual risk is a future code change that adds
OBO behavior, which the existing production guardrail is designed to catch.

## Next recommended command

After a human reviews the fresh plan, use the normal approved deployment
workflow for `dev`. Do not issue a bind, deploy, run, or smoke-test command as
part of this configuration-only pre-deploy round.
