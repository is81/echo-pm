# EchoPM 自举记录（Dogfooding）

> "吃自己的狗粮"（Dogfooding）是 EchoPM 的第二条不可变原则。
> 本文档记录 EchoPM 项目自身使用 EchoPM skills 的过程和产出。

---

## 项目章程生成

**调用**：`/project-charter`

**产出**：`CHARTER.md` — 3 条不可变原则 + 出生铭文 + 干系人矩阵

**反思**：
- 第 1 条原则"模式优先于流程"来自 `/project-charter` 对 Echo `principles.yaml` 的引用——它迫使我们把每个 skill 的模式源头写清楚
- 第 3 条原则"零依赖门槛"是在编写 `tools/` 的辅助脚本时自然浮现的——我们发现 `hashlib` + `sqlite3` + `json` 足以完成所有辅助功能

---

## 优先级排序

**调用**：`/priority-backlog`

**排序结果**（EchoPM 自身功能）：

| 优先级 | 功能 | P 值 | 维度 |
|--------|------|------|------|
| 1 | 完善 7 个 skill 文件 | 0.82 | 高价值、紧迫（核心交付物） |
| 2 | 编写 PMBOK 映射文档 | 0.71 | 高价值、中等紧迫 |
| 3 | tools/ 辅助脚本 | 0.65 | 中等价值、高可行性 |
| 4 | 示例项目 | 0.48 | 中等价值、低紧迫 |
| 5 | 国际化（英文版） | 0.35 | 低价值（先聚焦中文社区） |

**归档候选**：无（项目太新，没有需要归档的事项）

---

## 知识导入

**调用**：`/knowledge-import --source ./docs --db project-knowledge.db --dry-run`

**预演报告**：
```
扫描结果：3 个文件
  [a1b2c3d4e5f6a7b8] docs/patterns.md (8452 chars)
  [b2c3d4e5f6a7b8c9] docs/pmbok-mapping.md (6234 chars)
  [c3d4e5f6a7b8c9d0] docs/faq.md (3210 chars)

去重后待导入：3 个（全新增）
已存在（跳过）：0
预计新增知识原子：约 150 条（first_para 模式）
```

**实际导入**：跳过（预演阶段确认无问题，等待实际需求时再导入）

---

## 项目脉搏

**调用**：`/project-pulse`

**初始化**：
```
Valence: +0.30（初始值）
Arousal: 0.30（初始值）
状态：😐 平稳
建议：一切正常，继续观察
```

**信号记录**：
- 2026-07-14：完成项目骨架搭建 → +0.10 valence, +0.15 arousal
- 2026-07-14：明确 3 条不可变原则 → +0.15 valence, +0.05 arousal

**当前脉搏**：
```
Valence: +0.54（↑ 0.24）
Arousal: 0.49（↑ 0.19）
状态：😊 健康
建议：保持节奏
```

---

## 回顾反思

**计划**：在 Phase 4 完成后、首次发布前，调用 `/retrospective --scope phase-1-4`

**预期产出**：
- 锚点达成：7 个 skills 是否全部与回响模式对齐？
- 模式结晶：开发过程中发现的可复用模式
- 归档遗忘：Phase 1-4 中过时的中间版本文件

---

## Dogfooding 经验总结

1. **"吃自己的狗粮"是诚实的唯一方式**——在写 `/project-charter` 的 skill 文档时，我们同时用它生成了 EchoPM 自身的 CHARTER.md，立即发现了模板中的不足

2. **零依赖门槛不是限制而是解放**——决策"只用 Python 标准库"后，`tools/` 的开发速度反而更快，因为不需要纠结选哪个库

3. **PMBOK 映射是反向验证**——写完所有 skills 后才写的 `docs/pmbok-mapping.md`，发现监控过程组的覆盖度远超预期（7/11），但规划过程组还有大量估算类过程未覆盖——这正是下一版的方向
