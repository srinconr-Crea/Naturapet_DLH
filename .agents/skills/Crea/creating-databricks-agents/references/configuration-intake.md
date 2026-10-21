# Configuration Intake

## Contents

1. Required values
2. Model-assisted discovery
3. Manual discovery
4. Collection rules

## 1. Required values

Collect and confirm these values before implementation:

| Value | Purpose | Required source |
|---|---|---|
| Workspace host | Select the Databricks workspace | Workspace URL or bundle |
| CLI profile | Authenticate CLI commands | `databricks auth profiles` or user |
| Environment and bundle target | Bound validation/deployment | `databricks.yml` or user |
| Bundle root | Locate `databricks.yml` | Local repository |
| App name and existing/new status | Modify or create the correct App | Apps UI/API or user |
| App source path/repository | Bound local changes | Existing App/bundle or user |
| Model endpoint | Select the runtime model | Serving UI/API or user |
| Identity mode | App principal or on-behalf-of-user | App design and user decision |
| Repository/Git Folder path, object ID, branch | Bound repository tools and ACL checks | Workspace UI/API or user |
| Capabilities and tools | Derive least privilege | Agent requirement |
| UC objects, warehouse, jobs, MCP resources | Grant only required access | Requirement and workspace inspection |
| MLflow experiment and trace tables | Configure observability | App/bundle or user |
| Approval flags | Bound probes, changes, deploys, and runs | Explicit user authorization |

Do not require irrelevant values. For example, an agent without data tools does not need catalogs or tables.

## 2. Model-assisted discovery

The model may perform read-only inspection when allowed:

1. Read repository instructions, `databricks.yml`, resource files, and existing App source.
2. Run `databricks auth profiles` without displaying configuration-file contents or secrets.
3. Use the candidate profile explicitly for `current-user me`, Apps, serving endpoints, Workspace, Unity Catalog, MLflow, jobs, and bundle discovery.
4. Present discovered candidates with their source; ask the user to select or confirm ambiguous values.
5. Write confirmed values into a copy of `assets/agent-spec.json` and validate it.

Discovery is evidence, not authorization. Finding a profile, resource, or target does not permit using it for mutation.

## 3. Manual discovery

A human can obtain the same values as follows:

- Workspace host: copy the browser URL through the workspace domain, excluding page-specific paths.
- CLI profile: run `databricks auth profiles`; provide only the profile name, never credentials.
- Bundle target and root: open `databricks.yml`; use a key under `targets` and the folder containing the file.
- App: open **Compute > Apps** and copy its exact name; note whether it already exists.
- Model: open the serving/model catalog interface and copy the exact endpoint name available to the App identity.
- Repository/Git Folder: open its Workspace page and copy path, object ID from the URL/API, and checked-out branch.
- Data and jobs: copy fully qualified catalog objects and exact job IDs/names from Catalog Explorer or Workflows.
- Observability: copy the MLflow experiment name/path and any trace table names from the App resources or experiment UI.

UI labels vary by Databricks release. Prefer exact names and IDs shown by the current workspace rather than guessing navigation labels.

## 4. Collection rules

- Ask one grouped configuration question when values are closely related; avoid many token-heavy confirmation rounds.
- Show a compact table: value, discovered candidate, source, status.
- Use placeholders when a value is unknown; do not invent it.
- Never request tokens, client secrets, passwords, `.databrickscfg` contents, or `.env` contents.
- Reconfirm only values changed by new evidence or scope.
- Stop before mutation until required values and approval flags are explicit.
