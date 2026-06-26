# MCP Skill Manager 设计规格

> 设计日期：2026-06-26  
> 目标：构建一个统一的 MCP 服务，用于集中管理代码开发中常用的 Skill，并按代码语言、开发动作、触发词动态组装 Prompt 模板。

---

## 1. 背景与目标

### 1.1 问题

- 当前 Skill 文档通常是静态的、按项目本地管理，每个项目都要重复配置。
- 不同编程语言对同一 Skill 的上下文规则描述存在差异（如 Python 与 Go 的代码规范）。
- 固定 Skill 靠开发动作和触发词运行，但无法灵活地按语言、动作、触发词动态加载片段。

### 1.2 目标

构建一个 **MCP Skill Manager** 服务：

1. 统一管理常用代码开发 Skill，避免每个项目重复配置。
2. 支持按 **代码语言（language）**、**开发动作（action）**、**触发词（trigger）** 动态组装 Prompt。
3. 提供 **固定兜底 Prompt**，在无法精确匹配时降级使用。
4. 暴露规范的 MCP 接口，供 Claude Code、Cursor、ZCode 等工具调用。
5. 支持项目本地覆盖，满足项目级定制需求。
6. 采用可插拔存储，默认文件系统，未来可替换为数据库或远程存储。

### 1.3 设计原则

- **功能独立成包**：每个独立功能应作为单独的包/组件开发，不强制挤入统一的目录层级。当前项目结构是参考和基础环境，但具体实现应保持模块化。
- **Core + Format 分离**：复用 `agents_develop` 的现有架构，核心逻辑与工具特定格式解耦。
- **动态组装优于静态复制**：同一 Skill 的不同语言/动作变体通过片段组装，避免内容重复。
- **显式优先于隐式**：触发词、动作、语言应尽量显式声明，语义匹配仅作补充。

---

## 2. 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     MCP Skill Manager                        │
│                   (一个独立 MCP Server)                       │
├─────────────────────────────────────────────────────────────┤
│  API Layer (MCP Tools)                                       │
│  ├── list_skills()                                           │
│  ├── resolve_skill(name, language, action, trigger, ctx)    │
│  ├── detect_language(project_path)                           │
│  ├── register_skill(metadata, base_prompt, fragments)        │
│  └── update_fragment(skill_name, fragment)                   │
├─────────────────────────────────────────────────────────────┤
│  Resolution Engine                                           │
│  ├── PriorityResolver                                        │
│  │   本地覆盖 > L+A+T 精确匹配 > 部分匹配 > 固定兜底          │
│  ├── FragmentAssembler                                       │
│  │   base_prompt + fragments → 最终 prompt                   │
│  └── LanguageDetector                                        │
│      项目文件 / 显式传入 / 文件后缀                           │
├─────────────────────────────────────────────────────────────┤
│  Storage Abstraction (可插拔)                                 │
│  ├── FileSystemStore  （默认）                                │
│  ├── SQLiteStore      （预留）                                │
│  └── RemoteStore      （预留）                                │
├─────────────────────────────────────────────────────────────┤
│  Data Model                                                  │
│  ├── Skill                                                   │
│  ├── PromptFragment                                          │
│  ├── TriggerRule                                             │
│  └── ProjectOverride                                         │
└─────────────────────────────────────────────────────────────┘
```

### 2.1 与 agents_develop 的关系

- 复用 `core/shared/base.py` 的 `ComponentMetadata` 作为 Skill 元数据基础。
- 复用 `core/mcp_base/server.py` 作为 MCP Server 基座。
- 新增一个独立 component：`skill_manager_mcp_server`，但作为一个独立包存在，不强耦合到现有 `components/` 目录层级。

---

## 3. 数据模型

### 3.1 Skill

```python
@dataclass
class Skill:
    name: str                          # 唯一标识，如 "code_review"
    description: str                   # 一句话描述
    version: str                       # 语义版本
    base_prompt: str                   # 固定兜底 Prompt
    default_action: str | None         # 默认动作，如 "review"
    supported_languages: list[str]     # ["python", "typescript", "go", "*"]
    tags: list[str]                    # 用于搜索和分类
    triggers: list[TriggerRule]        # 触发词规则
    created_at: str
    updated_at: str
```

### 3.2 PromptFragment

```python
@dataclass
class PromptFragment:
    id: str
    skill_name: str
    language: str | None               # "python" / None 表示通用
    action: str | None                 # "self_review" / None 表示通用
    trigger: str | None                # "/review" / None 表示通用
    priority: int                      # 越大越优先
    content: str                       # Markdown 片段
    is_required: bool                  # 是否必须包含
```

### 3.3 TriggerRule

```python
@dataclass
class TriggerRule:
    type: Literal["slash", "keyword", "intent", "event"]
    value: str                         # "/review", "review", "code_review", "on_save"
    action: str                        # 触发后对应的 action
    language_hint: str | None          # 可选的语言提示
```

### 3.4 ProjectOverride

```python
@dataclass
class ProjectOverride:
    skill_name: str
    project_path: str                  # 项目根目录或标识
    fragment: PromptFragment
```

### 3.5 ResolveResult

```python
@dataclass
class ResolveResult:
    skill: str
    resolved_for: dict                 # {language, action, trigger}
    prompt: str
    fragments_applied: list[str]
    fallback_used: bool
    warnings: list[str]
```

---

## 4. Prompt 解析与组装

### 4.1 解析优先级

当一个 `resolve_skill` 请求进来时，按以下顺序组装：

| 优先级 | 来源 | 匹配条件 |
| --- | --- | --- |
| 1 | ProjectOverride | `project_path` 匹配，且 `skill_name` 匹配 |
| 2 | 精确片段 | `language` + `action` + `trigger` 全匹配 |
| 3 | 双匹配片段 | 任意两个维度匹配（如 L+A, L+T, A+T） |
| 4 | 单匹配片段 | 任意一个维度匹配 |
| 5 | `Skill.base_prompt` | 没有任何片段匹配时兜底 |

### 4.2 组装逻辑

1. 从 Skill 取出 `base_prompt`。
2. 按优先级从高到低收集匹配的 fragments。
3. 如果 fragment 标记 `is_required=True`，则强制替换同位置内容。
4. 最终合并成完整 Prompt 返回。

### 4.3 返回示例

```json
{
  "skill": "code_review",
  "resolved_for": {
    "language": "python",
    "action": "self_review",
    "trigger": "/review"
  },
  "prompt": "# 完整 Prompt ...",
  "fragments_applied": ["fragment_id_1", "fragment_id_2"],
  "fallback_used": false,
  "warnings": []
}
```

---

## 5. MCP 暴露接口

### 5.1 list_skills

```json
{
  "name": "list_skills",
  "description": "List all registered skills with metadata",
  "inputSchema": {
    "type": "object",
    "properties": {
      "filter_language": {"type": "string"},
      "filter_action": {"type": "string"},
      "filter_tag": {"type": "string"}
    }
  }
}
```

返回：

```json
[
  {
    "name": "code_review",
    "description": "Review code for quality and bugs",
    "version": "1.0.0",
    "default_action": "self_review",
    "supported_languages": ["python", "typescript", "go", "*"]
  }
]
```

### 5.2 resolve_skill

```json
{
  "name": "resolve_skill",
  "description": "Resolve a skill prompt for given context",
  "inputSchema": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "language": {"type": "string"},
      "action": {"type": "string"},
      "trigger": {"type": "string"},
      "project_path": {"type": "string"}
    },
    "required": ["name"]
  }
}
```

### 5.3 detect_language

```json
{
  "name": "detect_language",
  "description": "Detect primary programming language of a project or file",
  "inputSchema": {
    "type": "object",
    "properties": {
      "project_path": {"type": "string"},
      "file_path": {"type": "string"}
    }
  }
}
```

### 5.4 register_skill

```json
{
  "name": "register_skill",
  "description": "Register a new skill with metadata and optional fragments",
  "inputSchema": {
    "type": "object",
    "properties": {
      "metadata": {"type": "object"},
      "base_prompt": {"type": "string"},
      "fragments": {"type": "array"}
    },
    "required": ["metadata", "base_prompt"]
  }
}
```

### 5.5 update_fragment

```json
{
  "name": "update_fragment",
  "description": "Add or update a prompt fragment for a skill",
  "inputSchema": {
    "type": "object",
    "properties": {
      "skill_name": {"type": "string"},
      "fragment": {"type": "object"}
    },
    "required": ["skill_name", "fragment"]
  }
}
```

### 5.6 register_trigger

```json
{
  "name": "register_trigger",
  "description": "Register a custom trigger rule for a skill",
  "inputSchema": {
    "type": "object",
    "properties": {
      "skill_name": {"type": "string"},
      "trigger": {"type": "object"}
    },
    "required": ["skill_name", "trigger"]
  }
}
```

---

## 6. 存储层

### 6.1 抽象接口

```python
class SkillStore(ABC):
    @abstractmethod
    def list_skills(self, filters: dict | None = None) -> list[Skill]: ...

    @abstractmethod
    def get_skill(self, name: str) -> Skill | None: ...

    @abstractmethod
    def save_skill(self, skill: Skill) -> None: ...

    @abstractmethod
    def delete_skill(self, name: str) -> None: ...

    @abstractmethod
    def list_fragments(self, skill_name: str, filters: dict | None = None) -> list[PromptFragment]: ...

    @abstractmethod
    def save_fragment(self, fragment: PromptFragment) -> None: ...

    @abstractmethod
    def delete_fragment(self, fragment_id: str) -> None: ...

    @abstractmethod
    def list_project_overrides(self, project_path: str) -> list[ProjectOverride]: ...

    @abstractmethod
    def save_project_override(self, override: ProjectOverride) -> None: ...
```

### 6.2 默认实现：FileSystemStore

存储结构：

```
~/.agents-develop/skill-manager/
├── skills/
│   ├── code_review/
│   │   ├── skill.json
│   │   ├── base_prompt.md
│   │   └── fragments/
│   │       ├── python_self_review.md
│   │       ├── typescript_self_review.md
│   │       └── generic_review.md
├── triggers/
│   └── code_review.json
└── overrides/
    └── <project_hash>/
        └── code_review.md
```

### 6.3 预留实现

- `SQLiteStore`：本地 SQLite 数据库
- `RemoteStore`：远程 HTTP API / Git 仓库

---

## 7. 语言检测器

### 7.1 抽象接口

```python
class LanguageDetector(ABC):
    @abstractmethod
    def detect(self, project_path: str | None, file_path: str | None) -> DetectResult: ...
```

### 7.2 DetectResult

```python
@dataclass
class DetectResult:
    primary_language: str | None
    confidence: float
    secondary_languages: list[str]
    signals: list[str]
```

### 7.3 默认实现：HeuristicLanguageDetector

检测优先级：

| 优先级 | 信号 |
| --- | --- |
| 1 | 显式传入 `language` |
| 2 | `file_path` 后缀 |
| 3 | 项目标记文件 |
| 4 | 文件数量统计 |
| 5 | 无信号 |

### 7.4 语言标记配置

```python
LANGUAGE_MARKERS = {
    "python": ["pyproject.toml", "setup.py", "requirements.txt", "*.py"],
    "typescript": ["tsconfig.json", "package.json", "*.ts", "*.tsx"],
    "javascript": ["package.json", "*.js", "*.jsx"],
    "go": ["go.mod", "*.go"],
    "rust": ["Cargo.toml", "*.rs"],
    "java": ["pom.xml", "build.gradle", "*.java"],
}
```

---

## 8. 触发词解析器

### 8.1 抽象接口

```python
class TriggerResolver(ABC):
    @abstractmethod
    def resolve(self, input_text: str | None, event: str | None, skill: Skill) -> TriggerResult: ...
```

### 8.2 TriggerResult

```python
@dataclass
class TriggerResult:
    matched: bool
    trigger_type: str | None
    trigger_value: str | None
    action: str | None
    language_hint: str | None
    confidence: float
```

### 8.3 默认实现：MultiStrategyTriggerResolver

按以下顺序匹配：

| 顺序 | 策略 |
| --- | --- |
| 1 | Slash Command |
| 2 | Keyword |
| 3 | Event |
| 4 | Intent |
| 5 | 无匹配 |

### 8.4 触发词声明示例

```json
{
  "triggers": [
    {"type": "slash", "value": "/review", "action": "self_review"},
    {"type": "slash", "value": "/review-python", "action": "self_review", "language_hint": "python"},
    {"type": "keyword", "value": "review this code", "action": "self_review"},
    {"type": "event", "value": "on_save", "action": "quick_review"}
  ]
}
```

---

## 9. 项目本地覆盖

### 9.1 约定目录

```
.my-skills/
├── code_review.md          # 覆盖 code_review skill 的完整 Prompt
├── code_review/
│   ├── override.md         # 完整覆盖
│   └── fragments/
│       ├── python.md       # python 片段覆盖
│       └── self_review.md  # action 片段覆盖
└── .skill-config.json      # 项目级 skill 配置
```

### 9.2 加载优先级

1. `project_path` 显式传入时，才读取本地覆盖。
2. 同 Skill 下：完整覆盖文件 > 片段覆盖文件。
3. 精确命名 > 单维度命名。
4. 本地覆盖始终优先于 MCP 服务端模板。

### 9.3 项目级配置示例

```json
{
  "skills": {
    "code_review": {
      "enabled": true,
      "default_action": "peer_review",
      "overrides": {
        "python": "Prefer Django-style over Flask-style"
      }
    }
  }
}
```

---

## 10. 错误处理与降级策略

### 10.1 错误类型

```python
class SkillManagerError(AgentsDevelopError): ...
class SkillNotFoundError(SkillManagerError): ...
class FragmentNotFoundError(SkillManagerError): ...
class InvalidTriggerError(SkillManagerError): ...
class StorageError(SkillManagerError): ...
class LanguageDetectionError(SkillManagerError): ...
```

### 10.2 降级行为

| 场景 | 行为 |
| --- | --- |
| Skill 不存在 | 返回错误，附带可用 Skill 列表 |
| 语言检测失败 | 使用通用模板，标记 `fallback_used=true` |
| action 未匹配 | 使用 `Skill.default_action`，若无则用 `base_prompt` |
| trigger 未匹配 | 不触发特定片段，仅返回 `base_prompt` |
| 片段解析冲突 | 高优先级覆盖低优先级，日志警告 |
| 存储读取失败 | 返回内存中已加载的 Skill，记录警告 |
| 本地覆盖读取失败 | 降级到服务端模板 |

---

## 11. 内置 Skill 示例

### 11.1 code_review

- **base_prompt**：通用代码审查原则
- **actions**：`self_review`, `peer_review`, `security_review`
- **languages**：`python`, `typescript`, `go`, `javascript`, `rust`, `java`
- **triggers**：
  - `/review`
  - `/review-python`, `/review-go`, `/review-ts`
  - 关键词 "review this code"
  - 事件 `on_save`

### 11.2 debug

- **base_prompt**：通用调试流程
- **actions**：`trace`, `isolate`, `fix`
- **languages**：同上
- **triggers**：
  - `/debug`
  - `/debug-python`
  - 关键词 "why is this failing"

### 11.3 refactor

- **base_prompt**：通用重构原则
- **actions**：`simplify`, `extract`, `rename`
- **languages**：同上
- **triggers**：
  - `/refactor`
  - `/refactor-python`

---

## 12. 测试策略

### 12.1 单元测试

- `test_resolution_engine.py`：验证优先级和组装逻辑
- `test_language_detector.py`：验证语言检测
- `test_trigger_resolver.py`：验证触发词匹配
- `test_storage.py`：验证 `FileSystemStore`
- `test_mcp_server.py`：验证 MCP tool 接口

### 12.2 集成测试

- 启动 MCP Server，通过 stdio 调用 `resolve_skill`
- 完整流程：输入 `/review` + 项目路径 → 返回组装后的 Python review Prompt

### 12.3 示例 Skill

内置 `code_review` 示例 Skill，用于端到端验证。

---

## 13. 项目规范补充

每个独立开发的功能应作为单独的包/组件存在，不强制按统一目录层级组织。当前项目结构（`core/`, `formats/`, `components/`）是参考和基础环境，后续新增功能模块应保持独立可移植。

本 MCP Skill Manager 作为一个独立功能包开发，可独立安装和运行，同时与 `agents_develop` 的核心抽象兼容。

---

## 14. 后续工作

1. 编写实现计划。
2. 创建独立包：`skill_manager_mcp_server`。
3. 实现存储抽象和默认文件系统存储。
4. 实现解析引擎、语言检测器、触发词解析器。
5. 实现 MCP Server 和工具接口。
6. 编写内置示例 Skill 和测试。
7. 更新 `CLAUDE.md` 中的项目规范。
