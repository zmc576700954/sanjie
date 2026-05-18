# AI-Native Agent Cluster

这是一个基于 **Model Context Protocol (MCP)** 和 **AI-Native Persona** 的去中心化智能体集群架构。该框架旨在打破传统 Python 流水线（Workflow）的臃肿与中心化，通过高度解耦的 Agent 指令集与原子化的 Skill 工具箱，为 Claude Code、Cursor、Gemini CLI 等现代 AI IDE 提供生产级的自动化能力。

## 核心设计哲学：灵肉合一

*   **灵 (Soul - Persona):** 位于 `agents/` 下的独立 Markdown 指令集。定义了智能体的人格、决策流程与协作协议。
*   **肉 (Body - Skill Packages):** 位于 `skills/` 下的原生 MCP 服务器。提供如代码溯源、自动化修复、语义压缩等原子级能力，通过标准协议直接被 IDE 调用。

## 核心能力 (Protocols)

1.  **GSSC 记忆流水线:** 自动化的内存压缩与归档协议，防止 AI 上下文过载。
2.  **A2A (Agent-to-Agent) 通信协议:** 通过标准化的 JSON 数据信封实现去中心化智能体间的无损交接。
3.  **防越权沙盒 (Path Security):** 内置安全沙盒，严防 LLM 越权操作非工作区文件。
4.  **Schema 强制规范:** 所有工具调用均受 Pydantic 校验，确保参数输入准确，极大降低大模型幻觉。

## 快速安装与配置

### 1. 环境准备
确保已安装 Python 3.8+，并安装必要的 MCP SDK：
```bash
pip install mcp pydantic
```

### 2. 插件安装
将 `agents/` 下的 Persona 文件与 `skills/` 下的 MCP 服务器包复制到宿主平台的对应配置目录下。

### 3. IDE 挂载 (以 Claude Code/Cursor 为例)
在您的 `mcp.json` 或平台配置文件中挂载三界宝库：

```json
{
  "mcpServers": {
    "yangjian-server": { "command": "python", "args": ["skills/mcp_servers/tianyan_server.py"] },
    "taibai-server": { "command": "python", "args": ["skills/mcp_servers/taibai_server.py"] },
    "wanglingguan-server": { "command": "python", "args": ["skills/mcp_servers/wanglingguan_server.py"] }
  }
}
```

## 贡献与纪律
本项目开发必须严格遵循项目根目录下的 `GEMINI.md` 协议，禁止任何形式的硬编码中心化调度。所有新贡献的神仙（Agent）或法宝（Skill）均须通过王灵官审计协议验证。

---
*Powered by Celestial Architecture & MCP*
