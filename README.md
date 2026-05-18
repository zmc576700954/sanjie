# 三界 (Three Realms): AI-Native Agent 集群

三界 (Three Realms) 是一个基于 **Model Context Protocol (MCP)** 和 **AI-Native Persona** 的去中心化智能体集群架构。该框架旨在打破传统 Python 流水线（Workflow）的臃肿与中心化，通过高度解耦的 Agent 指令集与原子化的 Skill 工具箱，为 Claude Code、Cursor、Gemini CLI 等现代 AI IDE 提供生产级的自动化能力。

## 核心设计哲学：灵肉合一

*   **灵 (Soul - Persona):** 位于 `agents/` 下的独立 Markdown 指令集。定义了智能体的人格、决策流程与协作协议。
*   **肉 (Body - Skill Packages):** 位于 `mcp-servers/` 下的原生 MCP 服务器。提供如代码溯源、自动化修复、上下文压缩等原子级能力，通过标准协议直接被 IDE 调用。

## 项目结构

```text
/
├── agents/             # 智能体人格定义 (YangJian, Nezha, Taibai 等)
├── mcp-servers/        # MCP 标准服务实现 (运行在宿主 IDE 内部的逻辑)
├── skills/             # 原子化法宝库 (Tool definitions & logic scripts)
├── docs/               # 归档与知识库 (MEMORY_INDEX.md)
├── GEMINI.md           # 开发协议与架构纪律
├── plugin.json         # Claude Code 插件注册清单
└── install.py          # 自动化部署辅助工具
```

## 安装与集成指南

### 1. 环境准备
确保您的系统中已安装 Python 3.8+，并安装核心运行时依赖：
```bash
pip install mcp pydantic
```

### 2. 通过 Claude Code 安装 (插件模式)
如果您使用 Claude Code CLI，可以直接从 GitHub 安装本插件：
```bash
claude plugin install github:zmc576700954/sanjie
```

### 3. 多平台配置指南
为了让 IDE 能够调用集群中的法宝，请根据您的开发环境进行配置：

#### A. Claude Code / Cursor / Trae
在项目根目录的 `.cursor/mcp.json` 或 Claude 配置文件中添加：
```json
{
  "mcpServers": {
    "tianyan-server": { "command": "python", "args": ["mcp-servers/tianyan_server.py"] },
    "taibai-server": { "command": "python", "args": ["mcp-servers/taibai_server.py"] },
    "wanglingguan-server": { "command": "python", "args": ["mcp-servers/wanglingguan_server.py"] }
  }
}
```

#### B. Gemini CLI
在 `~/.gemini/settings.json` 中配置：
```json
{
  "mcpServers": {
    "tianyan-server": { "command": "python", "args": ["mcp-servers/tianyan_server.py"] },
    "taibai-server": { "command": "python", "args": ["mcp-servers/taibai_server.py"] }
  }
}
```

#### C. GitHub Copilot / Codex Desktop
在 VS Code 的 `settings.json` 中配置：
```json
{
  "github.copilot.mcp": {
    "taibai": { "command": "python", "args": ["mcp-servers/taibai_server.py"] }
  }
}
```

> **注意：** 请确保配置中的 `python` 命令指向包含 `mcp` 和 `pydantic` 依赖的虚拟环境。

## 贡献与纪律 (Celestial Protocol)
本项目开发必须严格遵循项目根目录下的 `GEMINI.md` 协议：
1. **绝对去中心化：** 禁止中心化编排，所有 Agent 独立运行。
2. **MCP-First:** 所有工具必须封装为符合 MCP 标准的本地服务器。
3. **安全审计：** 必须通过 WangLingguan 审计协议验证格式准确率。

---
*Powered by Three Realms Architecture & MCP*
