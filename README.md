# 三界 (Three Realms): AI-Native Agent 集群

三界 (Three Realms) 是一个基于 **Model Context Protocol (MCP)** 和 **AI-Native Persona** 的去中心化智能体集群架构。它彻底抛弃了臃肿的中心化 Python 调度器，通过高度解耦的 Agent 指令集与原子化的 Skill 工具箱，为 Claude Code、Cursor 等现代 AI IDE 提供生产级的自动化能力。

## 核心设计哲学：灵肉合一

*   **灵 (Soul - Persona):** 位于 `agents/` 下的独立 Markdown 指令集。定义了智能体的人格（如调查专家、执行专家）、决策流程与协作协议。
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

## 安装指南

### 1. 环境准备
确保您的系统中已安装 Python 3.8+，并安装核心运行时依赖：
```bash
pip install mcp pydantic
```

### 2. 通过 Claude Code 安装
如果您使用 Claude Code CLI，可以直接从 GitHub 安装本插件：
```bash
claude plugin install github:zmc576700954/sanjie
```

## 多平台配置指南

要将“三界”集群集成到您的开发环境中，请根据使用的工具添加以下 MCP 配置：

### 1. Claude Code / Cursor / Trae
在项目的 `.cursor/mcp.json` 或 Claude 配置中添加：

```json
{
  "mcpServers": {
    "yangjian-server": { "command": "python", "args": ["mcp-servers/tianyan_server.py"] },
    "taibai-server": { "command": "python", "args": ["mcp-servers/taibai_server.py"] },
    "wanglingguan-server": { "command": "python", "args": ["mcp-servers/wanglingguan_server.py"] }
  }
}
```

### 2. Gemini CLI
在 `~/.gemini/settings.json` 中配置：

```json
{
  "mcpServers": {
    "tianyan-server": { "command": "python", "args": ["mcp-servers/tianyan_server.py"] },
    "taibai-server": { "command": "python", "args": ["mcp-servers/taibai_server.py"] },
    "wanglingguan-server": { "command": "python", "args": ["mcp-servers/wanglingguan_server.py"] }
  }
}
```

### 3. GitHub Copilot / Codex Desktop
在 VS Code 的 `settings.json` 中找到 `github.copilot.mcp` 或通过 Copilot 扩展面板添加：

```json
{
  "github.copilot.mcp": {
    "taibai": { "command": "python", "args": ["mcp-servers/taibai_server.py"] }
  }
}
```

*(注意：请确保系统中 `python` 命令指向包含 `mcp` 依赖的虚拟环境)*

## 核心能力 (Protocols)

1.  **GSSC 记忆流水线:** 自动化的内存压缩与归档协议，防止 AI 上下文过载。
2.  **A2A (Agent-to-Agent) 通信协议:** 通过标准化的 `A2A_HANDOFF` JSON 数据信封实现去中心化智能体间的无损交接。
3.  **防越权沙盒 (Path Security):** 内置安全沙盒，严防 LLM 越权操作非工作区文件。
4.  **Schema 强制规范:** 所有工具调用均受 Pydantic 校验，确保参数输入准确，极大降低大模型幻觉。

## 贡献与纪律
本项目开发必须严格遵循项目根目录下的 `GEMINI.md` 协议，禁止任何形式的硬编码中心化调度。所有新贡献的 Agent 或 Skill 均须通过王灵官审计协议验证。

---
*Powered by Three Realms Architecture & MCP*
