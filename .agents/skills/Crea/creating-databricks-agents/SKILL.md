---
name: creating-databricks-agents
description: Use when creating, extending, or standardizing Databricks Apps that host custom agents, including individual roles and multi-agent Spec-Driven Development flows coordinated by a Supervisor.
---

# Creating Databricks Agents

## Overview

Create Databricks agents from an explicit specification, with live feasibility checks before implementation and verification proportional to risk. Keep role behavior replaceable; do not clone an impact-analyzer architecture blindly.

## Select the Mode

- `single-agent`: create or modify one App for one configurable role.
- `sdd-flow`: design several specialized Apps and their Supervisor integration.

Start with `single-agent` when the user has authorized only one App. Preserve contracts that allow later assembly into `sdd-flow`.

## Four-Phase Workflow

### 1. Preflight and scope

Read repository instructions, `databricks.yml`, `resources/`, App configuration, and involved source. Modify an existing App instead of creating a duplicate.

Follow `references/configuration-intake.md`; ask for missing values or discover and confirm them. Copy `assets/agent-spec.json`, complete it, then run `scripts/validate_agent_spec.py`. Read `references/preflight-and-permissions.md`. Require approval for model inference, deploy, restart, runs, permission changes, or data writes.

Stop when the model, App identity, required resources, tool/output compatibility, or permissions cannot be verified.

### 2. Contract and architecture

Define the role, instructions, input/output schemas, tools, capability boundaries, failure contract, evidence rules, and Supervisor handoff. Use `references/architecture.md` to choose role and capability packs. Grant the App identity only the permissions required by those capabilities.

### 3. Implementation

Reuse the existing App or an official current Databricks template. Separate shared runtime code from role-specific instructions, tools, and schemas. Treat repository paths, branches, catalogs, endpoints, and experiment names as configuration. Keep structured JSON canonical; derive human-readable Markdown from it when both are needed.

Use test-first development for behavior. Implement one phase at a time and avoid speculative abstractions.

### 4. Verification and delivery

Apply `references/verification-policy.md`. Run the smallest check that can detect the current defect. Run the full suite only at milestones, not after every literal or documentation edit. Use one independent review per phase; re-review only the corrected finding unless the fix changes architecture.

Before deploy, require a clean full suite, bundle validation, bundle plan, permission review, and explicit user approval. After deploy and App restart, run one short smoke before the complete functional smoke; inspect logs and final ACLs.

## Efficiency Contract

- Keep at most four implementation phases.
- Target 25–40 high-value tests initially; add a test for a discovered defect or meaningful invariant.
- Run full suites after client/tools, before deploy, and after the last significant fix.
- Do not repeat unchanged evidence, reviews, or reports.
- Do not use a powerful model for deterministic validation that a script can perform.
- Pause when the next action needs new authority or materially changes scope.

## Resources

- `assets/agent-spec.json`: reusable role and capability specification.
- `scripts/validate_agent_spec.py`: deterministic specification validator.
- `scripts/preflight.ps1`: safe Databricks discovery and bundle checks.
- `references/configuration-intake.md`: required values and manual/model discovery.
- `references/architecture.md`: modes, role packs, contracts, and layout.
- `references/preflight-and-permissions.md`: live checks and least privilege.
- `references/verification-policy.md`: risk-based test and review matrix.
