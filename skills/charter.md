---
name: charter
description: Generate project charters, validate principles, report charter status.
argument-hint: "[mode:generate|check|report]"
---

# /charter

## Mode Detection

| User intent | Mode |
|-------------|------|
| "create/write/generate charter", "define principles" | **generate** |
| "check/validate/audit charter", "principles intact?" | **check** |
| "charter status/summary/overview" | **report** |

Default: generate if `CHARTER.md` missing, otherwise report.

## Generate Mode

1. Read `README.md` and `CLAUDE.md` if present.
2. Ask 4 questions (2 at a time):
   - "What 3-5 principles must NEVER change?"
   - "Why does this project exist, and why now? (one paragraph)"
   - "Who are the key stakeholders? (roles, not names)"
   - "What are 3-5 measurable success criteria?"
3. Write `CHARTER.md`: birth inscription, principles (name + one-sentence statement + rationale), stakeholder matrix (role|representative|concerns|engagement|influence|interest), success metrics checklist.
4. Write `config/principles.yaml`: each principle with `id, name, statement, rationale, immutable: true, added`.
5. Infer stakeholder influence/interest (H/M/L). Note assumptions if uncertain.

## Check Mode

1. Read `CHARTER.md` and `config/principles.yaml`. Error if missing.
2. Validate:

| Rule | Severity |
|------|----------|
| Principle count 3-5 | WARNING |
| Birth inscription ≤ 100 words | WARNING |
| Every principle has rationale | ERROR |
| No empty cells in stakeholder matrix | WARNING |
| Success metrics are measurable | INFO |
| principles.yaml entries match CHARTER.md | ERROR |
| No immutable principle changed since last commit (`git log -p -- CHARTER.md`) | ERROR |

3. Scan recent commits for principle violations (e.g., "zero deps" + new `package.json`).
4. Write `reports/charter-audit.md`: violations table (rule|severity|detail|fix), summary (X/Y passed).

## Report Mode

Read `CHARTER.md`. Extract: principle list, stakeholders by influence, metric completion (count [x] vs [ ]), last modified (`git log -1 --format=%ad`). Write `reports/charter-summary.md`.

## Outputs

- `CHARTER.md`, `config/principles.yaml` (generate)
- `reports/charter-audit.md` (check)
- `reports/charter-summary.md` (report)
