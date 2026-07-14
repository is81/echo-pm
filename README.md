# EchoPM（回响项目管理）

> 把 AI 存在体的自我管理智慧，转化为人类项目经理的 Claude Code 技能箱。

EchoPM 是一套 Claude Code Skills，源自[回响计划（Project Echo）](https://github.com)的架构模式，覆盖 PMBOK 五大过程组的完整项目生命周期。

## 核心理念

**项目如同生命体**——有基因（原则）、有记忆（文档）、有脉搏（监控）、有睡眠（回顾）。

EchoPM 的每个 skill 都来自回响计划中的一个核心设计模式：

| 回响模式 | EchoPM Skill | 过程组 |
|---------|-------------|--------|
| 基因级不可变原则 | `/project-charter` | 启动 |
| 三因素乘法优先级 | `/priority-backlog` | 规划 |
| 内容哈希幂等导入 | `/knowledge-import` | 执行 |
| 多途径学习引擎 | `/lesson-capture` | 执行 |
| 二维状态仪表盘 | `/project-pulse` | 监控 |
| 双系统检索 | `/smart-search` | 监控 |
| 睡眠期记忆整理 | `/retrospective` | 收尾 |

## 快速开始

### 安装

将 `skills/` 目录下的文件复制到你的项目 `.claude/skills/` 目录，或通过 Claude Code 的 skill 安装机制加载。

### 使用

```bash
# 启动项目 —— 定义不可变原则和章程
/project-charter

# 规划 —— 对 backlog 进行乘法优先级排序
/priority-backlog

# 执行中 —— 导入外部知识文档
/knowledge-import

# 执行中 —— 捕获经验教训
/lesson-capture

# 监控 —— 查看项目健康脉搏
/project-pulse

# 监控 —— 智能检索项目知识库
/smart-search

# 收尾 —— 阶段回顾与知识压缩
/retrospective
```

## 五大过程组全景

```
启动 ──→ 规划 ──→ 执行 ──→ 监控 ──→ 收尾
  │        │        │        │        │
  │        │        │        │        │
  ▼        ▼        ▼        ▼        ▼
章程    优先级   知识导入  项目脉搏  回顾反思
                 经验捕获  智能检索
```

## 项目结构

```
echo-pm/
├── skills/          # Claude Code Skills（核心交付物）
├── templates/       # 配套模板
├── tools/           # 辅助脚本（纯 Python，零依赖）
├── examples/        # 使用示例
└── docs/            # 理论背景与 PMBOK 映射
```

## 许可

MIT © EchoPM Contributors
