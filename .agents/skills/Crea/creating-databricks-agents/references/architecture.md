# Architecture Reference

## Contents

1. Modes
2. Role packs
3. Capability packs
4. Agent contract
5. Suggested layout

## 1. Modes

### `single-agent`

Use for one Databricks App with one primary responsibility. It may later become a Supervisor subagent, so keep its input/output contract independent from its UI.

### `sdd-flow`

Use when the requested outcome needs distinct responsibilities, permissions, or validation boundaries. Prefer separate Apps when roles need different privileges or independent deployment. A typical flow is:

`impact analyst -> architect/planner -> developer -> validator/reviewer`

The Supervisor routes work and state; it must not silently broaden a subagent's permissions.

## 2. Role packs

| Role | Primary output | Typical authority |
|---|---|---|
| Impact analyst | Evidence-backed impact report | Read repository and metadata |
| Architect/planner | Approved specification and plan | Read-only |
| Developer | Patch and focused test evidence | Scoped repository write |
| Validator | Test, bundle, and smoke verdict | Read plus approved execution |
| Reviewer | Findings and decision | Read-only |
| Custom | User-defined schema | Explicitly declared |

Role packs configure instructions, schemas, and selected tools. They are not separate hard-coded architectures.

## 3. Capability packs

| Capability | Example operations | Boundary |
|---|---|---|
| `repository-read` | list, search, read, current branch | Allowed root and branch |
| `repository-write` | apply patch | Approved files; no push by default |
| `test-execution` | focused tests, bundle checks | Allowlisted commands |
| `unity-catalog-read` | list schemas/tables, sample metadata | Named catalogs and schemas |
| `data-read` | bounded query | Named objects and row/column limits |
| `job-execution` | run/repair | Explicit approval and job allowlist |
| `mcp-tooling` | external controlled tools | Declared server and methods |

Never infer write authority from read authority. Keep permissions aligned to capabilities.

## 4. Agent contract

Each agent specification must define:

- purpose and non-goals;
- input schema and canonical output schema;
- evidence and citation requirements;
- allowed tools and per-tool bounds;
- identity and resource permissions;
- canonical failure status without raw internal errors;
- Supervisor handoff fields;
- observability destinations;
- approval gates.

Prefer canonical structured output. If humans require Markdown, render it from the validated structured result rather than generating two independent answers.

## 5. Suggested layout

```text
agent-app/
  agent_server/
    agent.py
    config.py
    schemas.py
    tools/
  tests/
  scripts/
  app.yaml
  databricks.yml
  pyproject.toml
```

Keep shared runtime concerns separate from role-specific instructions, tool registration, and schemas. Use configuration for repository path, branch, model endpoint, catalog, experiment, and tool limits.
