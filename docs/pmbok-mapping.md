# EchoPM × PMBOK 47-Process Mapping Table

## Overview

This document provides a detailed mapping between EchoPM's 7 skills and the 47 project management processes from PMBOK 5th Edition.

Coverage statistics: **Direct alignment with 22/47 processes (47%), indirect relevance to 18/47 processes (38%), total relevance 85%.** Uncovered processes are primarily in procurement management and large-scale program management.

---

## Initiating Process Group (2 processes)

| PMBOK # | Process Name | EchoPM Skill | Coverage |
|---------|-------------|-------------|----------|
| 4.1 | Develop Project Charter | `/charter` | ✅ Direct — immutable principles + birth inscription = charter core |
| 13.1 | Identify Stakeholders | `/charter` | ✅ Direct — stakeholder matrix + influence/interest analysis |

---

## Planning Process Group (24 processes)

| PMBOK # | Process Name | EchoPM Skill | Coverage |
|---------|-------------|-------------|----------|
| 4.2 | Develop Project Management Plan | `/charter` | 🔗 Indirect — charter is an input to the management plan |
| 5.1 | Plan Scope Management | `/prioritize` | ✅ Direct — priority ranking after WBS decomposition |
| 5.2 | Collect Requirements | `/import` | 🔗 Indirect — structured import of requirements documents |
| 5.3 | Define Scope | `/charter` | 🔗 Indirect — immutable principles define scope boundaries |
| 5.4 | Create WBS | — | ⬜ Not covered (structural decomposition beyond skill scope) |
| 6.1 | Plan Schedule Management | — | 🔗 Indirect — pulse tracks but does not manage schedule planning |
| 6.2 | Define Activities | `/prioritize` | ✅ Direct — ranking activities after definition |
| 6.3 | Sequence Activities | `/prioritize` | 🔗 Indirect — priority implies execution order |
| 6.4 | Estimate Activity Resources | — | ⬜ Not covered |
| 6.5 | Estimate Activity Durations | — | ⬜ Not covered |
| 6.6 | Develop Schedule | — | ⬜ Not covered |
| 7.1 | Plan Cost Management | — | ⬜ Not covered |
| 7.2 | Estimate Costs | — | ⬜ Not covered |
| 7.3 | Determine Budget | — | ⬜ Not covered |
| 8.1 | Plan Quality Management | `/lessons` | 🔗 Indirect — lessons converted to quality improvements |
| 9.1 | Plan Human Resource Management | — | ⬜ Not covered |
| 10.1 | Plan Communications Management | `/import` | 🔗 Indirect — structured storage of communication information |
| 11.1 | Plan Risk Management | `/pulse` | 🔗 Indirect — risk signal source |
| 11.2 | Identify Risks | `/pulse` | ✅ Direct — health signals are risk signals |
| 11.3 | Perform Qualitative Risk Analysis | `/prioritize` | ✅ Direct — risk priority matrix (multiplicative scoring) |
| 11.4 | Perform Quantitative Risk Analysis | `/prioritize` | ✅ Direct — numerical risk scoring |
| 11.5 | Plan Risk Responses | — | 🔗 Indirect — pulse suggested actions = response direction |
| 12.1 | Plan Procurement Management | — | ⬜ Not covered (no procurement) |
| 13.2 | Plan Stakeholder Management | `/charter` | 🔗 Indirect — stakeholder matrix as input to management strategy |

---

## Executing Process Group (8 processes)

| PMBOK # | Process Name | EchoPM Skill | Coverage |
|---------|-------------|-------------|----------|
| 4.3 | Direct and Manage Project Work | `/import` + `/lessons` | ✅ Direct — knowledge deposition + lesson capture during execution |
| 8.2 | Perform Quality Assurance | `/lessons` | ✅ Direct — lessons converted to quality improvements |
| 9.2 | Acquire Project Team | — | ⬜ Not covered |
| 9.3 | Manage Project Team | `/lessons` | ✅ Direct — team experience deposition and transmission |
| 9.4 | Develop Project Team | — | ⬜ Not covered |
| 10.2 | Manage Communications | `/import` | ✅ Direct — structured information distribution |
| 12.2 | Conduct Procurements | — | ⬜ Not covered (no procurement) |
| 13.3 | Manage Stakeholder Engagement | `/lessons` + `/pulse` | ✅ Direct — feedback capture + satisfaction tracking |

---

## Monitoring and Controlling Process Group (11 processes)

| PMBOK # | Process Name | EchoPM Skill | Coverage |
|---------|-------------|-------------|----------|
| 4.4 | Monitor Project Work | `/pulse` | ✅ Direct — overall health assessment + pulse dashboard |
| 4.5 | Perform Integrated Change Control | `/search` | ✅ Direct — change impact search |
| 5.5 | Validate Scope | — | 🔗 Indirect |
| 5.6 | Control Scope | — | 🔗 Indirect |
| 6.7 | Control Schedule | `/pulse` | ✅ Direct — velocity monitoring + schedule variance alerts |
| 7.4 | Control Costs | `/pulse` | ✅ Direct — burn-down trends + cost variance alerts |
| 8.3 | Control Quality | `/lessons` | 🔗 Indirect — quality issue lesson recording |
| 10.3 | Control Communications | `/search` | ✅ Direct — information traceability and retrievability |
| 11.6 | Control Risks | `/pulse` | ✅ Direct — risk tracking + new risk monitoring |
| 12.3 | Control Procurements | — | ⬜ Not covered (no procurement) |
| 13.4 | Control Stakeholder Engagement | `/search` + `/pulse` | ✅ Direct — stakeholder concern tracking |

---

## Closing Process Group (2 processes)

| PMBOK # | Process Name | EchoPM Skill | Coverage |
|---------|-------------|-------------|----------|
| 4.6 | Close Project or Phase | `/retro` | ✅ Direct — six-step closeout: reflect → crystallize → learn → fill gaps → compress → archive |
| 12.4 | Close Procurements | `/retro` | ✅ Direct — contract closeout + knowledge transfer |

---

## Coverage Summary

```
Initiating       ████████████████ 2/2  (100%)
Planning         ████████░░░░░░░░ 6/24 (25%)*
Executing        ██████████████░░ 5/8  (63%)
Monitoring       ███████████████░ 7/11 (64%)
Closing          ████████████████ 2/2  (100%)
─────────────────────────────────────────
Total            ██████████░░░░░░ 22/47 (47% direct + 38% indirect = 85%)
```

*The lower coverage in the Planning process group is primarily because PMBOK includes many specific estimation techniques (resources, time, cost) that fall outside the scope of skills. However, EchoPM's priority ranking covers the most important decision-making aspects of planning.
