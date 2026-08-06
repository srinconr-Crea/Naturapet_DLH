# Task 8: pre-deploy scope alignment

## Cause probable

The existing App retained the default user API scopes
`iam.access-control:read` and `iam.current-user:read`, even though this agent
runs under its App service-principal identity and its production modules do
not use on-behalf-of-user authorization.

## Evidence found

- Live evidence supplied for the pre-deploy review: `databricks apps get
  agent-np-impact-analyzer --profile CREA_DEV` reported
  `effective_user_api_scopes: [iam.access-control:read, iam.current-user:read]`.
- `README.md` states that the deployed App uses its own service-principal
  identity and does not use OBO.
- `tests/test_read_only_surface.py` rejects OBO authorization helpers from
  production modules.
- The local bundle schema supports
  `resources.apps.<key>.user_api_scopes`.

## Local change

`databricks.yml` now declares `user_api_scopes: []` under
`resources.apps.np_impact_analyzer`. This is the only deployment-resource
change; the app name, resources, ACLs, source path, and identity are
unchanged. `tests/test_config.py` now asserts the empty list so a future
configuration edit cannot silently restore user API scopes.

## Verification

| Check | Result |
| --- | --- |
| Focused no-cache test: `uv run pytest tests/test_config.py -p no:cacheprovider` | Passed: 2 tests |
| Full no-cache test: `uv run pytest -p no:cacheprovider` | 103 passed; 1 environment error. Pytest could not access its `tmp_path` directory because of local Windows filesystem permissions. The error is unrelated to this change. |
| `databricks bundle validate --target dev --profile CREA_DEV` | Passed, with two warnings that the now-absent `.pytest_cache` exclusion patterns match no files. |
| `databricks bundle plan --target dev --profile CREA_DEV` | Succeeded: `create apps.np_impact_analyzer` |

The plan can show `create` before the existing App has been bound to this
bundle. It does not indicate that a remote change was made.

## Risk

The next bind/deploy should reconcile the declared empty list and remove the
two effective user API scopes. The app will no longer receive user API tokens,
which is aligned with its App-only, non-OBO implementation. No remote resource
was changed during this preparation.

## Next recommended command

After explicit human approval, bind the existing App before deploying:

```powershell
databricks bundle deployment bind np_impact_analyzer agent-np-impact-analyzer --auto-approve --target dev --profile CREA_DEV
```

Then review a fresh plan and obtain approval for deployment. Do not run this
command as part of this pre-deploy change.
