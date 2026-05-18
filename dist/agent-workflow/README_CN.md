# Agent Workflow — 风险分级的 AI 编码代理技能框架

[English](README.md) | 中文

一套面向 AI 编码工具的**热插拔技能系统**。将技能安装到你的 AI IDE 中，代理自动发现并使用它们，同时根据操作风险等级施加相应的安全护栏。

## 核心特性

- **热插拔技能** — 安装即生效，无需修改代理配置
- **风险分级** — 不同破坏性的操作对应不同强度的安全机制
- **跨平台** — 支持 Claude Code、Cursor、Codex、Trae
- **零依赖** — 仅使用 Python 标准库
- **一键安装** — 单条命令完成平台适配

## 快速开始

```bash
git clone https://github.com/yourname/agent-workflow.git
cd agent-workflow

# 选择你的平台，一键安装
python install.py --platform claude-code
python install.py --platform cursor
python install.py --platform codex
python install.py --platform trae

# 也可以只安装单个技能
python install.py --skill sanjian --platform claude-code
```

## 设计理念

### 为什么需要这个框架？

AI 编码工具（Claude Code、Cursor 等）本身已经很强大，但面对复杂任务时缺乏**结构化的执行流程**和**风险控制机制**。本框架通过 Skill（技能）为 AI 模型提供：

1. **规范化的执行流程** — 告诉 AI "遇到这类任务时，按什么步骤做"
2. **风险分级的安全护栏** — 小修复直接执行，大重构必须经过用户确认
3. **可组合的能力扩展** — 用户可以自由开发新技能，装进去就能用

### Agent 与 Skill 的关系

```
Agent（杨戬）
├── 固有技能：tianyan（天眼，不可卸载）
├── 技能发现：自动扫描已安装的技能库
├── 路由引擎：根据任务难度匹配最合适的技能
└── 执行：调用匹配的技能，施加对应的安全护栏
```

Agent 不硬编码可用技能列表。它在运行时从技能库中动态发现已安装的技能。安装新技能后，Agent 自动适配，无需任何配置变更。

## 技能一览

| 技能 | 定位 | 风险等级 | 核心机制 |
|------|------|---------|---------|
| `tianyan` | 调查与逻辑溯源 | 无（只读） | 错误分类 → 根因分析 → 生成移交报告 |
| `bajiu_xuangong` | 任务路由与难度评估 | 无（无副作用） | 扫描技能库 → 7因子评估 → 输出执行计划 |
| `yindan` | 精准单点修复 | 低 | 精确文本替换 → 语法校验 → 失败回滚 |
| `taie` | 常规功能开发 | 中 | 风险评估 → 用户确认 → AST 回归检测 → 失败回滚 |
| `sanjian` | 多文件重构 | 高 | 依赖分析 → 任务拆解 → 范围管控 → 备份执行 → 结果整合 |
| `kaishan` | 大范围破坏性操作 | 极高 | 影响面评估 → 强制用户确认 → 执行 → 销毁日志 |

## 工作流程

```
用户请求
    ↓
┌─────────────────────────────────────────────┐
│  tianyan（调查）                              │
│  分析错误 → 追溯逻辑 → 生成移交报告          │
└────────────────────┬────────────────────────┘
                     ↓
┌─────────────────────────────────────────────┐
│  bajiu_xuangong（路由）                       │
│  扫描已安装技能 → 评估难度 → 匹配最优技能     │
└────────────────────┬────────────────────────┘
                     ↓
┌─────────────────────────────────────────────┐
│  执行技能（根据难度自动选择）                  │
│  TRIVIAL → yindan                            │
│  MODERATE → taie                             │
│  COMPLEX → sanjian（需用户确认）              │
│  CRITICAL → kaishan（需用户确认 + 日志）      │
└─────────────────────────────────────────────┘
```

## 平台支持

| 平台 | 技能安装位置 | Agent/规则位置 | 安装命令 |
|------|------------|--------------|---------|
| Claude Code | `~/.claude/skills/` | `~/.claude/agents/` | `python install.py --platform claude-code` |
| Cursor | `~/.cursor/skills/` | `~/.cursor/agents/` | `python install.py --platform cursor` |
| Codex | `~/.agents/skills/` | 根目录 `AGENTS.md` | `python install.py --platform codex` |
| Trae | `.trae/skills/` | `.trae/rules/` | `python install.py --platform trae` |

## 手动安装

如果你更喜欢手动操作：

```bash
# 安装技能（以 Claude Code 为例，其他平台替换目标路径即可）
cp -r skills/tianyan ~/.claude/skills/
cp -r skills/sanjian ~/.claude/skills/
cp -r skills/yindan ~/.claude/skills/

# 安装 Agent 定义
cp platforms/claude-code/agents/yangjian.md ~/.claude/agents/
```

## 项目结构

```
agent-workflow/
├── skills/                      技能包（跨平台通用）
│   ├── tianyan/                  调查与逻辑溯源
│   │   ├── SKILL.md             AI 执行指令
│   │   └── scripts/             工具脚本
│   │       └── logic_tracer.py
│   ├── bajiu_xuangong/           任务路由
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       ├── skill_scanner.py
│   │       └── task_analyzer.py
│   ├── sanjian/                  多文件重构
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   ├── dependency_analyzer.py
│   │   │   ├── task_decomposer.py
│   │   │   ├── scope_guardian.py
│   │   │   ├── executor.py
│   │   │   └── result_integrator.py
│   │   └── references/
│   │       └── refactoring_patterns.md
│   ├── yindan/                   精准修复
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── precise_fix.py
│   ├── taie/                     功能开发
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       ├── risk_assessor.py
│   │       └── standard_write.py
│   └── kaishan/                  大范围操作
│       ├── SKILL.md
│       └── scripts/
│           ├── blast_assessor.py
│           └── bulk_operations.py
├── platforms/                   平台适配层
│   ├── claude-code/agents/      Claude Code Agent 定义
│   ├── cursor/agents/           Cursor Agent 定义
│   ├── codex/                   Codex AGENTS.md
│   └── trae/rules/             Trae 规则文件
├── docs/                        文档
│   ├── architecture.md          架构设计说明
│   └── contributing.md          贡献指南
├── tests/                       测试
│   └── test_skills_scripts.py   14 项功能测试
├── install.py                   一键安装脚本
├── AGENTS.md                    Agent 编排规则
├── CONTRIBUTING.md              贡献指南
├── README.md                    英文文档
├── README_CN.md                 中文文档（本文件）
└── pyproject.toml               Python 项目配置
```

## 开发自定义技能

每个技能是一个独立的文件夹，包含：

```
my-skill/
├── SKILL.md          # AI 执行指令（必需）
├── __init__.py       # Python 包标识
├── scripts/          # 工具脚本
│   ├── __init__.py
│   └── my_tool.py
└── references/       # 按需加载的参考资料（可选）
    └── patterns.md
```

### SKILL.md 编写规范

```markdown
---
name: my-skill
description: >
  Use when [触发条件].
  Handles [能力描述].
  Do NOT use for [排除条件].
---

# 技能标题

## Workflow

1. 第一步（祈使句，具体动作）
2. 第二步
3. 验证步骤

## Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `scripts/my_tool.py` | 做什么 | `参数1`, `参数2` | `{返回结构}` |

## Rules

- 约束条件一
- 约束条件二
```

**关键原则：**
- `description` 只说"何时触发"和"有什么能力"，不泄露具体流程
- Body 用祈使句编号步骤，不用解释性散文
- Scripts 只做确定性操作，返回结构化数据，不输出装饰性内容
- 控制在 500 行以内

### 安装自定义技能

```bash
# 将技能文件夹放入 skills/ 目录后
python install.py --skill my-skill --platform claude-code
```

## 测试

```bash
# 运行所有测试
python -m pytest tests -q

# 运行技能脚本功能测试
python -m tests.test_skills_scripts
```

## 与同类项目的区别

| 特性 | Agent Workflow | LangGraph/CrewAI | Cursor Rules |
|------|--------------|-----------------|--------------|
| 定位 | AI 工具的 Prompt 资产 | 独立 Python 运行时 | IDE 配置文件 |
| 安装方式 | 复制文件到平台目录 | pip install + 代码集成 | 项目内 .cursor/ |
| 跨平台 | 4 平台通用 | 平台无关（自带运行时） | 仅 Cursor |
| 热插拔 | 安装即生效 | 需要代码修改 | 需要重启 |
| 风险控制 | 内置分级护栏 | 需自行实现 | 无 |

## 贡献

参见 [CONTRIBUTING.md](CONTRIBUTING.md) 和 [docs/architecture.md](docs/architecture.md)。

## 许可证

见 [LICENSE](LICENSE)。
