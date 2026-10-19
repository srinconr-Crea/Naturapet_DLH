# Preflight and Permissions

## Contents

1. Preflight sequence
2. Approval boundaries
3. Permission model
4. Stop conditions

## 1. Preflight sequence

Before implementation:

1. Read repository instructions and existing App/bundle source.
2. Confirm the target workspace, profile, bundle target, App name, and whether it already exists.
3. Inspect App identity, declared resources, status, permissions, and source configuration.
4. Confirm the model endpoint exists and is available to the chosen identity.
5. Inspect repository or Git Folder ACLs and exact allowed root/branch.
6. Validate required experiments, trace tables, catalogs, schemas, tables, warehouses, jobs, or MCP servers.
7. Run `bundle validate` and `bundle plan` for the authorized development target.
8. With explicit approval, make one minimal model call and test tool/structured-output compatibility.

Use `scripts/preflight.ps1` for deterministic read-only discovery. Pass every profile and bundle target explicitly. Pass `QueryPayloadPath` only after model-probe approval. Never infer an environment-specific value from this skill.

## 2. Approval boundaries

Read-only discovery does not authorize:

- changing App permissions or resources;
- importing or modifying Workspace objects;
- model inference that creates cost;
- local source changes when the user requested only analysis;
- bundle deploy, App restart, job run, repair, or data write;
- QA or production changes.

Request approval immediately before the first authorized mutation. An approval for one environment or App does not cover another.

## 3. Permission model

Prefer the App service principal for stable service behavior. Use on-behalf-of-user only when the business rule genuinely requires user-specific authorization.

Build a capability-to-permission matrix before granting access:

| Capability | Minimum permission family |
|---|---|
| Use model | Endpoint/model use |
| Read Git Folder | Workspace object view/read as exposed by UI/API |
| Read UC metadata | Catalog/schema/table browse or select as required |
| Write UC data | Explicit modify/write on named objects |
| Trace to MLflow | Experiment write plus required trace storage access |
| Run job | Can-run on named job |

Record UI label and effective API permission because they may use different names. Verify effective access using the App identity, not only the deploying user's identity.

## 4. Stop conditions

Do not start implementation when:

- the target App or source repository is ambiguous;
- the model cannot be queried by the runtime identity;
- tool calling and structured output are incompatible without an agreed fallback;
- repository root or branch cannot be bounded;
- required data access is broader than the stated role;
- bundle plan proposes unexpected changes;
- observability requires unapproved tables or permissions.

Report the failed check, evidence, affected resource, risk, and smallest next action.
