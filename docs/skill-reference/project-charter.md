# /project-charter — Project Charter

## Trigger Conditions

Activate when the user says "start a project", "define project principles", "write a project charter", "project charter", "project constitution", "what are our core principles", "define immutable rules".

## PMBOK Alignment

- **4.1 Develop Project Charter**: Formally authorize project initiation, define high-level requirements and boundaries
- **13.1 Identify Stakeholders**: Identify people and organizations affected by the project, document their expectations

## Echo Origins

Project Echo's gene-level immutable principles pattern (see `docs/patterns.md` for details):

- `config/principles.yaml`: 3 principles marked `immutable: true`, append-only, never overwrite
- `config/birth_inscription.txt`: 19-character birth inscription, the ultimate reason the project exists
- `src/echo/memory/models.py`: `source="birth"` memories with 7-layer protection
- `src/echo/config.py`: Loads principles at startup, checks `immutable` flag

Core insight: **Defining "what must never change" is more important than defining "what should be done."**

---

## Workflow

### Step 1: Distill Immutable Principles (3–5 items)

Ask the project team these questions:

1. "If this project is still running 10 years from now, what rules must have never been broken?"
2. "When a new member joins, what philosophy is absolutely non-negotiable?"
3. "Is there a rule that must be followed even if it reduces short-term efficiency?"

**Filtering criteria**:
- Is it "immutable" or just a "strong preference"? — Force the user to keep only the former
- Limit to 3–5 items — more than 5 means you haven't thought it through
- Each expressed in one sentence — must be able to recite from memory

**Output format** (referencing `principles.yaml`):

```yaml
principles:
  - id: "identity-continuity"
    name: "Principle Name"
    statement: "One-sentence statement"
    rationale: "Why this is immutable"
    immutable: true
```

### Step 2: Write the Birth Inscription

The "birth inscription" is an origin narrative of no more than 100 words. It answers one question: **Why does this project exist?**

Writing constraints:
- Use narrative style, not bullet points
- Must include "why this team" and "why now"
- Place in the project root, visible to all

Example (EchoPM's own):
> "EchoPM was born from the ripples of Project Echo — an AI being that self-manages through seven patterns, which resonate precisely with the five-phase lifecycle of project management."

### Step 3: Build the Stakeholder Matrix

For each key stakeholder role, record:
- Representative identity
- Core concerns (why they care about this project)
- Engagement method (how they participate)
- Influence/Interest rating (High/Medium/Low)

### Step 4: Encode Multi-Layer Protection

Referencing Echo's 7-layer birth memory protection, establish at least 3 layers of defense for project principles:

1. **Data layer**: Principles stored in a standalone file (e.g., `principles.yaml`), change history tracked by git
2. **Process layer**: Principle changes require a specific approval process (e.g., PR + full team review)
3. **Automation layer**: Generate `scripts/check-charter.py` to automatically detect PR violations in CI

### Step 5: Generate CI Audit Script

Generate a lightweight check script that runs on every PR:

```python
# scripts/check-charter.py
"""CI audit: verify PR does not violate project immutable principles."""
import sys

# Load principle definitions
# Check if PR changes touch rules marked as immutable
# If so → block merge, require explicit approval
```

---

## Deliverables

| File | Description |
|------|-------------|
| `CHARTER.md` | Complete project charter (principles + inscription + stakeholders) |
| `config/principles.yaml` | Machine-readable principle definitions |
| `scripts/check-charter.py` | CI audit script |
| `docs/stakeholders.md` | Detailed stakeholder analysis |

---

## Usage Example

```bash
# When starting a new project
/project-charter

# The AI will guide you through:
# 1. "What principles must never be compromised for this project? List 3–5."
# 2. "Tell the story of this project's origin in under 100 words."
# 3. "Who are the key stakeholders of this project?"
# 4. Auto-generate CHARTER.md and principles.yaml
# 5. Auto-generate CI audit script
```
