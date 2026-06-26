# DocHub — 团队知识库管理插件设计规格

**Date:** 2026-06-26  
**Type:** Feature Design  
**Status:** Draft — Pending Review  
**Version:** 1.0  
**Related Spec:** [Agents Develop Environment Design](2025-06-25-agents-develop-environment-design.md)

---

## 1. 概述

### 1.1 设计目标

为 `agents-develop` 增加一个名为 **DocHub** 的整体业务插件，作为团队本地知识库的中枢。DocHub 以 Markdown 技术文档为主，支持团队成员在本地管理文档、按最佳实践分类、基于混合搜索快速查找内容，并通过 **Model Context Protocol (MCP)** 暴露给 Claude、Cursor、ZCode 等 AI 工具。

### 1.2 核心能力

| 能力 | 说明 |
|---|---|
| **文档管理** | 本地 Markdown 文档的创建、读取、更新、删除；支持可选的 PDF/DOCX 解析 |
| **增量协作** | 主文档（Master Doc）+ 贡献者增量补充（Contributor Addendum）模型，避免覆盖冲突 |
| **智能搜索** | 关键词搜索 + 语义向量搜索 + 混合搜索（Hybrid Search）+ RAG 问答 |
| **定向索引** | 按文档类型、作者、贡献者、SessionID、标签建立多层索引 |
| **MCP 服务** | 暴露文档查询、搜索、创建、补充等工具给 AI 客户端 |
| **动态 Prompt 模板** | 基于 Jinja2，根据检索结果和上下文动态组装提示词 |
| **AI Skill 文件** | 自动生成 Claude SKILL.md、Cursor SKILL.md、ZCode Command.md、MCP server.py |

### 1.3 与现有架构的融合

DocHub 作为 `agents-develop` 生态中的一个组件，遵循项目已有的 **Core + Format Separation** 架构：

- **Core 层**：工具无关的文档管理、索引、搜索逻辑，位于 `agents_dev/docs/`。
- **Format 层**：通过 `migration/generators/` 生成 Claude、Cursor、ZCode、MCP 等工具特定文件。
- **CLI 层**：通过 `agents-dev docs ...` 子命令使用。

DocHub MCP Server 继承现有 `core/mcp_base/server.py` 中的 `MCPServerBase`，工具定义使用 `MCPToolDefinition`。

---

## 2. 核心数据模型

### 2.1 主文档（Master Document）

主文档是知识库的基础单元，由创建者首次创建，原作者可追加更新。

```python
class MasterDocument(BaseModel):
    doc_id: str                       # URL-safe 唯一标识，如 "api_deploy"
    title: str
    author: str                       # 创建成员
    doc_type: str                     # tutorial | how-to | reference | explanation
    session_id: Optional[str]         # 可选，关联会话
    tags: List[str] = []
    summary: Optional[str]            # 文档摘要
    created_at: datetime
    updated_at: datetime
    content_path: Path                # 本地 Markdown 文件路径
    addendums: Dict[str, Addendum] = {}  # contributor -> Addendum
```

### 2.2 增量补充（Contributor Addendum）

每个辅助者针对同一件事的补充只有一个增量文档，后续更新覆盖或追加到同一文件，同时保留历史快照。

```python
class Addendum(BaseModel):
    addendum_id: str                  # 如 "api_deploy.bob"
    parent_doc_id: str
    contributor: str                  # 贡献者标识
    summary: str                      # 本次补充说明
    created_at: datetime
    updated_at: datetime
    content_path: Path
    versions: List[str] = []          # 历史快照文件名列表
```

### 2.3 索引文档块（Index Chunk）

用于搜索引擎的最小单位。

```python
class DocChunk(BaseModel):
    chunk_id: str                     # 全局唯一
    doc_id: str                       # 所属主文档
    doc_title: str
    doc_type: str
    author: str
    contributor: Optional[str]        # 主文档为 null，增量补充为 contributor
    session_id: Optional[str]
    tags: List[str]
    heading_path: List[str]           # 标题层级路径
    content: str
    source_path: Path
```

---

## 3. 存储与目录结构

### 3.1 知识库目录

```
team-kb/
├── dochub.yaml                 # DocHub 配置文件
├── index/
│   ├── meilisearch/            # Meilisearch 数据（可选）
│   └── chroma/                 # ChromaDB 数据（可选）
├── docs/
│   ├── master/
│   │   ├── api_deploy.md
│   │   └── api_deploy.meta.json
│   └── addendums/
│       ├── api_deploy.bob.md
│       └── api_deploy.bob.meta.json
└── sessions/
    └── sess_001.json           # 会话与文档关联索引
```

### 3.2 元数据文件示例

`docs/master/api_deploy.meta.json`：

```json
{
  "doc_id": "api_deploy",
  "title": "API 部署流程",
  "author": "alice",
  "doc_type": "how-to",
  "session_id": "sess_001",
  "tags": ["api", "deploy"],
  "summary": "API 服务从构建到上线的完整流程",
  "created_at": "2026-06-26T10:00:00Z",
  "updated_at": "2026-06-26T14:00:00Z",
  "addendums": {
    "bob": {
      "contributor": "bob",
      "summary": "补充 Docker 部署方式",
      "created_at": "2026-06-26T12:00:00Z",
      "updated_at": "2026-06-26T15:00:00Z"
    }
  }
}
```

---

## 4. 文档分类与增量协作规则

### 4.1 Diátaxis 文档分类

所有主文档必须属于以下四类之一：

| 类型 | 用途 | 示例 |
|---|---|---|
| `tutorial` | 教学型，手把手带领新手完成 | "30 分钟入门 agents-dev" |
| `how-to` | 问题导向型，解决具体任务 | "如何部署 API" |
| `reference` | 参考型，精确技术事实 | "CLI 命令参考" |
| `explanation` | 解释型，阐述原理与设计 | "为什么选择 Core+Format 架构" |

### 4.2 增量协作规则

| 操作 | 行为 |
|---|---|
| 创建主文档 | 生成 `doc_id`，文件存入 `docs/master/`，建立 `meta.json` |
| 原作者更新主文档 | 在原 Markdown 追加 `---update---` 区块，更新 `updated_at` |
| 辅助者首次补充 | 创建 `docs/addendums/<doc_id>.<contributor>.md`，登记到主文档 `addendums` |
| 辅助者再次补充同一件事 | 覆盖/追加到同一增量文件，旧版本保存为 `.v1.md`、`.v2.md` 等快照 |
| 查询时 | 默认返回主文档 + 所有增量补充；可按 `contributor` 筛选 |

---

## 5. 索引与搜索架构

### 5.1 三层索引策略

| 索引层 | 技术选型 | 用途 | 降级方案 |
|---|---|---|---|
| 关键词索引 | Meilisearch | 快速全文搜索、拼写容错、筛选、排序 | SQLite FTS5 |
| 向量语义索引 | ChromaDB | 语义相似度搜索、RAG 上下文召回 | 禁用（纯关键词搜索） |
| 元数据索引 | 与关键词索引共存 | 按作者、贡献者、SessionID、类型、标签筛选 | SQLite 表 |

### 5.2 文档处理流水线

```
原始文档 (Markdown / PDF / DOCX)
    ↓
解析（Markdown → AST / Docling → DoclingDocument）
    ↓
元数据提取（标题、作者、标签、摘要、SessionID）
    ↓
分块（按标题层级 + 语义边界）
    ↓
生成 embedding
    ↓
写入 Meilisearch + ChromaDB
```

### 5.3 分块策略

- 主文档按 H1/H2/H3 标题边界分块。
- 每个增量补充作为一个独立 chunk。
- Chunk 大小：512–1024 tokens，重叠 100–200 tokens。
- 每个 chunk 必须携带完整元数据：`doc_id`、`doc_type`、`author`、`contributor`、`session_id`、`heading_path`、`tags`。

### 5.4 搜索模式

| 模式 | 说明 |
|---|---|
| `keyword` | Meilisearch 全文召回 |
| `semantic` | ChromaDB 向量语义召回 |
| `hybrid` | 关键词 Top-K + 向量 Top-K，使用 RRF（Reciprocal Rank Fusion）融合排序 |
| `rag` | 混合召回 → Prompt 组装 → LLM 生成答案 |

### 5.5 筛选能力

支持以下过滤条件：

- `author:<成员>`
- `contributor:<成员>`
- `session_id:<会话ID>`
- `doc_type:<类型>`
- `tag:<标签>`
- 组合筛选：`author:alice AND tag:api`

### 5.6 定向索引

- **类型目录索引**：按 tutorial/how-to/reference/explanation 分组。
- **贡献者索引**：每个贡献者的增量补充单独成组，便于查看某人所有补充。
- **会话索引**：同一会话产生的文档/补充关联。
- **标签分面**：支持多标签组合筛选。
- **热门查询缓存**：记录常见查询并预热索引。

---

## 6. MCP 服务设计

### 6.1 服务器基类

`DocHubMCPServer` 继承现有 `core/mcp_base/server.py` 中的 `MCPServerBase`：

```python
class DocHubMCPServer(MCPServerBase):
    def __init__(self, config: DocHubConfig):
        super().__init__("dochub", version="1.0.0")
        self.store = DocumentStore(config.docs_path)
        self.searcher = HybridSearcher(config)
        self.renderer = PromptRenderer(config.templates_path)
        self._register_tools()
```

### 6.2 暴露的工具

| 工具名 | 描述 | 输入参数 |
|---|---|---|
| `doc_search` | 混合搜索文档块 | `query`, `mode` (keyword/semantic/hybrid), `filters`, `limit` |
| `doc_query` | RAG 问答 | `question`, `context_limit`, `filters` |
| `doc_read` | 读取主文档或增量补充 | `doc_id`, `addendum_id` (可选) |
| `doc_create` | 创建主文档 | `title`, `content`, `author`, `doc_type`, `tags`, `session_id`, `summary` |
| `doc_update_master` | 原作者在主文档追加更新 | `doc_id`, `content_delta`, `summary` |
| `doc_add_addendum` | 添加/更新贡献者增量补充 | `parent_doc_id`, `contributor`, `content`, `summary` |
| `doc_index_status` | 查看索引状态 | `doc_id` (可选) |
| `doc_list_sessions` | 按 SessionID 列出相关文档 | `session_id`, `filters` |

### 6.3 工具定义示例

```python
MCPToolDefinition(
    name="doc_search",
    description="Search the DocHub knowledge base using keyword, semantic, or hybrid search.",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "mode": {"type": "string", "enum": ["keyword", "semantic", "hybrid"], "default": "hybrid"},
            "filters": {"type": "object"},
            "limit": {"type": "integer", "default": 10}
        },
        "required": ["query"]
    }
)
```

---

## 7. 动态 Prompt 模板

### 7.1 模板引擎

使用 **Jinja2** 作为模板引擎，与项目现有 `formats/` 模板保持一致，并兼容 LlamaIndex `RichPromptTemplate` 风格。

### 7.2 模板文件

存放于 `agents_dev/docs/prompts/templates/`：

| 模板文件 | 用途 |
|---|---|
| `search_context.j2` | 将搜索结果格式化为 LLM 上下文 |
| `rag_answer.j2` | 基于检索结果生成答案 |
| `addendum_suggest.j2` | 根据代码/修改生成增量补充建议 |
| `doc_summarize.j2` | 总结主文档 + 所有增量补充 |
| `session_recap.j2` | 基于 SessionID 汇总相关文档 |

### 7.3 模板渲染器

```python
class PromptRenderer:
    def __init__(self, templates_path: Path):
        self.env = Environment(loader=FileSystemLoader(templates_path))

    def render(self, template_name: str, **context) -> str:
        template = self.env.get_template(f"{template_name}.j2")
        return template.render(**context)
```

### 7.4 `search_context.j2` 示例

```jinja2
以下是知识库中检索到的相关文档片段：
{% for chunk in chunks %}
---
[来源] {{ chunk.doc_title }}
[类型] {{ chunk.doc_type }}
{% if chunk.contributor %}[贡献者] {{ chunk.contributor }}{% else %}[作者] {{ chunk.author }}{% endif %}
[路径] {{ chunk.heading_path | join(' > ') }}
{{ chunk.content }}
{% endfor %}

请根据以上信息回答：
{{ query }}
```

---

## 8. Python 工具集

### 8.1 模块结构

```
agents_dev/docs/
├── __init__.py
├── config.py                 # DocHubConfig
├── models.py                 # MasterDocument / Addendum / DocChunk
├── store.py                  # DocumentStore
├── indexer/
│   ├── __init__.py
│   ├── base.py               # IndexBackend ABC
│   ├── meilisearch_idx.py    # MeilisearchIndex
│   ├── sqlite_idx.py         # SQLiteFTS5Index（降级）
│   ├── chroma_idx.py         # ChromaIndex
│   └── hybrid.py             # HybridSearcher
├── parser/
│   ├── __init__.py
│   ├── markdown_parser.py
│   └── docling_adapter.py    # 可选 PDF/DOCX 解析
├── chunker.py                # MarkdownChunker
├── prompts/
│   ├── __init__.py
│   ├── loader.py             # PromptRenderer
│   └── templates/
├── mcp/
│   ├── __init__.py
│   ├── server.py             # DocHubMCPServer
│   └── tools.py              # DocHub 工具实现
└── cli/
    ├── __init__.py
    ├── init_cmd.py
    ├── add_cmd.py
    ├── search_cmd.py
    ├── ask_cmd.py
    ├── update_cmd.py
    ├── addendum_cmd.py
    └── serve_cmd.py
```

### 8.2 核心类职责

| 类 | 职责 |
|---|---|
| `DocHubConfig` | 加载 `dochub.yaml`，管理索引后端、embedding 模型、分块参数 |
| `DocumentStore` | 本地文档 CRUD、主文档/增量关系管理、元数据持久化 |
| `MarkdownChunker` | 按标题层级分块，保留 heading_path 和元数据 |
| `MeilisearchIndex` | 关键词索引的增删改查 |
| `SQLiteFTS5Index` | 无外部服务时的关键词索引降级 |
| `ChromaIndex` | 向量索引与语义搜索 |
| `HybridSearcher` | 混合召回、RRF 融合、元数据过滤 |
| `PromptRenderer` | Jinja2 模板加载与渲染 |
| `DocHubMCPServer` | MCP 服务器，注册并调度所有工具 |

---

## 9. CLI 设计

DocHub 作为 `agents-dev` CLI 的子命令 `docs`。

### 9.1 命令列表

```bash
# 初始化知识库
agents-dev docs init --path ./team-kb

# 添加主文档
agents-dev docs add master \
  --title "API 部署流程" \
  --author alice \
  --type how-to \
  --tags api,deploy \
  --session-id sess_001 \
  --file deploy.md

# 原作者更新主文档
agents-dev docs update-master <doc_id> \
  --file delta.md \
  --summary "增加回滚步骤"

# 添加/更新贡献者增量补充
agents-dev docs add-addendum <doc_id> \
  --contributor bob \
  --file bob_updates.md \
  --summary "补充 Docker 部署方式"

# 全文/语义/混合搜索
agents-dev docs search "如何部署 API" \
  --mode hybrid \
  --author alice \
  --contributor bob \
  --session-id sess_001 \
  --limit 10

# RAG 问答
agents-dev docs ask "部署 API 的步骤是什么？" \
  --session-id sess_001

# 按 SessionID 列出文档
agents-dev docs list-sessions --session-id sess_001

# 启动 MCP 服务器
agents-dev docs serve --transport stdio --config ./team-kb/dochub.yaml
```

### 9.2 输出格式

默认使用 Rich 表格输出搜索结果，支持 `--json` 输出机器可读格式。

---

## 10. AI Skill 文件生成

通过 `agents-develop` 的 migration 层，DocHub 生成以下工具格式文件：

| 工具 | 生成文件 |
|---|---|
| Claude | `components/dochub/formats/claude/SKILL.md` |
| Cursor | `components/dochub/formats/cursor/SKILL.md` + `cursor_config.json` |
| ZCode | `components/dochub/formats/zcode/Command.md` |
| MCP | `components/dochub/formats/mcp/mcp_server.py` + `mcp_config.json` |
| Reasionix | `components/dochub/formats/reasionix/script.py` |

### 10.1 Claude SKILL.md 要点

- 说明 DocHub 的文档模型（主文档 + 增量补充）
- 提供 `doc_search`、`doc_query`、`doc_read` 等工具调用示例
- 说明如何根据 SessionID 和贡献者筛选结果
- 说明 Diátaxis 分类约定

---

## 11. 依赖策略

### 11.1 核心依赖（必须）

这些依赖项目前已存在或体量小：

```toml
"markdown"              # Markdown 解析
"python-frontmatter"    # YAML frontmatter 解析
"pydantic"              # 已存在
"jinja2"                # 已存在
"rich"                  # 已存在
"click"                 # 已存在
```

### 11.2 可选依赖

```toml
"meilisearch-python"    # 关键词索引
"chromadb"              # 向量索引
"sentence-transformers" # 本地 embedding 模型
"docling"               # PDF/DOCX 解析
"marker-pdf"            # 备选 PDF 解析
```

### 11.3 降级策略

当可选依赖不可用时：

- 关键词索引降级为 SQLite FTS5。
- 向量索引禁用，搜索模式自动回退到 `keyword`。
- PDF/DOCX 解析报错并提示安装 `docling` 或 `marker-pdf`。

---

## 12. 错误处理

沿用并扩展项目现有错误层次：

```python
AgentsDevelopError
├── ComponentError
│   └── DocHubError
│       ├── DocumentNotFoundError
│       ├── AddendumNotFoundError
│       ├── DuplicateDocumentError
│       ├── InvalidDocumentTypeError
│       ├── IndexConnectionError
│       ├── IndexBackendError
│       └── PromptTemplateError
└── MigrationError
    └── DocHubFormatError
```

---

## 13. 配置示例

`team-kb/dochub.yaml`：

```yaml
name: team-kb
version: "1.0.0"
index:
  keyword:
    backend: meilisearch
    url: http://localhost:7700
    api_key: null
  vector:
    backend: chromadb
    path: ./team-kb/index/chroma
  embedding:
    model: sentence-transformers/all-MiniLM-L6-v2
    device: cpu
chunking:
  size: 512
  overlap: 100
search:
  default_mode: hybrid
  top_k: 10
  rrf_k: 60
```

---

## 14. 数据流图

```
┌─────────────────────────────────────────────────────────────────┐
│                         DocHub 数据流                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   用户/AI 客户端                                                  │
│        │                                                        │
│        ▼                                                        │
│   ┌────────────┐    ┌────────────┐    ┌─────────────────────┐  │
│   │   CLI      │    │   MCP      │    │   AI Skill 文件      │  │
│   │  agents-dev│    │  Server    │    │  (Claude/Cursor/...)│  │
│   └─────┬──────┘    └─────┬──────┘    └──────────┬──────────┘  │
│         │                 │                      │              │
│         └─────────────────┴──────────────────────┘              │
│                           │                                     │
│                           ▼                                     │
│              ┌──────────────────────┐                          │
│              │   DocumentStore      │                          │
│              │   (本地文件 + 元数据) │                          │
│              └──────────┬───────────┘                          │
│                         │                                       │
│         ┌───────────────┼───────────────┐                       │
│         ▼               ▼               ▼                       │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐                 │
│   │ Meili/   │    │ ChromaDB │    │ Prompt   │                 │
│   │ SQLite   │    │ (可选)   │    │ Renderer │                 │
│   └──────────┘    └──────────┘    └──────────┘                 │
│         │               │                                       │
│         └───────┬───────┘                                       │
│                 ▼                                               │
│         ┌──────────────┐                                        │
│         │ HybridSearch │                                        │
│         └──────────────┘                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 15. 测试策略

| 测试类型 | 覆盖内容 |
|---|---|
| 单元测试 | `DocumentStore`、分块器、索引器、模板渲染器、MCP 工具 |
| 集成测试 | CLI 完整工作流、MCP Server 启动与工具调用、混合搜索结果一致性 |
| 降级测试 | 无 Meilisearch/ChromaDB 时回退到 SQLite/关键词搜索 |
| 迁移测试 | 各格式生成与验证（Claude/Cursor/ZCode/MCP） |

---

## 16. 实施阶段建议

| 阶段 | 内容 |
|---|---|
| Phase 1 | 核心数据模型、DocumentStore、CLI `init/add/update/addendum/read` |
| Phase 2 | Markdown 分块、SQLite FTS5 关键词索引、CLI `search` |
| Phase 3 | ChromaDB 向量索引、Hybrid Search、CLI `ask` |
| Phase 4 | MCP Server、动态 Prompt 模板 |
| Phase 5 | AI Skill 文件生成、迁移验证、测试完善 |
| Phase 6 | 可选 Web UI、PDF/DOCX 解析、性能优化 |

---

## 17. 成功标准

- [ ] 团队可以在本地初始化并管理一个 Markdown 知识库
- [ ] 支持主文档 + 贡献者增量补充，不发生冲突覆盖
- [ ] 支持关键词、语义、混合三种搜索模式
- [ ] 支持按作者、贡献者、SessionID、文档类型、标签筛选
- [ ] MCP Server 可被 Claude / Cursor / ZCode 调用
- [ ] 动态 Prompt 模板能根据查询结果正确组装上下文
- [ ] 自动生成各目标工具的 Skill / Command / MCP 文件
- [ ] 无外部服务时可降级运行
- [ ] 单元测试 + 集成测试覆盖率 ≥ 80%

---

## 18. 参考资源

- [Diátaxis Framework](https://diataxis.fr/)
- [Meilisearch Documentation](https://www.meilisearch.com/docs)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Docling GitHub](https://github.com/DS4SD/docling)
- [Marker GitHub](https://github.com/datalab-to/marker)
- [LlamaIndex Prompt Templates](https://docs.llamaindex.ai/en/stable/module_guides/models/prompts/)
