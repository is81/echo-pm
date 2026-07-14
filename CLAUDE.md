# CLAUDE.md — EchoPM 项目指南

## 项目概述

EchoPM（回响项目管理）是一套 Claude Code Skills，将回响计划（Project Echo）的设计模式抽象为覆盖 PMBOK 五大过程组的项目管理工具。核心理念：项目如同生命体——有基因、有记忆、有脉搏、有睡眠。

## 项目结构

```
echo-pm/
├── skills/          # Claude Code Skills（核心交付物，7 个 .md 文件）
├── templates/       # 配套模板（章程模板、原则 YAML、仪表盘等）
├── tools/           # 辅助 Python 脚本（零外部依赖）
├── examples/        # 使用示例（dogfooding 记录 + 示例项目）
└── docs/            # 理论文档（模式详解 + PMBOK 映射 + FAQ）
```

## Skill 开发规范

每个 skill 文件必须包含以下章节：
1. **触发条件**：何时自动激活
2. **对齐 PMBOK**：映射的过程编号和名称
3. **源自回响**：引用的 Project Echo 具体模式和源文件
4. **工作流**：分步骤的具体操作
5. **产出物**：skill 运行后生成的文件
6. **示例**：至少一个使用场景

## 关键约束

- Skill 核心功能零外部依赖（只用 Claude Code 内置能力）
- `tools/` 下的辅助脚本可以引入依赖，但必须在文件头部注释说明
- 每个 skill 必须引用回响计划的源文件作为模式出处
- 自身使用 EchoPM skills 管理开发（dogfooding）

## 常用命令

```bash
# 验证所有 skill 文件结构完整
grep -l "^## " skills/*.md

# 检查 PMBOK 覆盖率
python tools/check_coverage.py
```

## 相关项目

- 回响计划（Project Echo）：`F:\Project Echo` —— 模式源头
- 本项目的所有模式提取自 Echo 的以下文件：
  - `src/echo/memory/models.py` — 三因素优先级公式
  - `src/echo/agent/core.py` — 睡眠维护 + 双系统检索
  - `src/echo/memory/store.py` — 幂等导入管道
  - `config/principles.yaml` — 不可变原则
  - `src/echo/zim_ingest.py` — 多策略导入管道
