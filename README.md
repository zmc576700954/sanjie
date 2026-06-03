# agents-develop: AI 代码调查、修复与审查工具包

> **pip install agents-develop** — 安装后获得专业级代码调查 + 修复 + 审查 + 文档生成能力

## 快速开始

### 安装

```bash
pip install agents-develop
```

### 配置

```bash
# 设置 LLM Provider
agents config set-provider anthropic  # 或 openai
agents config set-key sk-xxx

# 可选：设置模型
agents config set-model claude-sonnet-4-20250514
```

### CLI 命令

```bash
# 调查错误根因
agents investigate "用户登录后 session 过期" --file auth.py

# 修复 Bug（自动先调查再修复）
agents fix "null pointer at session lookup" --file session.py

# 修复 + 审查
agents fix "登录超时" --file auth.py --review

# 代码审查
agents review src/auth.py --type security
agents review src/ --type quality

# 生成文档（GSSC 流水线）
agents document src/auth.py --doc-type spec --output docs/auth-spec.md

# 全流程管线：调查 → 修复 → 审查
agents pipeline "session timeout" --file auth.py

# 任务路由：查看哪个 Skill 匹配当前任务
agents route "帮我修一个登录超时的 bug"
```

### Python SDK

```python
from agents_develop import Investigator, Reviewer, Fixer, Documenter
from agents_develop.schemas import (
    InvestigateInput, FixInput, ReviewInput, DocumentInput,
    TokenBudget,
)
from agents_develop.llm_client import LLMClient
from agents_develop.orchestrator import Orchestrator

llm = LLMClient(provider="anthropic")

# 单独使用 SubAgent
investigator = Investigator(llm)
result = investigator.run(InvestigateInput(error_description="session timeout"))
print(result.root_cause, result.confidence)

# 使用 Orchestrator 编排管线
orch = Orchestrator(llm, token_budget=TokenBudget(total=200_000))
pipeline_result = orch.full_pipeline(FixInput(
    error_description="session timeout",
    target_files=["auth.py"],
))
print(pipeline_result.stages, pipeline_result.total_tokens)
```

## 架构

```
CLI (agents investigate/fix/review/document/pipeline/route)
  │
  ▼
Orchestrator (路由 + 链式编排 + 并行扇出)
  │
  ├─→ Investigator SubAgent (yangjian.md)
  │     └─ tools: trace_error, cross_verify, analyze_complexity
  │
  ├─→ Fixer SubAgent (nezha.md)
  │     └─ tools: demon_hunt, lotus_body, assess_workload
  │
  ├─→ Reviewer SubAgent (wanglingguan.md)
  │     └─ tools: scan_file, scan_secrets, scan_all
  │
  ├─→ Documenter SubAgent (taibai.md)
  │     └─ tools: compress_context, run_gssc_pipeline
  │
  └─→ Skill Bridge (关键词路由 → 9 个 Skill)
        └─ nezha / tianyan / wanglingguan / yindan / taibai / taie / sanjian / kaishan / bajiu
```

**关键特性：**
- **Token Budget 控制** — 整条管线共享 Token 预算，防止超支
- **并行扇出** — 多文件 Review 并发执行（`parallel_review`）
- **错误感知降级** — 某阶段失败不阻塞后续阶段
- **Agent Handoff 协议** — SubAgent 间通过结构化 Schema 传递上下文
- **Tracing Spans** — 全链路可观测

## 项目结构

```
agents_develop/
├── src/agents_develop/         # 可安装的 Python 包
│   ├── cli.py                  # CLI 入口（click）
│   ├── orchestrator.py         # 路由 + 编排 + 并行扇出
│   ├── base.py                 # SubAgent 基类（熔断器、预算控制）
│   ├── schemas.py              # Pydantic I/O 模型 + Handoff + Budget + Tracing
│   ├── llm_client.py           # LLM API 抽象（Anthropic / OpenAI）
│   ├── config.py               # 配置管理
│   ├── skill_bridge.py         # Agent-Skill 桥接（关键词路由注册表）
│   ├── agents/                 # SubAgent 实现
│   │   ├── investigator.py     # 调查 Agent
│   │   ├── fixer.py            # 修复 Agent
│   │   ├── reviewer.py         # 审查 Agent
│   │   └── documenter.py       # 文档 Agent
│   ├── tools/                  # 工具封装层
│   │   ├── code_analysis.py    # 逻辑追踪、交叉验证、复杂度分析
│   │   ├── code_modification.py# demon_hunt、lotus_body 等修复工具
│   │   ├── security_scan.py    # 安全扫描、密钥检测
│   │   └── doc_tools.py        # 上下文压缩、GSSC 文档流水线
│   └── prompts/                # 各 SubAgent 的系统 prompt
│
├── agents/                     # 原始 Persona 定义（三界协议格式）
│   ├── yangjian.md             # 调查者 Persona
│   ├── nezha.md                # 修复者 Persona
│   ├── wanglingguan.md         # 审查者 Persona
│   ├── taibai.md               # 文档者 Persona
│   └── jinzha.md               # 辅助 Persona
│
├── skills/                     # Skill 定义（SKILL.md + 脚本）
│   ├── tool_nezha/             # 修复 Skill
│   ├── tool_tianyan/           # 调查 Skill
│   ├── tool_wanglingguan/      # 审查 Skill
│   ├── tool_yindan/            # 精准修复 Skill
│   ├── tool_taibai/            # 文档 Skill
│   ├── tool_taie/              # 新功能开发 Skill
│   ├── tool_sanjian/           # 多文件重构 Skill
│   ├── tool_kaishan/           # 批量操作 Skill
│   ├── tool_bajiu/             # 任务路由 Skill
│   └── utils.py                # Skill 公共工具
│
├── mcp-servers/                # MCP Server（Claude Code 集成）
│   ├── taibai_server.py
│   ├── tianyan_server.py
│   ├── wanglingguan_server.py
│   └── yindan_server.py
│
├── a2a_inbox/                  # Agent-to-Agent 消息信箱
│   └── review_tickets/         # 审查工单（JSON 格式）
│
├── tools/                      # 开发者工具
│   └── create_persona.py       # Persona 模板生成器
│
├── tests/                      # 测试套件
├── docs/                       # 设计文档
│   ├── SPEC.md                 # 三界协议规范
│   └── superpowers/            # 设计文档和实现计划
├── scripts/                    # 脚本目录
└── pyproject.toml              # 项目配置
```

## 9 个 Skill 一览

| Skill | 用途 | 触发关键词示例 |
|-------|------|--------------|
| **nezha** | Bug 修复、代码修改 | 修复bug, fix bug, patch |
| **tianyan** | 调查、逻辑追踪、根因分析 | 追踪, 诊断, root cause |
| **wanglingguan** | 合规审查、安全扫描 | 安全扫描, 合规检查, OWASP |
| **yindan** | 单点精准修复 | 精准修复, 精确替换 |
| **taibai** | 文档管理、上下文压缩 | 写文档, 归档, GSSC |
| **taie** | 新功能开发 | 新功能, add feature |
| **sanjian** | 多文件重构 | 多文件重构, 架构重组 |
| **kaishan** | 批量删除、大规模清理 | 批量删除, 全局替换, nuke |
| **bajiu** | 任务路由、难度评估 | 哪个工具, 任务拆解, triage |

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v

# 查看 CLI 帮助
agents --help
agents investigate --help
agents pipeline --help
```

## 技术栈

- Python 3.10+
- Pydantic v2（I/O Schema + Handoff 协议 + Token Budget）
- Anthropic SDK / OpenAI SDK（LLM 调用）
- Click（CLI）
- tree-sitter（多语言代码分析）
- pytest（测试）

## 项目起源

本项目源自 **三界（Three Realms）协议** — 一套 AI IDE 多角色协作规范（L3 Config 层）。原始设计文档见 `docs/SPEC.md`。

v2.0 重构为可独立运行的 Python 包，保留了原始 Persona prompt（`agents/`）和 Skill 脚本（`skills/`）作为 SubAgent 的底层实现，并新增了 Orchestrator 编排层、Skill Bridge 路由、Agent Handoff 协议等生产化能力。

---

*Powered by Three Realms Protocol*
