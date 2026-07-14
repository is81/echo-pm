# /knowledge-import — 知识导入

## 触发条件

当用户说"导入文档"、"批量导入"、"知识库"、"ingest"、"import data"、"把这些文档导入"、"抓取内容"、"同步文档"、"建立知识库"时激活。

## 对齐 PMBOK

- **4.3 指导与管理项目工作**：执行过程中产生的知识需要结构化沉淀
- **10.2 管理沟通**：将信息以结构化方式分发给需要的人

## 源自回响

Project Echo 的 ZIM Wikipedia 导入管道 + 内容哈希幂等去重（详见 `docs/patterns.md`）：

- `src/echo/zim_ingest.py`：多策略发现（命名空间扫描 → 标题关键词 fallback）、可配置内容模式、预演模式
- `src/echo/memory/store.py` L173-223：`bulk_insert()` — SHA256 内容哈希 + UNIQUE INDEX + INSERT OR IGNORE + 批量事务
- `src/echo/zim_reader.py`：多后端（libzim → fallback → 提示安装命令）

核心洞察：**让导入可安全重复执行是设计层面的决定，不是应用层的约定。数据库层强制执行唯一性。**

---

## 工作流

### 第一步：盘点导入源

识别所有需要导入的外部知识来源：

| 来源类型 | 示例 | 策略 |
|---------|------|------|
| 需求文档 | PRD.md, spec.pdf | 全文导入 |
| 会议纪要 | meeting-*.md | 摘要导入 |
| 技术方案 | design-*.md | 全文导入 |
| API 文档 | swagger.json | 结构化提取 |
| 代码注释 | docstrings | 提取关键片段 |
| 外部参考 | RFC, 论文, 博客 | 基于话题筛选 |

### 第二步：定义内容身份标识

确定"两个文档是同一个"的判断标准：

**参考 Echo 的方案**：
```python
content_hash = SHA256(content)[:16]  # 64 bits
```

对于你的场景，可选的身份标识策略：
- `SHA256(content)` — 内容完全相同时去重
- `SHA256(path + content)` — 同路径同内容才去重（允许文档迁移）
- `(business_key, version)` — 业务主键去重（允许内容迭代）

### 第三步：建立数据库层唯一性约束

**关键设计原则**：去重由数据库引擎强制执行，不是应用层 check-then-insert。

```sql
CREATE TABLE knowledge_base (
    id INTEGER PRIMARY KEY,
    content_hash TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT,
    content_mode TEXT,      -- full / summary / title_only
    tags TEXT,              -- JSON array
    base_weight REAL DEFAULT 0.5,
    created_at REAL DEFAULT (UNIXEPOCH())
);

CREATE UNIQUE INDEX idx_content_hash ON knowledge_base(content_hash);
```

Python 插入代码：
```python
# 使用 INSERT OR IGNORE（SQLite）或 ON CONFLICT DO NOTHING（PostgreSQL）
conn.execute(
    "INSERT OR IGNORE INTO knowledge_base (content_hash, content, source) "
    "VALUES (?, ?, ?)",
    (hash, text, source_path)
)
```

### 第四步：实现分批事务导入

**关键设计**：每个批次独立事务，一个批次失败不影响其他。逐条 try/except IntegrityError 允许部分成功。

```python
for batch in chunks(items, batch_size=500):
    conn.execute("BEGIN")
    for item in batch:
        try:
            insert_one(item)
        except IntegrityError:
            stats.skipped += 1   # 重复，跳过
        except Exception:
            stats.failed += 1    # 异常，记录后继续
    conn.commit()
```

### 第五步：启用预演模式

在真正导入前，先扫描并报告：

```
预演报告
════════
扫描路径：./docs/, ./meetings/
发现文件：142 个
去重后待导入：87 个
已存在（跳过）：55 个
预计新增：约 45,000 条知识原子
内容模式：first_para（首段模式）

确认导入？[y/N]
```

### 第六步：设计多策略发现 + Fallback

**参考 Echo 的双策略**：V namespace 索引 → 标题关键词扫描

通用化为：

```
策略 A（优先）：结构化元数据提取（目录索引、frontmatter、API schema）
    ↓ 失败/不可用
策略 B（备用）：文件系统扫描 + 文件名关键词匹配
    ↓ 失败/不可用
策略 C（兜底）：全量遍历 + MIME type 过滤
```

每种策略独立运行，记录成功/失败数。最终报告三种策略各自的成果。

---

## 产出物

| 文件 | 说明 |
|------|------|
| `tools/hash_dedup.py` | 内容哈希去重导入工具 |
| `schema.sql` | 知识库表结构（含 UNIQUE INDEX） |
| 导入报告 | 预演 + 最终导入统计 |

---

## 使用示例

```bash
# 将全部文档导入项目知识库
/knowledge-import --source ./docs --db project-knowledge.db

# 先预览
/knowledge-import --source ./docs --dry-run

# 指定内容模式（仅标题+首句）
/knowledge-import --source ./meetings --mode summary

# AI 会：
# 1. 扫描源目录，列出所有文件
# 2. 计算去重统计
# 3. 预演报告（如果 --dry-run）
# 4. 分批导入，显示进度
# 5. 输出导入统计报告
```
