# Risk-Based Verification Policy

## Contents

1. Change matrix
2. Milestones
3. Review policy
4. Token and execution budget
5. Evidence format

## 1. Change matrix

| Change | Required verification |
|---|---|
| Documentation, prompt wording, or literal | One focused check |
| YAML or resource configuration | Configuration test plus `bundle validate` |
| Path guard, secret guard, client, or read tool | Affected module tests |
| Input/output or Supervisor contract | Agent and schema tests |
| Permission or identity behavior | Focused test plus live read-only preflight |
| Architectural change | Full suite plus one independent review |
| Predeploy | Full suite, validate, plan, permission review |
| Postdeploy | Short smoke, logs; then final functional smoke and ACL review |

A new regression test is justified by a discovered defect or a durable invariant. Do not add tests solely to increase the count.

## 2. Milestones

Use no more than four:

1. synchronization and configuration;
2. client and tools;
3. agent and output contract;
4. deploy and smoke.

Run the complete local suite primarily after client/tools, before deployment, and after the last significant fix. A focused test is sufficient between those milestones when the change cannot affect broader behavior.

## 3. Review policy

Use one independent review per phase. If a review finds a defect, correct it and re-review only that finding. Repeat the full review only when the correction changes architecture, permissions, public contracts, or multiple modules.

Do not create one review agent per commit. Do not reproduce unchanged evidence in every report.

## 4. Token and execution budget

- Target 25–40 selected tests for a new agent before production-specific regressions.
- Use deterministic scripts for schema, configuration, path, and permission-manifest checks.
- Use the smallest capable model for mechanical validation; reserve stronger models for architecture, adversarial review, and ambiguous reasoning.
- Batch independent read-only discovery commands.
- Stop repeating a passing check unless relevant code changed or it is a release gate.
- Keep reports delta-based: outcome, new evidence, residual risk, next gate.

Safety gates override the budget. Never skip the full predeploy suite or approved postdeploy smoke merely to save tokens.

## 5. Evidence format

For each phase record only:

```text
scope:
checks_run:
result:
new_findings:
residual_risk:
next_gate:
```

If a check was not run, state why. Do not claim live validation from mocks or static inspection.
