# agents-develop: AI 代码调查、修复与审查工具包

> **pip install agents-develop** — 安装后获得专业级代码调查 + 修复 + 审查能力

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

### 使用

```bash
# 调查错误
agents investigate "用户登录后 session 过期" --file auth.py

# 修复 Bug（自动先调查再修复）
agents fix "null pointer at session lookup" --file session.py

# 修复 + 审查
agents fix "登录超时" --file auth.py --review

# 代码审查
agents review src/auth.py --type security
agents review src/ --type quality
```

### Python SDK

```python
from agents_develop import Investigator, Reviewer
from agents_develop.schemas import InvestigateInput, ReviewInput
from agents_develop.llm_client import LLMClient

llm = LLMClient(provider="anthropic")
investigator = Investigator(llm)
result = investigator.run(InvestigateInput(error_description="session timeout"))
print(result.root_cause)
print(result.confidence)
```

## 架构

```
CLI (agents investigate/fix/review)
  │
  ▼
Orchestrator (路由 + 链式编排)
  │
  ├─→ Investigator SubAgent
  │     ├─ system prompt (from yangjian.md)
  │     └─ tools: logic_tracer, cross_verifier, semantic_analyzer
  │
  ├─→ Fixer SubAgent
  │     ├─ system prompt (from nezha.md)
  │     └─ tools: demon_hunt, lotus_body
  │
  └─→ Reviewer SubAgent
        ├─ system prompt (from wanglingguan.md)
        └─ tools: security_scanner, semantic_analyzer
```

每个 SubAgent 是一个 Python 类，封装：
- **系统 prompt**（来自 `agents/*.md` 提炼）
- **工具列表**（来自 `skills/tool_*/` 封装）
- **输入输出 Schema**（Pydantic 模型，可程序化验证）

## 项目结构

```
agents_develop/
├── src/agents_develop/       # 可安装的 Python 包
│   ├── cli.py                # CLI 入口
│   ├── orchestrator.py       # 路由 + 编排
│   ├── base.py               # SubAgent 基类
│   ├── schemas.py            # Pydantic I/O 模型
│   ├── llm_client.py         # LLM API 抽象（Anthropic/OpenAI）
│   ├── config.py             # 配置管理
│   ├── agents/               # SubAgent 实现
│   ├── tools/                # 工具封装层
│   └── prompts/              # 系统 prompt
│
├── agents/                   # 原始 Agent 定义（保留）
├── skills/                   # 原始 Skill 脚本（保留）
├── mcp-servers/              # MCP Server（Claude Code 集成）
├── tests/                    # 测试套件
└── docs/
    ├── SPEC.md               # Three Realms 协议规范
    └── superpowers/          # 设计文档和实现计划
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v

# 运行 CLI
agents --help
```

## 技术栈

- Python 3.10+
- Pydantic v2（I/O Schema）
- Anthropic SDK / OpenAI SDK（LLM 调用）
- Click（CLI）
- pytest（测试）

## 原始项目说明

本项目源自"三界（Three Realms）"协议 — 一套 AI IDE 多角色协作规范。原始设计文档见 `docs/SPEC.md`。

v2.0 重构为可独立运行的 Python 包，保留了原始 Persona prompt 和 Skill 脚本作为 SubAgent 的底层实现。

---

*Powered by Three Realms Protocol*
