---
name: charter
description: Generate, validate, and audit project charters with immutable principles and stakeholder matrices.
argument-hint: "[mode:generate|check|report]"
---

# /charter

## Purpose

This skill produces and validates project charters. In generate mode, it asks targeted questions and writes a complete `CHARTER.md` and `config/principles.yaml`. In check mode, it audits an existing charter for structural integrity and consistency. In report mode, it produces a one-page charter summary.

## Modes

### Mode 1: Generate (default)

**What it does:**

1. **Scout existing project context:**
   - Read `README.md` if it exists (Glob + Read) to understand the project
   - Read `CLAUDE.md` if it exists for development conventions
   - Check if `CHARTER.md` already exists (warn before overwriting)

2. **Ask 4 blocking questions** (use AskUserQuestion, 2 at a time):

   **Batch 1:**
   - "What 3-5 principles must NEVER change for this project? (Things you'd bet the project on.)"
   - "In one paragraph: why does this project exist, and why now?"

   **Batch 2:**
   - "Who are the key stakeholders? List roles, not names (e.g., 'Product Owner', 'Tech Lead', 'End Users')."
   - "What are 3-5 measurable success criteria? (e.g., '3 real projects adopt this', 'Coverage ≥ 80%')"

3. **Synthesize and write:**

   **`CHARTER.md`:**
   ```markdown
   # [Project Name] Project Charter
   > immutable: true | Established: YYYY-MM-DD | Version: 1.0

   ## Birth Inscription
   [User's origin narrative, verbatim or lightly edited]

   ## Immutable Principles
   ### Principle N: [Name]
   [One-sentence statement]
   **Why It's Immutable:** [Rationale]

   ## Stakeholder Matrix
   | Role | Representative | Concerns | Engagement | Influence | Interest |

   ## Success Metrics
   - [ ] [Metric 1]
   ```

   **`config/principles.yaml`:**
   ```yaml
   principles:
     - id: "principle-1"
       name: "..."
       statement: "..."
       rationale: "..."
       immutable: true
       added: "YYYY-MM-DD"
   ```

4. **Assign stakeholder ratings** (influence/interest: High/Medium/Low) based on the described roles. If uncertain, note assumptions.

**Output:**
- `CHARTER.md` — full charter
- `config/principles.yaml` — machine-readable principles

---

### Mode 2: Check

**What it does:**

1. **Read** `CHARTER.md` and `config/principles.yaml` (report error if missing)

2. **Validate against these rules:**

   | Rule | Severity | Check |
   |------|----------|-------|
   | Principle count 3-5 | WARNING | < 3 = too few, > 5 = unfocused |
   | Birth inscription ≤ 100 words | WARNING | Count words, flag if over |
   | All principles have rationale | ERROR | Missing rationale = incomplete |
   | Stakeholder matrix complete | WARNING | Empty cells flagged |
   | Success metrics are measurable | INFO | Vague metrics flagged ("improve X" without target) |
   | principles.yaml matches CHARTER.md | ERROR | ID mismatch, missing entries |
   | Immutable principles unchanged since last commit | ERROR | Run `git log -p -- CHARTER.md`, check if `immutable` sections changed |
   | At least one stakeholder with High influence | INFO | If all are Low, flag |

3. **Scan for principle violations in recent changes:**
   - Run `git log --oneline -20` to get recent commits
   - For each principle, check if any recent commit message or changed file suggests a violation
   - Example: If a principle says "zero external dependencies" and `package.json` was added, flag it

4. **Write** `reports/charter-audit.md`:
   ```markdown
   # Charter Audit — YYYY-MM-DD
   ## Violations
   | # | Rule | Severity | Detail | Fix |
   ## Warnings
   | # | Rule | Detail | Fix |
   ## Info
   | # | Rule | Detail |
   ## Summary
   Passed: X/Y checks. N errors, M warnings.
   ```

**Output:** `reports/charter-audit.md`

---

### Mode 3: Report

**What it does:**

1. **Read** `CHARTER.md`

2. **Extract and summarize:**
   - Principle list (names only + one-line each)
   - Stakeholder map (group by influence level)
   - Success metric completion (count [x] vs [ ])
   - Last modified date (from git: `git log -1 --format=%ad -- CHARTER.md`)

3. **Write** `reports/charter-summary.md`:
   ```markdown
   # Charter Summary — [Project Name]
   **Last updated:** YYYY-MM-DD
   **Version:** X.X

   ## Principles (N)
   1. **Name** — one-line summary

   ## Stakeholders
   - High Influence (M): ...
   - Medium Influence (N): ...

   ## Success Metrics
   X of Y complete (Z%)

   ## Charter Health
   - Age: N days since last update
   - Principle changes in last 90 days: N
   ```

**Output:** `reports/charter-summary.md`

---

## Mode Detection

| User says | Mode |
|-----------|------|
| "create/write/generate/start a charter", "define principles", "project charter" | generate |
| "check/validate/audit charter", "are my principles intact", "charter violations" | check |
| "charter status/summary/overview", "what's in our charter" | report |

If unclear, default to generate if no `CHARTER.md` exists, otherwise report.

## Outputs

| File | Mode |
|------|------|
| `CHARTER.md` | generate |
| `config/principles.yaml` | generate |
| `reports/charter-audit.md` | check |
| `reports/charter-summary.md` | report |

## Trigger Conditions

Activate when the user says: "project charter", "define principles", "write a charter", "create a charter", "charter", "immutable rules", "project constitution", "validate charter", "check principles", "charter audit", "charter status", "project principles".
