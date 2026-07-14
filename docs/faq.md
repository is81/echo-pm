# EchoPM 常见问题

## Q: EchoPM 和传统项目管理工具有什么不同？

EchoPM 不是 Jira、Trello、Asana 的替代品。它是一套**认知工具**——帮助你思考项目管理中的"为什么"和"什么最重要"，而非管理"谁在什么时候做什么"。

核心差异：
- 传统工具：追踪任务状态
- EchoPM：理解项目健康度、优先级逻辑、知识结构

## Q: 我必须懂 PMBOK 才能用 EchoPM 吗？

不需要。PMBOK 映射是给熟悉它的人作为参考的。每个 skill 的设计自包含，你只需要说"帮我排优先级"或"生成项目脉搏报告"。

## Q: 我需要安装什么？

零。所有 skills 的核心工作流只使用 Claude Code 的内置能力。

`tools/` 目录下的 Python 脚本是可选的辅助工具，如果你想要独立的计算能力。它们也都只依赖 Python 3.8+ 标准库。

## Q: 我可以只用一个 skill 吗？

可以。7 个 skills 相互独立，按需使用。但配合使用效果更好：
- `/project-charter` 定义的原则会被 `/retrospective` 的锚点反思步骤引用
- `/knowledge-import` 建立的知识库是 `/smart-search` 的检索对象
- `/priority-backlog` 的评分结果会被 `/project-pulse` 的 arousal 信号引用

## Q: EchoPM 自身怎么管理开发？

我们用 EchoPM 管理 EchoPM（dogfooding）：
- CHARTER.md 由 `/project-charter` 生成
- 功能优先级由 `/priority-backlog` 排序
- 每次发布前跑 `/retrospective`
- `.echo-pm/pulse.json` 追踪项目健康度

## Q: 怎么贡献？

1. Fork 仓库
2. 选择一个你想改进的 skill 或新增一个 skill
3. 确保新 skill 遵循 `docs/patterns.md` 中的模式
4. 提交 PR，附带使用该 skill 的实际案例
5. 确保与 PMBOK 的过程对齐（更新 `docs/pmbok-mapping.md`）

## Q: 为什么叫 EchoPM？

Echo（回响）来自回响计划（Project Echo），我们从中提取了这些模式。PM 是 Project Management 的缩写。

"回响"（Echo）也暗示了核心理念：好的管理就像回声——你说出意图，系统回应结构。不是控制，而是共鸣。

## Q: 这些模式真的能用于非软件项目吗？

可以。虽然模式源自软件工程，但核心逻辑是通用的：
- 不可变原则：适用于任何有宪章/章程的组织
- 三因素优先级：适用于任何需要多维排序的场景
- 经验捕获：适用于任何知识密集型工作
- 项目脉搏：适用于任何有"健康度"概念的团队
