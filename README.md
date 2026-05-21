# 三界 (Three Realms): Persona & Skill Protocol + Toolkit

三界是一套**协议规范 + 工具套件**，让 Claude Code、Cursor、Codex 等 AI IDE 更好地在多角色、多技能场景下协作。

> **一句话定位**：Claude Code 是大脑，我们的 Persona 是大脑的"通用语"，MCP Server 是大脑的"手脚"。

## 三层架构（各司其职）

```
L1  Runtime    Claude Code / Cursor / Codex  (Agent 本体，不由我们开发)
     │              AI 模型自主决策："现在该加载哪个 Persona？"
     │              ↓
L3  Config     Persona (agents/*.md) + Skill (skills/tool_*/)  ← 我们在这里
     │              行为模板 + 输出规范 + 交接标准
     │              ↓
L2  Protocol   MCP Server (mcp-servers/*)  ← 确定性执行层
                工具调用标准，输入输出严格契约
```

| 层级 | 职责 | 去中心化 vs 规范 |
|------|------|-----------------|
| **L1: Claude Code** | "现在该调用哪个 Persona/Skill？" | **去中心化** — 模型自主推理 |
| **L3: Persona 内部** | "我怎么思考？" | **去中心化** — Core Directives 完全自由 |
| **L3: Output Schema** | "我完成后输出什么？" | **Workflow** — 强制标准化，确保交接 |
| **L2: MCP Skill** | "这个工具怎么执行？" | **Workflow** — 确定性函数，严格契约 |

## 核心机制：模型自主决策 + 规范交接

### 1. 决策阶段（去中心化）

Claude Code 读取所有 Persona 的 Capability Registry，AI 模型自主决定加载谁：

```
用户："帮我审查这段代码"
    ↓
Claude Code 扫描 agents/*.md
    ↓
发现 WangLingguan 有 review 能力
    ↓
AI 模型决策：加载 WangLingguan
```

### 2. 执行阶段（去中心化）

加载的 Persona 自由思考，不受限制：

```
WangLingguan Persona 加载到上下文
    ↓
AI 模型以"王灵官"的角色执行审查
    ↓
自由思考、自由分析（Core Directives 不限制过程）
```

### 3. 交接阶段（强制规范）

Persona 完成后，必须输出标准化的交接单：

```markdown
[task_status]: completed
[output_summary]: 发现 3 个问题
[next_action]: 修复 UserController.php:42 的 null pointer
[capability]: problem_solving
[tags]: debug, php
```

### 4. 路由阶段（去中心化）

Claude Code 读取 `[next_action]`，AI 模型自主决策下一步：

```
读取 [next_action] + [tags]
    ↓
AI 模型决策：
    ├── 匹配到 Nezha（problem_solving）→ 加载 Nezha
    ├── 直接调用 yindan Skill（通过 MCP）
    └── 直接回答用户（兜底）
```

## 项目结构

```
agents_develop/
├── agents/                 # Persona 行为模板
│   ├── nezha.md           # 哪吒 - 代码修复
│   ├── taibai.md          # 太白金星 - 文档
│   ├── yangjian.md        # 杨戬 - 调查
│   └── wanglingguan.md    # 王灵官 - 审查
├── skills/                # Skill 定义（L2 层的"砖块"）
│   ├── tool_yindan/       # 精准修复
│   ├── tool_taie/         # 功能开发
│   └── ...
├── mcp-servers/           # MCP Server 实现（确定性执行）
│   ├── taibai_server.py
│   ├── tianyan_server.py
│   └── wanglingguan_server.py
├── tools/                 # Creator 工具（帮助生成规范）
│   └── create_persona.py  # CLI：生成符合规范的新 Persona
├── docs/
│   └── SPEC.md            # 协议规范详情
├── tests/                 # Skill 单元测试
└── README.md              # 本文件
```

## Persona 规范格式

每个 `agents/*.md` 必须包含三部分：

### 1. Capability Registry（给 Claude Code 扫描用）

```markdown
## Capability Registry

| Domain | Tags | Confidence | Description |
|--------|------|------------|-------------|
| problem_solving | [debug, fix, php] | high | 代码级 Bug 修复 |

### Domain: problem_solving
- **Trigger Patterns**: `[root_cause]` present
- **Required Context**: 调查报告、错误日志
- **Output Schema**: `[fix_summary]`, `[modified_files]`
```

### 2. Core Directives（完全自由，不限制思维过程）

```markdown
## Core Directives
1. 使用 `demon_hunt` 调查 Bug
2. 使用 `lotus_body` 执行修改
3. 不要猜测根因
```

**注意**：不要写 "先 A 后 B" 的 workflow 步骤。让 Claude Code 自己决定顺序。

### 3. Output Schema（强制规范，确保交接）

```markdown
## Output Schema
产出必须包含：
- [task_status]: completed | failed | needs_clarification
- [output_summary]: 一句话总结
- [next_action]: 下一步建议（供 Claude Code 决策）
- [capability]: 使用的能力域
- [tags]: 相关标签
- [deliverables]: 文件列表（如有）
```

## 使用 Creator 工具生成新 Persona

```bash
python tools/create_persona.py \
  --name jinzha \
  --domain problem_solving \
  --tags "debug,fix,go" \
  --description "Go 语言专家"
```

生成符合规范的 `agents/jinzha.md`，包含：
- 标准 Capability Registry 格式
- 空白 Core Directives（用户自己填）
- 标准 Output Schema

## 放弃 vs 聚焦

### ❌ 放弃（不要做的事）

1. **不要写运行时代码** — Claude Code 已经是最好的运行时，不要造轮子
2. **不要在 Persona 里写 workflow 步骤** — 不要教 Claude Code "先 A 后 B"，让它自己决定
3. **不要把 MCP 当信封协议** — MCP 只做确定性工具执行，不做路由

### ✅ 聚焦（要做的事）

1. **定义规范格式** — Capability Registry + Input/Output Schema 的标准格式
2. **提供示例 Persona** — 展示规范怎么落地（哪吒、太白金星等）
3. **提供 Creator 工具** — CLI 帮助用户快速生成新 Persona
4. **提供 MCP Skill 套件** — 常用的确定性工具（文件操作、Git、测试等）
5. **验证核心假设** — Claude Code 读取标准化的 `next_action` 后，能否稳定地自主路由？

## 核心规范

详见 `docs/SPEC.md`。

---
*Powered by Three Realms Protocol*
