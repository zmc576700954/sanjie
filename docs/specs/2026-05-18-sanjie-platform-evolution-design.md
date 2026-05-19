---
title: "三界平台化演进设计文档"
date: 2026-05-18
status: active
author: system-architect
version: 1.0.0
---

# 三界平台化演进设计文档

## 摘要

本文档基于对 `agents_develop` 项目现有架构的全面评审，提出五项系统性优化，旨在将当前"文档驱动"的去中心化架构升级为"基础设施驱动"的平台化架构。所有设计严格遵循 `GEMINI.md` 定义的八大原则，特别是：绝对去中心化（§1）、MCP-First（§2）、零代码可靠性（§3）、Schema 强制输出（§4）。

## 背景与动机

经过对现有代码、文档和测试覆盖的深入分析，发现五个维度的系统性断层：

1. **MCP Server 样板代码重复**：新增 Skill 需要手动复制粘贴 `sys.path`、`ensure_safe_path`、`McpError` 处理等样板代码，边际成本高且易出错。
2. **A2A 协议未自动化**：GEMINI.md §6 定义了精美的 `A2A_HANDOFF` 协议，但实际工作流仍依赖用户手动复制粘贴，接收方注意力被对话填充稀释。
3. **路由层智能化不足**：`logic_tracer.py` 使用纯关键词匹配，无法处理复合错误和未知错误类型。
4. **GSSC Pipeline 不完整**：Taibai 定义的 Gather-Select-Structure-Compress 流程中，Gather 和 Select 步骤完全缺失，Structure 依赖 Agent 手动执行。
5. **Skill 风险分级无自动化守卫**：architecture.md 定义了四级风险分级和对应的安全机制，但缺乏统一的入口拦截层，各 Skill 自行实现，标准不一。

## 架构总览

本次演进包含五个核心子系统，按实施优先级排列：

| 优先级 | 子系统 | 核心目标 | 与现有代码关系 |
|--------|--------|---------|---------------|
| P0 | MCP Auto-Registry | 新增 Skill 零样板代码 | 零破坏，渐进采纳 |
| P0 | A2A Inbox | 去中心化消息传递自动化 | 零侵入，可选采纳 |
| P1 | Host-Aware Routing | Agent-Native LLM 路由 + 多 Provider 支持 | 拆分现有逻辑，兼容降级 |
| P1 | GSSC Pipeline | Taibai 四步管道自动化 | 补充缺失步骤 |
| P2 | Risk Guard Layer | 声明式 Skill 风险守卫 | 前置拦截，不改变 Skill 内部逻辑 |

## 详细设计

### 第一节：统一 MCP 注册中心（MCP Auto-Registry）

#### 问题

目前 3 个 MCP Server（tianyan、taibai、wanglingguan）均为手写 `*_server.py`，每个文件包含：
- `sys.path` 注入
- `ensure_safe_path` 包裹
- `McpError` 统一捕获
- `pydantic.Field` 参数定义
- `mcp.tool()` 装饰器

新增 Skill 时需复制粘贴这份样板代码，极易出错，且 `plugin.json` 需手动同步。

#### 设计目标

新增 Skill 只需完成：
```
skills/tool_foo/
├── SKILL.md          # YAML frontmatter 定义工具签名
└── scripts/
    └── do_foo.py     # 纯函数，接受标准参数
```
系统自动生成 MCP Server 注册和 `plugin.json`。

#### 架构设计

**不引入中心化编排**：注册中心只做"技能发现"和"代码生成/加载"，不持有业务逻辑、不决定执行顺序。

```
skills/celestial_registry/
├── generator.py        # 扫描 SKILL.md → 产出 MCP Server 代码
├── loader.py           # 运行时动态加载工具到 FastMCP
├── plugin_writer.py    # 重写 plugin.json
└── guard.py            # 风险守卫（见第六节）
```

**运行时路径**：

```
mcp-servers/
├── auto_server.py      # 统一入口：扫描 + 动态注册所有工具
├── tianyan_server.py   # 手动覆盖层（需要特殊逻辑时保留）
└── ...
```

`auto_server.py` 启动时：
1. 扫描 `skills/tool_*/SKILL.md`
2. 解析 YAML frontmatter 中的 `tools:` 列表
3. 根据 `script:` 路径和 `parameters:` 定义，动态生成 pydantic 模型
4. 将每个 tool 注册到同一个 `FastMCP` 实例
5. 按 `name:` 前缀做命名空间隔离

**生成时路径**：

`generator.py` 可以一次性生成所有 `*_server.py` 文件（由模板产出），然后提交到仓库。

#### 关键技术点

1. **YAML Schema 扩展**：SKILL.md 的 `tools:` 块中增加 `risk_level` 字段，供下游守卫层使用。
2. **动态 Pydantic 模型**：使用 `pydantic.create_model()` 从 YAML 参数自动生成带 `Field(description=...)` 的模型类。
3. **路径安全**：所有动态注册的 tool 自动包裹 `ensure_safe_path`。
4. **覆盖机制**：如果 `mcp-servers/<name>_server.py` 已存在，`auto_server.py` 优先加载手动版本。

---

### 第二节：轻量级 A2A 事件总线（A2A Inbox）

#### 问题

GEMINI.md §6 定义了 `A2A_HANDOFF` 协议，但真实工作流是：
> 用户从 YangJian 的输出里复制 `A2A_HANDOFF` 块 → 打开另一个对话 → 粘贴给 NeZha

导致：传输混入对话填充、状态无持久化、用户成为人肉消息队列。

#### 设计约束（不可突破）

1. **零中心化编排**：不能有 `a2a_router.py` 决定谁什么时候运行什么
2. **Agent 不互相调用**：Agent 不能 `import` 或 `subprocess` 另一个 Agent
3. **文本协议是唯一接口**：Agent 之间只通过结构化 Markdown/JSON 块通信

#### 架构设计

**核心洞察**：事件总线不是进程、不是类、不是服务——它是一套**文件系统命名约定**。总线本身无状态、无逻辑、不运行。

```
a2a_inbox/          # 在 .gitignore 中，不提交到 git
├── pending/        # 待领取
├── claimed/        # 已被目标 Agent 读取
└── completed/      # 执行完毕，归档备查
```

**信封写入协议**（发送方 Agent 遵守）：

Agent 输出中包含 `A2A_HANDOFF` 块时，其 `<Celestial Protocol>` 新增指令：
> `[Action Required]: 将以下 A2A 信封写入文件 a2a_inbox/pending/{timestamp}_{from}_to_{to}.md`

信封内容扩展元数据：

```markdown
```json A2A_ENVELOPE
{
  "message_id": "uuid-v4",
  "from": "yangjian",
  "to": "nezha",
  "timestamp": "2026-05-18T15:23:01Z",
  "context_pointers": ["docs/specs/2026-05-18-payment-design.md"],
  "handoff_payload": {
    "logic_chain": "...",
    "root_cause": "...",
    "recommended_skill": "yindan",
    "action": "Add None guard..."
  },
  "priority": "normal"
}
```

**信封读取协议**（接收方 Agent 遵守）：

每个 Agent 的 `<Celestial Protocol>` 新增启动指令：
> `[Startup Check]: 扫描 a2a_inbox/pending/*_to_{agent_name}.md。若存在，优先读取最新的一封，将其移动到 a2a_inbox/claimed/，然后忽略用户的闲聊输入，直接处理信封中的 actionable_spec。`

#### 可选：轻量通知守护脚本

提供完全可选的 `skills/a2a_daemon.py`：
- 只轮询 `pending/` 目录，向 stdout 打印通知
- **不执行任何 Agent 逻辑，不做任何路由决策**
- 它是观察者，不是编排器

#### 边界防护

在 `GEMINI.md` 中新增铁律：
> **A2A Inbox 法则**：`a2a_inbox/` 中不得出现任何形式的"执行指令"（如 `run_command`、`exec_script`）。信封只能包含**上下文指针**和**结构化 spec**。执行永远发生在接收 Agent 自身的决策流程内。

---

### 第三节：Agent-Native LLM 路由（Host-Aware Routing）

#### 问题

`logic_tracer.py` 使用纯字符串关键词匹配：

```python
if "none" in desc_lower or "typeerror" in desc_lower:
    return {...yindan...}
```

导致两个瓶颈：
1. **复合错误无法处理**："NoneType in async payment webhook during bulk import" 同时命中多个关键词，结果不可预期
2. **新类型错误永久盲区**：未知错误只能 fallback 到 yindan

#### 核心洞察

当用户唤醒 YangJian 时，Agent 本身就是 LLM 的化身：
- **Claude Code** → Claude Sonnet/Opus
- **Cursor** → GPT-4 / Claude
- **Gemini CLI** → Gemini 1.5 Pro
- **Codex** → GPT-4
- **Trae** → Claude/GPT

**bajiu 不需要"调用 LLM"，只需要"给当前 LLM 提供正确的上下文和指令"。**

#### 三层路由架构

```
error_desc ──→ L1 Keyword Router (确定性代码) ──→ 置信度高？──→ 直接输出
                │
                │ 置信度低 / 复合 / 未知错误
                ↓
           L2 Agent-Native Reasoning
           (Agent 用当前 Host IDE 的 LLM 继续推理)
           基于共享的 Skill Registry
                │
                │ Agent 明确输出 [UNCERTAIN]
                ↓
           L3 Environment-Aware Fallback
           (ollama / 配置 API / 返回结构化 prompt)
```

#### 关键技术点

**1. 共享 Skill Registry（自动生成）**

```
agents/_shared/
└── skill_registry.md    # 由 celestial_registry 自动生成
```

内容由 `celestial_registry/generator.py` 扫描 `skills/tool_*/SKILL.md` 后生成，新增 Skill 自动被所有 Agent 知晓。

**2. Agent Protocol 升级**

每个 Agent 的 `<Celestial Protocol>` 新增路由决策协议：

```markdown
### Routing Decision Protocol

When classifying an error or task:

1. **L1 Check**: Use built-in keyword matching
2. **L2 Reasoning**: If L1 ambiguous, consult `agents/_shared/skill_registry.md`
3. **L3 Fallback**: If still uncertain, output `[UNCERTAIN]` and append `[Action Required]: 调用 bajiu 环境探测`

Output MUST include:
- `[reasoning]`: Why you chose this skill
- `[recommended_skill]`: The chosen skill name
- `[confidence]`: high | medium | low
```

**3. bajiu skill 的新定位**

`skills/tool_bajiu/scripts/`：
- `keyword_router.py`：L1，提取现有逻辑
- `environment_probe.py`：检测当前 Host IDE 和可用降级 provider
- `fallback_prompt_builder.py`：为纯脚本环境构建 prompt

`environment_probe.py` 检测到 `host != "none"` 时，返回提示让 Agent 直接进行 L2 推理。仅当 `host == "none"` 时，才尝试 ollama 或 API。

---

### 第四节：扩展 `providers/` 目录（Host-Aware Provider 生态）

#### 设计定位

`providers/` 不是为正常运行时的 Agent 准备（Agent 运行在 IDE Host 中，本身就是 LLM）。`providers/` 只为**纯脚本环境**（`host=none`，如 CI/CD、自动化测试、无头服务器）提供降级方案。

#### 目录结构

```
skills/tool_bajiu/scripts/providers/
├── __init__.py               # 注册表 + 自动发现
├── base.py                   # 抽象接口
├── ollama_provider.py        # 本地 LLM（默认，全平台）
├── openai_provider.py        # OpenAI API（原生匹配 Cursor, Codex）
├── anthropic_provider.py     # Anthropic API（原生匹配 Claude Code, Trae）
├── gemini_provider.py        # Google Gemini API（原生匹配 Gemini CLI）
└── openrouter_provider.py    # OpenRouter（通用聚合）
```

#### 抽象接口

```python
from abc import ABC, abstractmethod


class ModelProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def native_hosts(self) -> list[str]:
        """List of Host IDE names this provider natively matches."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def infer(self, system_prompt: str, user_prompt: str, timeout: float) -> str:
        pass
```

#### Provider 实现概要

所有 provider 使用 **Python 标准库 `urllib`**，零外部依赖。

| Provider | 原生 Host | 可用性检测 | 环境变量 |
|----------|----------|-----------|---------|
| ollama | 全部 | `localhost:11434/api/tags` | `SANJIE_OLLAMA_HOST`, `SANJIE_OLLAMA_MODEL` |
| openai | cursor, codex | `OPENAI_API_KEY` | `OPENAI_API_KEY`, `SANJIE_OPENAI_MODEL`, `OPENAI_BASE_URL` |
| anthropic | claude_code, trae | `ANTHROPIC_API_KEY` | `ANTHROPIC_API_KEY`, `SANJIE_ANTHROPIC_MODEL` |
| gemini | gemini_cli | `GOOGLE_API_KEY` | `GOOGLE_API_KEY`, `SANJIE_GEMINI_MODEL` |
| openrouter | 全部 | `OPENROUTER_API_KEY` | `OPENROUTER_API_KEY`, `SANJIE_OPENROUTER_MODEL` |

#### 注册表与自动发现

```python
def get_available_provider(force: str = None) -> Optional[ModelProvider]:
    """
    优先级：强制指定 > Host 原生匹配 > 任意可用。
    """
```

#### 降级链

```python
def route(error_desc: str, source_code: str = "") -> dict:
    l1_result = keyword_router.classify(error_desc)
    l1_confidence = confidence_scorer.score(l1_result, error_desc)
    
    if l1_confidence >= 0.9:
        return l1_result
    
    provider = get_available_provider()
    if provider:
        try:
            raw = provider.infer(build_system_prompt(), error_desc)
            l2_result = json.loads(raw)
            if l2_result.get("confidence", 0) >= 0.6:
                return l2_result
        except Exception:
            pass
    
    return l1_result
```

---

### 第五节：自动化 GSSC Pipeline（补齐 Taibai）

#### 问题

Taibai 定义的 Gather-Select-Structure-Compress 流程中：
- `context_compressor.py` 只做了 **C**
- `archive_manager.py` 只做了归档移动
- **Gather** 和 **Select** 完全缺失
- 四个步骤之间没有自动化衔接

#### 架构设计

```
skills/tool_taibai/
├── SKILL.md
└── scripts/
    ├── context_compressor.py    # C 步骤（已有）
    ├── archive_manager.py       # 归档（已有）
    ├── gather.py                # G 步骤（新增）
    ├── select.py                # S 步骤（新增）
    ├── structure.py             # S 步骤（新增）
    └── gssc_pipeline.py         # 管道编排器（新增）
```

**Gather（收集器）**：从多个来源收集原始上下文，返回元数据（路径、类型、大小、token 估算），不做任何过滤。

**Select（选择器）**：从原始内容中过滤噪音。内置规则：重复 stack trace、对话填充、装饰性 ASCII、py_compile 成功日志、空行。

**Structure（结构化器）**：自动注入 YAML Frontmatter 和标准 Markdown 结构。支持模板：`spec`、`archive`、`handoff`、`memory`。

**管道编排器**：

```python
def run_pipeline(
    source_paths: list[str],
    doc_type: str = "spec",
    aggressive_compress: bool = False,
    output_path: str = None
) -> dict:
    """一键执行 GSSC 四步管道。"""
    gathered = gather.gather_sources(source_paths)
    selected = select.select_content(gathered)
    structured = structure.structure_document(selected, doc_type=doc_type)
    compressed = compressor.compress(structured)
    # 返回元数据：原始 token、最终 token、压缩比
```

---

### 第六节：Skill 风险守卫自动化

#### 问题

architecture.md 定义了四级风险分级，但缺乏统一的入口拦截层，各 Skill 自行实现，标准不一。

#### 架构设计

```
skills/celestial_registry/
├── __init__.py
├── generator.py
├── loader.py
├── guard.py              # 新增：风险守卫层
└── skill_manifest.py     # 新增：Skill 元数据解析
```

#### 声明式风险配置

扩展 SKILL.md YAML frontmatter：

```yaml
---
name: sanjian
risk_level: high           # lowest | medium | high | highest
guard_rules:
  - name: scope_guardian
    required: true
    parameters:
      max_files: 10
      allowed_extensions: [".py", ".md"]
  - name: backup
    required: true
  - name: syntax_validation
    required: true
  - name: rollback
    required: true
---
```

#### 守卫层（guard.py）

```python
class RiskGuard:
    """
    声明式风险守卫。
    不决定 Agent 执行什么——只根据 SKILL.md 声明，
    在执行前验证必要条件是否满足。
    """
    
    def validate(self, skill_name: str, invocation_context: dict) -> None:
        manifest = self._load_manifest(skill_name)
        for rule in manifest.get("guard_rules", []):
            guard_fn = self._GUARD_FUNCTIONS.get(rule["name"])
            if guard_fn:
                guard_fn(invocation_context, rule.get("parameters", {}))
```

#### 守卫规则映射

| Risk Level | 强制规则 | 可选规则 |
|-----------|---------|---------|
| lowest | `syntax_validation` | `auto_rollback` |
| medium | `syntax_validation`, `user_approval` | `risk_assessment`, `ast_regression` |
| high | `syntax_validation`, `backup`, `scope_guardian`, `rollback` | — |
| highest | `syntax_validation`, `backup`, `blast_assessment`, `mandatory_approval`, `destruction_logging` | — |

#### 与 MCP Server 集成

`auto_server.py` 在注册工具时自动包裹守卫层：

```python
def register_guarded_tool(mcp, skill_name, tool_config):
    guard = RiskGuard()
    
    @mcp.tool()
    def guarded_tool(**params):
        guard.validate(skill_name, params)    # 前置守卫
        result = original_tool(**params)       # 执行
        guard.post_validate(skill_name, result) # 后置守卫
        return result
```

#### 边界防护

- **守卫不替代 skill 内部逻辑**：只是"门卫"，检查必要条件
- **可显式绕过**：`SANJIE_BYPASS_GUARD=true` 可跳过守卫（日志中标记）
- **纯声明式**：新增 skill 只需在 YAML 中声明，无需写 Python 守卫代码

---

## 实施优先级

### Phase 1：基础设施（P0，1-2 周）

1. **MCP Auto-Registry**
   - 实现 `celestial_registry/generator.py` 和 `loader.py`
   - 生成 `auto_server.py`
   - 为现有 3 个手写 server 验证兼容性
   - 更新 `plugin.json` 为自动生成

2. **A2A Inbox**
   - 创建 `a2a_inbox/` 目录结构
   - 在 YangJian 和 NeZha 的 `<Celestial Protocol>` 中新增信封协议
   - 实现可选的 `a2a_daemon.py`

### Phase 2：智能化（P1，2-3 周）

3. **Host-Aware Routing**
   - 拆分 `logic_tracer.py` 的 `_classify_error` 为独立 `keyword_router.py`
   - 实现 `environment_probe.py` 和 `fallback_prompt_builder.py`
   - 创建 `agents/_shared/skill_registry.md` 自动生成机制
   - 更新所有 Agent 的 `<Celestial Protocol>` 路由决策协议

4. **Provider 生态**
   - 实现 `providers/base.py` 和全部 5 个 provider
   - 实现注册表自动发现
   - 编写 `tests/test_bajiu_router.py`

5. **GSSC Pipeline**
   - 实现 `gather.py`、`select.py`、`structure.py`
   - 实现 `gssc_pipeline.py`
   - 更新 Taibai 的 `SKILL.md` 为管道式工作流

### Phase 3：安全（P2，1-2 周）

6. **Risk Guard Layer**
   - 实现 `guard.py` 和 `skill_manifest.py`
   - 为现有 skill 补充 `risk_level` 和 `guard_rules`
   - 集成到 `auto_server.py` 的注册流程
   - 编写 `tests/test_guard.py`

---

## GEMINI.md 兼容性矩阵

| GEMINI.md 原则 | 对应设计 | 是否兼容 |
|---------------|---------|---------|
| §1 绝对去中心化 | MCP Auto-Registry 只做代码生成；A2A Inbox 是文件系统约定；Guard 是声明式拦截 | ✅ |
| §2 MCP-First | Auto-Registry 自动生成 MCP Server；Provider 只用于纯脚本降级 | ✅ |
| §3 零代码可靠性 | Skill Registry 自动生成；路由协议写入 Agent Prompt；Guard 声明式配置 | ✅ |
| §4 Schema 强制输出 | GSSC Structure 自动注入 YAML Frontmatter；A2A 信封固定 JSON Schema | ✅ |
| §5 GSSC Pipeline | 补齐 Gather + Select，自动化四步流转 | ✅ |
| §6 A2A 文本协议 | 文件系统即总线，信封不含执行指令 | ✅ |
| §7 Skill Evaluation | Risk Guard 提供可验证的安全检查点 | ✅ |
| §8 MCP 安全标准 | Path Security 通过 `ensure_safe_path`；Error Handling 通过 `McpError` | ✅ |

---

## 附录

### A. 环境变量速查表

| 变量 | 用途 | 示例 |
|------|------|------|
| `SANJIE_LLM_PROVIDER` | 强制指定 provider | `ollama`, `openai`, `anthropic` |
| `SANJIE_HOST` | 声明当前 Host IDE | `claude_code`, `cursor`, `gemini_cli` |
| `SANJIE_OLLAMA_HOST` | Ollama 端点 | `http://localhost:11434` |
| `SANJIE_OLLAMA_MODEL` | Ollama 模型 | `codellama:7b-code` |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` | OpenAI 配置 | `sk-xxx` / `https://...` |
| `ANTHROPIC_API_KEY` | Anthropic 配置 | `sk-ant-xxx` |
| `GOOGLE_API_KEY` | Gemini 配置 | `your-key` |
| `OPENROUTER_API_KEY` | OpenRouter 配置 | `sk-or-xxx` |
| `SANJIE_BYPASS_GUARD` | 跳过风险守卫 | `true` |

### B. 新增文件清单

```
skills/celestial_registry/
├── generator.py
├── loader.py
├── plugin_writer.py
├── guard.py
└── skill_manifest.py

skills/tool_bajiu/scripts/
├── keyword_router.py
├── environment_probe.py
├── fallback_prompt_builder.py
└── providers/
    ├── __init__.py
    ├── base.py
    ├── ollama_provider.py
    ├── openai_provider.py
    ├── anthropic_provider.py
    ├── gemini_provider.py
    └── openrouter_provider.py

skills/tool_taibai/scripts/
├── gather.py
├── select.py
├── structure.py
└── gssc_pipeline.py

agents/_shared/
├── skill_registry.md
└── host_profiles.md

mcp-servers/
└── auto_server.py

skills/
└── a2a_daemon.py

tests/
├── test_celestial_registry.py
├── test_bajiu_router.py
├── test_gssc_pipeline.py
└── test_guard.py
```
