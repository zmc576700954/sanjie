# Agents Develop Environment Design Spec

**Date:** 2025-06-25
**Type:** Architecture Design
**Status:** Approved
**Version:** 2.0

## Overview

A personal development repository for building custom Agents, Skills, and Python tools with multi-tool migration support. This environment allows developers to create components once and deploy them across multiple AI development tools (Claude Code CLI, Claude Desktop, ZCode, Cursor, Reasionix) through format adaptation.

## Problem Statement

Modern AI development tools have different approaches to custom extensions:
- **Claude Code/Desktop**: SKILL.md format, plugins, custom slash commands
- **ZCode**: Command.md format, custom commands
- **Cursor**: SKILL.md format, JSON configuration
- **Reasionix**: Script-based approach (Deepseek optimized)
- **All tools**: Support MCP (Model Context Protocol)

**Core Challenge:** Need a unified development environment where:
1. Components can be developed and tested independently
2. Migration to different tools is simple and automated
3. Core functionality is tool-agnostic
4. Different tools get appropriate format adaptations

## Architecture

### Core Principle: Core + Format Separation

The architecture separates core functionality from tool-specific formats:

```
Core Implementation (Tool-Agnostic) + Format Adapters (Tool-Specific) = Complete Component
```

### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Developer Workflow                           │
│                                                                 │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │  Create   │───▶│   Generate   │───▶│     Export / Deploy   │  │
│  │  Core     │    │   Formats    │    │     to Target Tool    │  │
│  └──────────┘    └──────────────┘    └──────────────────────┘  │
│       │                │                       │                │
│       ▼                ▼                       ▼                │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │  Test     │    │   Validate   │    │     Verify in         │  │
│  │  Core     │    │   Formats    │    │     Target Env        │  │
│  └──────────┘    └──────────────┘    └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

Component Data Flow:
┌────────────┐     ┌─────────────┐     ┌──────────────────┐
│  core/*.py │────▶│ manifest.json│────▶│ Format Generators │
│  (logic)   │     │ (metadata)   │     │ (per-tool adapt)  │
└────────────┘     └─────────────┘     └────────┬─────────┘
                                                 │
                    ┌────────────────────────────┼────────────────┐
                    ▼                ▼            ▼                ▼
              ┌──────────┐   ┌──────────┐  ┌──────────┐   ┌──────────┐
              │ claude/  │   │ zcode/   │  │ cursor/  │   │ mcp/     │
              │ SKILL.md │   │Command.md│  │ SKILL.md │   │server.py │
              └──────────┘   └──────────┘  └──────────┘   └──────────┘
```

### Directory Structure

```
agents_develop/
├── core/                          # 核心实现（工具无关）
│   ├── __init__.py
│   ├── agents/                    # Agent核心逻辑
│   │   ├── __init__.py
│   │   ├── base.py               # Agent基类
│   │   └── registry.py           # Agent注册表
│   ├── skills/                    # Skill核心实现
│   │   ├── __init__.py
│   │   ├── base.py               # Skill基类
│   │   └── registry.py           # Skill注册表
│   ├── tools/                     # Python工具库
│   │   ├── __init__.py
│   │   ├── base.py               # Tool基类
│   │   └── registry.py           # Tool注册表
│   ├── shared/                    # 共享工具函数
│   │   ├── __init__.py
│   │   ├── config.py             # 配置管理
│   │   ├── logging.py            # 日志工具
│   │   ├── errors.py             # 统一错误定义
│   │   └── utils.py              # 通用工具函数
│   └── mcp_base/                  # MCP服务器基础
│       ├── __init__.py
│       ├── server.py             # MCP服务器基类
│       └── tool_def.py           # MCP工具定义基类
│
├── formats/                       # 不同工具的格式定义
│   ├── __init__.py
│   ├── claude/
│   │   ├── __init__.py
│   │   ├── SKILL.md.template      # Claude技能模板
│   │   ├── plugin_config.json     # 插件配置模板
│   │   └── slash_commands/        # 斜杠命令定义
│   │       └── template.md
│   ├── zcode/
│   │   ├── __init__.py
│   │   ├── Command.md.template    # ZCode命令模板
│   │   └── command_config/        # 命令配置
│   │       └── template.json
│   ├── cursor/
│   │   ├── __init__.py
│   │   ├── SKILL.md.template      # Cursor技能模板
│   │   └── cursor_config.json     # Cursor配置
│   ├── reasionix/
│   │   ├── __init__.py
│   │   ├── script_templates/      # 脚本模板
│   │   │   └── template.py
│   │   └── deepseek_config/       # Deepseek优化配置
│   │       └── template.json
│   └── mcp/
│       ├── __init__.py
│       ├── mcp_server.py.template # MCP服务器模板
│       └── mcp_config.json        # MCP配置模板
│
├── components/                    # 完整组件（核心+所有格式）
│   ├── _example/                  # 示例组件（开发参考）
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── example_skill.py
│   │   ├── formats/
│   │   │   ├── claude/SKILL.md
│   │   │   ├── zcode/Command.md
│   │   │   ├── cursor/SKILL.md
│   │   │   ├── reasionix/script.py
│   │   │   └── mcp/mcp_server.py
│   │   └── manifest.json
│   └── README.md                  # 组件库说明
│
├── migration/                     # 迁移工具
│   ├── __init__.py
│   ├── generators/                # 格式生成器
│   │   ├── __init__.py
│   │   ├── base.py               # 生成器基类
│   │   ├── claude_generator.py
│   │   ├── zcode_generator.py
│   │   ├── cursor_generator.py
│   │   ├── reasionix_generator.py
│   │   └── mcp_generator.py
│   ├── validators/                # 格式验证器
│   │   ├── __init__.py
│   │   ├── base.py               # 验证器基类
│   │   ├── claude_validator.py
│   │   ├── zcode_validator.py
│   │   ├── cursor_validator.py
│   │   └── mcp_validator.py
│   └── exporter.py                # 统一导出工具
│
├── cli/                           # 命令行接口
│   ├── __init__.py
│   ├── main.py                    # CLI入口
│   ├── create_cmd.py              # create 命令
│   ├── generate_cmd.py            # generate 命令
│   ├── export_cmd.py              # export 命令
│   ├── validate_cmd.py            # validate 命令
│   └── list_cmd.py                # list 命令
│
├── templates/                     # 项目模板
│   ├── claude_project/            # Claude项目模板
│   ├── zcode_project/             # ZCode项目模板
│   ├── cursor_project/            # Cursor项目模板
│   └── universal_project/         # 通用项目模板
│
├── tests/                         # 测试
│   ├── __init__.py
│   ├── conftest.py                # 测试配置和fixtures
│   ├── core/                      # 核心测试
│   │   ├── test_base.py
│   │   ├── test_registry.py
│   │   └── test_shared.py
│   ├── formats/                   # 格式测试
│   │   ├── test_claude_format.py
│   │   ├── test_zcode_format.py
│   │   └── test_mcp_format.py
│   ├── migration/                 # 迁移测试
│   │   ├── test_generators.py
│   │   ├── test_validators.py
│   │   └── test_exporter.py
│   └── integration/               # 集成测试
│       ├── test_create_and_export.py
│       └── test_full_workflow.py
│
├── docs/                          # 文档
│   ├── architecture.md            # 架构说明
│   ├── migration_guide.md         # 迁移指南
│   ├── format_specs/              # 格式规范
│   │   ├── claude_format.md
│   │   ├── zcode_format.md
│   │   ├── cursor_format.md
│   │   └── mcp_format.md
│   ├── component_development.md   # 组件开发指南
│   └── cli_reference.md           # CLI参考手册
│
├── pyproject.toml                 # 项目配置
├── CLAUDE.md                      # Claude Code指令
├── GEMINI.md                      # Gemini指令
├── .gitignore
└── README.md
```

## Core Interface Definitions

### Base Classes

All core components inherit from a common base that defines the contract:

```python
# core/shared/base.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class ComponentType(Enum):
    AGENT = "agent"
    SKILL = "skill"
    TOOL = "tool"
    MCP_SERVER = "mcp_server"


@dataclass
class ComponentMetadata:
    """组件元数据 - 与 manifest.json 对应"""
    name: str
    type: ComponentType
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    created: str = ""
    updated: str = ""
    tags: List[str] = field(default_factory=list)
    core_dependencies: List[str] = field(default_factory=list)
    supported_tools: List[str] = field(default_factory=lambda: ["claude", "zcode", "cursor", "reasionix", "mcp"])
    config_schema: Dict[str, Any] = field(default_factory=dict)  # JSON Schema for component config


class CoreComponent(ABC):
    """所有核心组件的基类"""

    def __init__(self, metadata: ComponentMetadata):
        self._metadata = metadata
        self._config: Dict[str, Any] = {}

    @property
    def metadata(self) -> ComponentMetadata:
        return self._metadata

    @property
    def name(self) -> str:
        return self._metadata.name

    @property
    def component_type(self) -> ComponentType:
        return self._metadata.type

    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行组件核心逻辑"""
        pass

    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据"""
        pass

    def configure(self, config: Dict[str, Any]) -> None:
        """配置组件"""
        self._config = config

    def get_config_schema(self) -> Dict[str, Any]:
        """获取配置的JSON Schema"""
        return self._metadata.config_schema

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典（供格式生成器使用）"""
        return {
            "name": self.name,
            "type": self.component_type.value,
            "version": self._metadata.version,
            "description": self._metadata.description,
            "config_schema": self._metadata.config_schema,
        }
```

### Agent Interface

```python
# core/agents/base.py

class AgentBase(CoreComponent):
    """Agent基类 - 具有角色定义和工具调用的智能体"""

    def __init__(self, metadata: ComponentMetadata):
        super().__init__(metadata)
        self._system_prompt: str = ""
        self._tools: List[Dict[str, Any]] = []

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Agent的系统提示词"""
        pass

    @property
    @abstractmethod
    def available_tools(self) -> List[Dict[str, Any]]:
        """Agent可用的工具定义列表"""
        pass

    @abstractmethod
    def plan(self, task: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """规划任务执行步骤"""
        pass

    @abstractmethod
    def reflect(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """反思执行结果，决定是否需要调整"""
        pass

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Agent执行入口"""
        task = input_data.get("task", "")
        context = input_data.get("context", {})
        steps = self.plan(task, context)
        results = []
        for step in steps:
            step_result = self._execute_step(step)
            reflection = self.reflect(step_result)
            if reflection.get("needs_adjustment"):
                steps = self.plan(task, {**context, "reflection": reflection})
            results.append(step_result)
        return {"steps": steps, "results": results}

    def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个步骤（子类可覆盖）"""
        return step
```

### Skill Interface

```python
# core/skills/base.py

class SkillBase(CoreComponent):
    """Skill基类 - 可复用的技能模块"""

    def __init__(self, metadata: ComponentMetadata):
        super().__init__(metadata)
        self._instructions: str = ""
        self._examples: List[Dict[str, str]] = []

    @property
    @abstractmethod
    def instructions(self) -> str:
        """Skill的使用指令（将转化为SKILL.md/Command.md的内容）"""
        pass

    @property
    def examples(self) -> List[Dict[str, str]]:
        """使用示例"""
        return self._examples

    @abstractmethod
    def get_checklist(self) -> List[str]:
        """Skill执行检查清单"""
        pass

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入是否符合Skill要求"""
        required = self._metadata.config_schema.get("required", [])
        return all(key in input_data for key in required)

    def to_skill_md(self) -> str:
        """生成SKILL.md格式的指令内容（工具无关的纯文本）"""
        checklist = "\n".join(f"- [ ] {item}" for item in self.get_checklist())
        examples_text = ""
        for ex in self.examples:
            examples_text += f"\n**Input:** {ex.get('input', '')}\n**Output:** {ex.get('output', '')}\n"

        return f"""# {self.name}

{self._metadata.description}

## Instructions

{self.instructions}

## Checklist

{checklist}

## Examples
{examples_text}
"""
```

### Tool Interface

```python
# core/tools/base.py

class ToolBase(CoreComponent):
    """Tool基类 - Python工具函数"""

    def __init__(self, metadata: ComponentMetadata):
        super().__init__(metadata)
        self._function_defs: List[Dict[str, Any]] = []

    @property
    @abstractmethod
    def function_definitions(self) -> List[Dict[str, Any]]:
        """工具函数定义列表（MCP tool格式）"""
        pass

    @abstractmethod
    def run(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        """执行指定工具函数"""
        pass

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Tool执行入口"""
        func_name = input_data.get("function", "")
        args = input_data.get("arguments", {})
        result = self.run(func_name, args)
        return {"function": func_name, "result": result}
```

### MCP Server Base

```python
# core/mcp_base/server.py

class MCPServerBase(ABC):
    """MCP服务器基类"""

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self._tools: List[ToolBase] = []

    def register_tool(self, tool: ToolBase) -> None:
        """注册工具到MCP服务器"""
        self._tools.append(tool)

    @abstractmethod
    def get_server_info(self) -> Dict[str, Any]:
        """获取服务器信息"""
        pass

    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有已注册工具"""
        all_defs = []
        for tool in self._tools:
            all_defs.extend(tool.function_definitions)
        return all_defs

    def call_tool(self, tool_name: str, function_name: str, arguments: Dict[str, Any]) -> Any:
        """调用指定工具的函数"""
        for tool in self._tools:
            if tool.name == tool_name:
                return tool.run(function_name, arguments)
        raise ToolNotFoundError(f"Tool '{tool_name}' not found")
```

### Registry

```python
# core/shared/registry.py

class ComponentRegistry:
    """组件注册表 - 管理所有已注册的组件"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._components: Dict[str, CoreComponent] = {}
            cls._instance._by_type: Dict[ComponentType, List[str]] = {
                t: [] for t in ComponentType
            }
        return cls._instance

    def register(self, component: CoreComponent) -> None:
        """注册组件"""
        name = component.name
        if name in self._components:
            raise DuplicateComponentError(f"Component '{name}' already registered")
        self._components[name] = component
        self._by_type[component.component_type].append(name)

    def get(self, name: str) -> CoreComponent:
        """获取组件"""
        if name not in self._components:
            raise ComponentNotFoundError(f"Component '{name}' not found")
        return self._components[name]

    def list_by_type(self, component_type: ComponentType) -> List[CoreComponent]:
        """按类型列出组件"""
        return [self._components[name] for name in self._by_type.get(component_type, [])]

    def list_all(self) -> List[CoreComponent]:
        """列出所有组件"""
        return list(self._components.values())

    def unregister(self, name: str) -> None:
        """取消注册"""
        if name in self._components:
            component = self._components.pop(name)
            self._by_type[component.component_type].remove(name)
```

## Key Components

### 1. Core Layer (`core/`)

**Purpose:** Tool-agnostic implementation of agents, skills, and tools.

**Components:**
- `agents/`: Domain-specific and workflow orchestration agents
- `skills/`: Reusable skill implementations
- `tools/`: Python utility functions and libraries
- `shared/`: Common utilities, helpers, and base classes
- `mcp_base/`: Base MCP server implementation

**Design Principles:**
- Zero dependency on tool-specific formats
- Pure Python implementation
- Clear interfaces and contracts (defined above)
- Comprehensive unit testing
- All components are serializable (via `to_dict()`) for format generation

### 2. Format Definitions (`formats/`)

**Purpose:** Define templates and specifications for each tool's format requirements.

**Components:**
- Tool-specific templates (SKILL.md, Command.md, etc.)
- Configuration file templates
- Best practices and conventions
- Format validators

**Template Variable System:**

All format templates use a `{{variable}}` syntax for substitution:

| Variable | Source | Description |
|----------|--------|-------------|
| `{{name}}` | manifest.json | Component name |
| `{{type}}` | manifest.json | Component type |
| `{{version}}` | manifest.json | Version |
| `{{description}}` | manifest.json | Description |
| `{{instructions}}` | core skill.instructions | Skill instructions text |
| `{{checklist}}` | core skill.get_checklist() | Checklist items |
| `{{examples}}` | core skill.examples | Usage examples |
| `{{tools}}` | core tool.function_definitions | Tool definitions |
| `{{system_prompt}}` | core agent.system_prompt | Agent system prompt |
| `{{config_schema}}` | manifest.json | Configuration JSON Schema |
| `{{dependencies}}` | manifest.json | Python dependencies |

### 3. Component Library (`components/`)

**Purpose:** Complete, ready-to-use components with all format adaptations.

**Structure per Component:**
```
component_name/
├── core/              # Tool-agnostic implementation
│   ├── __init__.py
│   └── <component>.py
├── formats/           # All tool-specific adaptations
│   ├── claude/
│   │   └── SKILL.md
│   ├── zcode/
│   │   └── Command.md
│   ├── cursor/
│   │   └── SKILL.md
│   ├── reasionix/
│   │   └── script.py
│   └── mcp/
│       └── mcp_server.py
└── manifest.json      # Component metadata
```

**Manifest.json Schema:**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["name", "type", "version", "description"],
  "properties": {
    "name": {
      "type": "string",
      "pattern": "^[a-z][a-z0-9_]*$",
      "description": "Component identifier (snake_case)"
    },
    "type": {
      "type": "string",
      "enum": ["agent", "skill", "tool", "mcp_server"],
      "description": "Component type"
    },
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "description": "Semantic version"
    },
    "description": {
      "type": "string",
      "description": "One-line component description"
    },
    "author": {
      "type": "string",
      "description": "Author name"
    },
    "created": {
      "type": "string",
      "format": "date",
      "description": "Creation date (YYYY-MM-DD)"
    },
    "updated": {
      "type": "string",
      "format": "date",
      "description": "Last update date (YYYY-MM-DD)"
    },
    "tags": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Searchable tags"
    },
    "core_dependencies": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Python package dependencies"
    },
    "supported_tools": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["claude", "zcode", "cursor", "reasionix", "mcp"]
      },
      "description": "Target tools this component supports"
    },
    "config_schema": {
      "type": "object",
      "description": "JSON Schema for component configuration"
    },
    "format_overrides": {
      "type": "object",
      "description": "Per-tool format customizations",
      "properties": {
        "claude": { "type": "object" },
        "zcode": { "type": "object" },
        "cursor": { "type": "object" },
        "reasionix": { "type": "object" },
        "mcp": { "type": "object" }
      }
    },
    "mcp_config": {
      "type": "object",
      "description": "MCP server configuration",
      "properties": {
        "transport": {
          "type": "string",
          "enum": ["stdio", "sse"],
          "default": "stdio"
        },
        "tools": {
          "type": "array",
          "items": { "type": "string" },
          "description": "List of tool function names exposed via MCP"
        }
      }
    }
  }
}
```

### 4. Migration Tools (`migration/`)

**Purpose:** Automate the conversion and deployment process.

**Generator Base Interface:**
```python
# migration/generators/base.py

class FormatGenerator(ABC):
    """格式生成器基类"""

    tool_name: str  # e.g., "claude", "zcode"

    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
        self._templates: Dict[str, str] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """加载格式模板"""
        for template_file in self.template_dir.glob("*.template"):
            self._templates[template_file.stem] = template_file.read_text(encoding="utf-8")

    @abstractmethod
    def generate(self, component: CoreComponent, manifest: Dict) -> Dict[str, str]:
        """
        生成工具特定格式

        Args:
            component: 核心组件实例
            manifest: manifest.json 内容

        Returns:
            Dict[str, str]: {相对路径: 文件内容} 的映射
        """
        pass

    def _render_template(self, template_name: str, variables: Dict[str, Any]) -> str:
        """渲染模板（简单的 {{var}} 替换）"""
        template = self._templates.get(template_name, "")
        for key, value in variables.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))
        return template
```

**Validator Base Interface:**
```python
# migration/validators/base.py

@dataclass
class ValidationResult:
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class FormatValidator(ABC):
    """格式验证器基类"""

    tool_name: str

    @abstractmethod
    def validate(self, generated_files: Dict[str, str], manifest: Dict) -> ValidationResult:
        """
        验证生成的格式文件

        Args:
            generated_files: 生成的文件内容映射
            manifest: manifest.json 内容

        Returns:
            ValidationResult: 验证结果
        """
        pass
```

**Exporter Interface:**
```python
# migration/exporter.py

class ComponentExporter:
    """统一导出工具"""

    def __init__(self, generators: Dict[str, FormatGenerator],
                 validators: Dict[str, FormatValidator]):
        self.generators = generators
        self.validators = validators

    def export(self, component: CoreComponent, manifest: Dict,
               target_tools: List[str], output_dir: Path) -> Dict[str, ValidationResult]:
        """
        导出组件到指定工具格式

        Args:
            component: 核心组件
            manifest: manifest.json
            target_tools: 目标工具列表
            output_dir: 输出目录

        Returns:
            Dict[str, ValidationResult]: 每个工具的验证结果
        """
        results = {}
        for tool in target_tools:
            if tool not in self.generators:
                results[tool] = ValidationResult(
                    valid=False,
                    errors=[f"Unsupported tool: {tool}"]
                )
                continue

            # 生成格式
            generator = self.generators[tool]
            generated = generator.generate(component, manifest)

            # 写入文件
            tool_dir = output_dir / "formats" / tool
            tool_dir.mkdir(parents=True, exist_ok=True)
            for rel_path, content in generated.items():
                file_path = tool_dir / rel_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content, encoding="utf-8")

            # 验证
            if tool in self.validators:
                results[tool] = self.validators[tool].validate(generated, manifest)
            else:
                results[tool] = ValidationResult(valid=True)

        return results
```

## CLI Design

### Command Structure

```
agents-dev <command> [options]

Commands:
  create <type> <name>        创建新组件 (agent|skill|tool|mcp_server)
  generate <name> [tools...]  为组件生成指定工具的格式
  export <name> [tools...]    导出组件到指定工具格式（生成+验证+输出）
  validate <name> [tools...]  验证组件的格式适配
  list [type]                 列出所有组件（可按类型过滤）
  info <name>                 显示组件详细信息
  init <tool> [path]          初始化目标工具项目（使用模板）
```

### Command Details

**`create` - 创建新组件:**
```bash
# 交互式创建
agents-dev create skill data_analysis

# 带选项创建
agents-dev create skill data_analysis \
  --description "Data analysis skill" \
  --tools claude,zcode,mcp \
  --tags "data,analysis"

# 输出: 创建 components/data_analysis/ 目录结构
```

**`generate` - 生成格式:**
```bash
# 为所有支持的工具生成
agents-dev generate data_analysis

# 只生成指定工具的格式
agents-dev generate data_analysis claude mcp

# 输出: 在 components/data_analysis/formats/ 下生成对应格式文件
```

**`export` - 导出组件:**
```bash
# 导出并验证
agents-dev export data_analysis claude

# 导出到指定目录
agents-dev export data_analysis claude --output /path/to/claude/project

# 导出所有支持的工具
agents-dev export data_analysis --all
```

**`validate` - 验证格式:**
```bash
# 验证所有已生成的格式
agents-dev validate data_analysis

# 验证指定工具
agents-dev validate data_analysis claude mcp
```

**`list` - 列出组件:**
```bash
# 列出所有
agents-dev list

# 按类型过滤
agents-dev list skill
agents-dev list agent
```

**`init` - 初始化项目:**
```bash
# 初始化Claude项目
agents-dev init claude /path/to/my-claude-project

# 初始化通用项目
agents-dev init universal /path/to/my-project
```

## Error Handling Strategy

### Error Hierarchy

```python
# core/shared/errors.py

class AgentsDevelopError(Exception):
    """Base error for all agents_develop errors"""
    pass

class ComponentError(AgentsDevelopError):
    """Component-related errors"""
    pass

class ComponentNotFoundError(ComponentError):
    """Component not found in registry"""
    pass

class DuplicateComponentError(ComponentError):
    """Component already exists"""
    pass

class ComponentValidationError(ComponentError):
    """Component input/output validation failed"""
    pass

class MigrationError(AgentsDevelopError):
    """Migration-related errors"""
    pass

class FormatGenerationError(MigrationError):
    """Format generation failed"""
    pass

class FormatValidationError(MigrationError):
    """Format validation failed"""
    pass

class UnsupportedToolError(MigrationError):
    """Target tool not supported"""
    pass

class TemplateError(MigrationError):
    """Template rendering error"""
    pass

class ConfigError(AgentsDevelopError):
    """Configuration errors"""
    pass
```

### Error Handling Principles

1. **Fail Fast**: Validate inputs early, raise descriptive errors immediately
2. **Graceful Degradation**: If one tool format fails, continue with others and report all errors
3. **Actionable Messages**: Error messages include what went wrong, why, and how to fix it
4. **Structured Results**: Validation results separate errors (must fix) from warnings (should fix)

### Export Error Handling Flow

```
export component → for each target_tool:
  ├── generator not found → skip, record UnsupportedToolError
  ├── generation fails → skip, record FormatGenerationError
  ├── write fails → abort this tool, record IOError
  ├── validation fails → record errors/warnings in ValidationResult
  └── success → record ValidationResult(valid=True)

Final: Report all results, exit code = 0 if all valid, 1 if any errors
```

## Dependency Management

### Python Dependencies

```toml
# pyproject.toml

[project]
name = "agents-develop"
version = "0.1.0"
description = "Multi-tool agent/skill development environment"
requires-python = ">=3.10"
dependencies = [
    "jinja2>=3.1",          # Template rendering
    "jsonschema>=4.0",      # JSON Schema validation
    "pydantic>=2.0",        # Data validation
    "rich>=13.0",           # CLI output formatting
    "click>=8.0",           # CLI framework
]

[project.optional-dependencies]
mcp = [
    "mcp>=0.9",             # MCP SDK
]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "ruff>=0.1",            # Linter/formatter
]

[project.scripts]
agents-dev = "cli.main:main"

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### Component Dependencies

Each component declares its Python dependencies in `manifest.json` under `core_dependencies`. These are:
- **Not** automatically installed by the framework
- Validated during export (warn if dependencies are missing)
- Listed in generated format files for user reference

## Tool-Specific Format Specifications

### Claude Code/Desktop Format

**SKILL.md Structure:**
```markdown
---
name: {{name}}
description: {{description}}
version: {{version}}
---

# {{name}}

{{description}}

## When to Use
{{instructions}}

## Instructions
{{checklist}}

## Examples
{{examples}}
```

**Plugin Config (plugin_config.json):**
```json
{
  "name": "{{name}}",
  "version": "{{version}}",
  "description": "{{description}}",
  "type": "{{type}}",
  "skills": ["{{name}}"],
  "mcpServers": {{mcp_config}}
}
```

**Key Features:**
- Rich skill definitions with frontmatter metadata
- Plugin architecture with MCP server integration
- Slash commands for quick invocation
- Skill composition and chaining

**Migration Requirements:**
- Skill metadata must include frontmatter
- MCP server configs must follow Claude's format
- Slash commands need separate definition files

### ZCode Format

**Command.md Structure:**
```markdown
# {{name}}

{{description}}

## Usage

\```
/{{name}} [arguments]
\```

## Instructions
{{instructions}}

## Checklist
{{checklist}}

## Examples
{{examples}}
```

**Command Config (command_config.json):**
```json
{
  "name": "{{name}}",
  "description": "{{description}}",
  "type": "command",
  "arguments": {{config_schema}},
  "dependencies": {{core_dependencies}}
}
```

**Key Features:**
- Simple command definitions
- File-based configuration
- Direct argument mapping

**Migration Requirements:**
- Convert skill instructions to command format
- Map config schema to command arguments
- Simplify complex skill features to command-level

### Cursor Format

**SKILL.md Structure:** (Similar to Claude with Cursor-specific additions)
```markdown
---
name: {{name}}
description: {{description}}
version: {{version}}
cursorVersion: ">=0.40"
---

# {{name}}

{{description}}

## Instructions
{{instructions}}

## Tools
{{tools}}

## Examples
{{examples}}
```

**Cursor Config (cursor_config.json):**
```json
{
  "skills": ["{{name}}"],
  "mcpServers": {{mcp_config}},
  "cursorRules": {
    "include": ["{{name}}"]
  }
}
```

**Key Features:**
- Claude-compatible SKILL.md format
- MCP integration (same protocol as Claude)
- Cursor-specific rules configuration

**Migration Requirements:**
- Nearly identical to Claude format
- Add cursorVersion to frontmatter
- Include cursor-specific config fields

### Reasionix Format

**Script Template:**
```python
#!/usr/bin/env python3
\"\"\"{{name}} - {{description}}

Optimized for Deepseek model.
\"\"\"

# === Component: {{name}} v{{version}} ===
# Generated from agents_develop core implementation

{{instructions_as_python_comments}}

def execute(**kwargs):
    \"\"\"Main execution function\"\"\"
    # {{core_logic}}
    pass

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="{{description}}")
    {{argument_parsing}}
    args = parser.parse_args()
    result = execute(**vars(args))
    print(result)
```

**Deepseek Config:**
```json
{
  "name": "{{name}}",
  "type": "script",
  "model": "deepseek",
  "optimizations": {
    "chunked_prompts": true,
    "max_context_tokens": 32000,
    "temperature": 0.1
  },
  "dependencies": {{core_dependencies}}
}
```

**Key Features:**
- Script-based approach (standalone Python scripts)
- Deepseek model optimizations (chunked prompts, low temperature)
- CLI-friendly with argparse

**Migration Requirements:**
- Convert skill instructions to Python comments/docstrings
- Wrap core logic in executable script
- Add Deepseek-specific optimizations
- Generate argparse-based CLI

### MCP (Universal) Format

**MCP Server Template:**
```python
#!/usr/bin/env python3
\"\"\"MCP Server: {{name}} - {{description}}\"\"\"

from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("{{name}}")

{{tool_definitions}}

{{tool_handlers}}

async def main():
    async with server.run() as runner:
        await runner.wait()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

**MCP Config:**
```json
{
  "mcpServers": {
    "{{name}}": {
      "command": "python",
      "args": ["path/to/{{name}}_server.py"],
      "transport": "{{mcp_transport}}"
    }
  }
}
```

**Key Features:**
- Universal protocol supported by all tools
- Tool definitions follow MCP specification
- stdio transport (most compatible)

**Migration Requirements:**
- Convert tool functions to MCP tool definitions
- Implement MCP tool handlers
- Generate server entry point
- Create configuration snippet for tool integration

## Workflow

### Development Workflow

1. **Create Core Component:**
   ```bash
   agents-dev create skill data_analysis
   ```
   - Creates directory structure in `components/data_analysis/`
   - Generates `manifest.json` with metadata
   - Creates skeleton core implementation
   - Developer implements core logic

2. **Implement Core Logic:**
   - Write core implementation in `components/data_analysis/core/`
   - Inherit from appropriate base class (`SkillBase`, `AgentBase`, etc.)
   - Implement required abstract methods
   - Write unit tests

3. **Generate Format Adaptations:**
   ```bash
   agents-dev generate data_analysis
   ```
   - Run migration generators
   - Review generated formats
   - Customize if needed (edit generated files directly)

4. **Test Component:**
   ```bash
   agents-dev validate data_analysis
   pytest tests/
   ```
   - Test core implementation
   - Test format adaptations
   - Run integration tests

5. **Export to Target Tool:**
   ```bash
   agents-dev export data_analysis claude --output /path/to/claude/project
   ```
   - Select target tools
   - Generate deployment package
   - Validate output
   - Deploy to target environment

### Migration Workflow

1. **Select Component:**
   ```bash
   agents-dev list
   agents-dev info data_analysis
   ```

2. **Configure Export:**
   - Select target tools
   - Set export parameters
   - Choose export format

3. **Generate Export:**
   ```bash
   agents-dev export data_analysis claude zcode mcp
   ```

4. **Deploy:**
   - Copy generated files to target project
   - Configure in target tool
   - Test in target environment

## Testing Strategy

### Core Testing
- **Unit tests** for all core components (base classes, registry, shared utils)
- **Contract tests** verifying interface compliance for each component type
- **Mock tool-specific interfaces** to ensure core is tool-agnostic
- **Tools:** pytest, pytest-cov

### Format Testing
- **Template rendering tests** - verify templates render with valid variables
- **Generator tests** - test each generator with sample components
- **Validator tests** - test validators with valid and invalid formats
- **Round-trip tests** - generate → validate → verify structure

### Migration Testing
- **Export tests** - test export to each supported tool
- **Deployment package tests** - verify generated packages are complete
- **Error scenario tests** - test graceful handling of failures
- **Cross-tool consistency tests** - verify same core produces consistent behavior across tools

### Integration Testing
- **End-to-end workflow** - create → generate → validate → export
- **Multi-tool deployment** - export same component to multiple tools
- **Regression testing** - ensure changes don't break existing components
- **CLI integration** - test all CLI commands

### Test Coverage Targets
| Layer | Target Coverage |
|-------|----------------|
| core/shared | ≥ 90% |
| core/agents, skills, tools | ≥ 80% |
| migration/generators | ≥ 85% |
| migration/validators | ≥ 90% |
| cli | ≥ 70% |
| integration | Key workflows covered |

## Implementation Phases

### Phase 1: Core Foundation (Priority: Critical)

**Goal:** Establish the base classes, registry, and shared utilities.

**Deliverables:**
- [ ] `core/shared/` - Base classes, errors, config, logging, utils
- [ ] `core/agents/base.py` - AgentBase with system_prompt, plan, reflect
- [ ] `core/skills/base.py` - SkillBase with instructions, checklist, examples
- [ ] `core/tools/base.py` - ToolBase with function_definitions, run
- [ ] `core/mcp_base/` - MCPServerBase, tool definition helpers
- [ ] `core/shared/registry.py` - ComponentRegistry singleton
- [ ] `pyproject.toml` - Project configuration with dependencies
- [ ] `tests/core/` - Unit tests for all core components
- [ ] `CLAUDE.md` / `GEMINI.md` - Tool-specific instructions

**Exit Criteria:**
- All base classes are importable and tested
- Registry can register/retrieve components
- Error hierarchy is complete
- `pytest tests/core/` passes with ≥ 90% coverage

### Phase 2: Format Templates & Generators (Priority: High)

**Goal:** Create format templates and generators for all supported tools.

**Deliverables:**
- [ ] `formats/claude/` - SKILL.md template, plugin config template
- [ ] `formats/zcode/` - Command.md template, command config template
- [ ] `formats/cursor/` - SKILL.md template, cursor config template
- [ ] `formats/reasionix/` - Script template, deepseek config template
- [ ] `formats/mcp/` - MCP server template, config template
- [ ] `migration/generators/base.py` - FormatGenerator base class
- [ ] `migration/generators/claude_generator.py`
- [ ] `migration/generators/zcode_generator.py`
- [ ] `migration/generators/cursor_generator.py`
- [ ] `migration/generators/reasionix_generator.py`
- [ ] `migration/generators/mcp_generator.py`
- [ ] `tests/formats/` - Template rendering tests
- [ ] `tests/migration/test_generators.py`

**Exit Criteria:**
- All 5 generators can produce valid output from a sample component
- Templates render correctly with all variable substitutions
- `pytest tests/formats/ tests/migration/` passes

### Phase 3: Validators & Exporter (Priority: High)

**Goal:** Implement format validators and the unified exporter.

**Deliverables:**
- [ ] `migration/validators/base.py` - FormatValidator base class
- [ ] `migration/validators/claude_validator.py`
- [ ] `migration/validators/zcode_validator.py`
- [ ] `migration/validators/cursor_validator.py`
- [ ] `migration/validators/mcp_validator.py`
- [ ] `migration/exporter.py` - ComponentExporter
- [ ] `tests/migration/test_validators.py`
- [ ] `tests/migration/test_exporter.py`

**Exit Criteria:**
- Validators catch invalid format output
- Exporter can export a component to all 5 tools
- Export handles errors gracefully (partial success)
- `pytest tests/migration/` passes

### Phase 4: CLI & Integration (Priority: Medium)

**Goal:** Build the command-line interface and end-to-end integration.

**Deliverables:**
- [ ] `cli/main.py` - CLI entry point with Click
- [ ] `cli/create_cmd.py` - create command
- [ ] `cli/generate_cmd.py` - generate command
- [ ] `cli/export_cmd.py` - export command
- [ ] `cli/validate_cmd.py` - validate command
- [ ] `cli/list_cmd.py` - list command
- [ ] `components/_example/` - Example component for reference
- [ ] `tests/integration/` - End-to-end workflow tests
- [ ] `docs/` - User documentation

**Exit Criteria:**
- All CLI commands work as specified
- End-to-end workflow (create → generate → validate → export) works
- Example component demonstrates the full workflow
- Documentation is complete

### Phase 5: Polish & Advanced Features (Priority: Low)

**Goal:** Refine the experience and add advanced features.

**Deliverables:**
- [ ] `templates/` - Project templates for each tool
- [ ] `cli/init_cmd.py` - init command for project scaffolding
- [ ] Component dependency resolution
- [ ] Version compatibility checking
- [ ] Interactive component creation (with prompts)
- [ ] Component search/filter improvements
- [ ] Performance optimization

**Exit Criteria:**
- Project templates are usable
- Advanced features work correctly
- Full test suite passes
- Documentation is up to date

## Migration from Previous Codebase

The previous codebase (commit `47dcf3b` and earlier) contained a Chinese-mythology-themed agent/skill system. Key salvageable components:

| Previous Component | Salvageable? | Notes |
|---|---|---|
| `skills/tool_wanglingguan/` (security scanner, semantic analyzer) | ✅ Yes | Core logic is tool-agnostic, can be wrapped in new SkillBase |
| `skills/tool_bajiu/` (multi-provider LLM routing) | ✅ Yes | LLM client logic is reusable |
| `skills/tool_taibai/` (GSSC pipeline) | ✅ Yes | Pipeline logic is tool-agnostic |
| `mcp-servers/*.py` | ⚠️ Partial | Need refactoring to new MCPServerBase |
| `src/agents_develop/` (orchestrator, CLI) | ❌ No | Architecture is fundamentally different |
| `agents/*.md` (persona definitions) | ⚠️ Partial | Persona concepts can be adapted, format must change |
| `a2a_inbox/` (review tickets) | ❌ No | Protocol-specific, not portable |

**Migration Approach:**
1. Extract core logic from previous skills into new `SkillBase` subclasses
2. Wrap previous MCP servers with new `MCPServerBase`
3. Discard tool-specific orchestration (replaced by new architecture)
4. Preserve domain knowledge (security scanning, LLM routing, etc.)

## Concrete Example Walkthrough

### Creating a "Code Security Scanner" Skill

**Step 1: Create the component**
```bash
agents-dev create skill code_security_scanner \
  --description "Scans code for security vulnerabilities" \
  --tools claude,zcode,mcp \
  --tags "security,scanning,code-review"
```

This creates:
```
components/code_security_scanner/
├── core/
│   ├── __init__.py
│   └── code_security_scanner.py    # Skeleton with SkillBase
├── formats/                         # Empty, to be generated
└── manifest.json                    # Pre-filled metadata
```

**Step 2: Implement core logic**

```python
# components/code_security_scanner/core/code_security_scanner.py

from core.skills.base import SkillBase, ComponentMetadata, ComponentType

class CodeSecurityScanner(SkillBase):
    """Scans code for security vulnerabilities"""

    def __init__(self):
        metadata = ComponentMetadata(
            name="code_security_scanner",
            type=ComponentType.SKILL,
            version="1.0.0",
            description="Scans code for security vulnerabilities",
            tags=["security", "scanning", "code-review"],
            core_dependencies=["pathlib", "re"],
            supported_tools=["claude", "zcode", "mcp"],
        )
        super().__init__(metadata)

    @property
    def instructions(self) -> str:
        return """Scan the provided code for security vulnerabilities including:
1. SQL injection risks
2. XSS vulnerabilities
3. Hardcoded secrets/credentials
4. Insecure file operations
5. Command injection risks
Report each finding with severity, location, and remediation advice."""

    def get_checklist(self) -> list[str]:
        return [
            "Check for SQL string concatenation",
            "Check for unescaped user input in HTML",
            "Check for hardcoded passwords/API keys",
            "Check for os.system/subprocess with user input",
            "Check for insecure file path handling",
        ]

    def execute(self, input_data: dict) -> dict:
        code = input_data.get("code", "")
        language = input_data.get("language", "python")
        findings = self._scan(code, language)
        return {"findings": findings, "count": len(findings)}

    def validate_input(self, input_data: dict) -> bool:
        return "code" in input_data

    def _scan(self, code: str, language: str) -> list:
        # Core scanning logic (tool-agnostic)
        findings = []
        # ... implementation ...
        return findings
```

**Step 3: Generate formats**
```bash
agents-dev generate code_security_scanner
```

This produces:
- `formats/claude/SKILL.md` - Claude skill definition
- `formats/zcode/Command.md` - ZCode command definition
- `formats/mcp/mcp_server.py` - MCP server with scan tool

**Step 4: Validate**
```bash
agents-dev validate code_security_scanner
```

**Step 5: Export to Claude project**
```bash
agents-dev export code_security_scanner claude --output ~/my-claude-project/.claude/skills/
```

## Success Criteria

1. **Unified Development:**
   - Single source of truth for component logic
   - Clear separation between core and formats
   - Easy to develop new components

2. **Automated Migration:**
   - One-command export to target tools
   - Validated output generation
   - Support for all 5 target tools

3. **Maintainability:**
   - Clear directory structure
   - Comprehensive documentation
   - Automated testing with ≥ 80% coverage

4. **Extensibility:**
   - Easy to add new tool support (just add a generator + validator)
   - Simple to create new components (inherit base class)
   - Flexible migration options

5. **Developer Experience:**
   - Intuitive CLI interface
   - Clear error messages
   - Example components for reference
   - Complete documentation

## Future Considerations

1. **Additional Tool Support:**
   - Easy to add new tools by creating new generators
   - Format specifications can be extended
   - Community contribution workflow

2. **Enhanced Migration:**
   - Automatic dependency management (pip install from manifest)
   - Version compatibility checking
   - Conflict resolution for existing files

3. **Component Discovery:**
   - Component registry/search
   - Usage analytics
   - Community sharing

4. **Development Tools:**
   - Component scaffolding with interactive prompts
   - Visual component editor
   - Live preview of generated formats
   - Hot-reload during development

5. **Advanced Features:**
   - Component composition (skill A uses skill B)
   - Cross-component dependency resolution
   - Automated testing in target tool environments
   - CI/CD integration for component validation

## References

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Cursor AI Documentation](https://cursor.sh/)
- [DeepSeek Platform](https://platform.deepseek.com/)
- [MCP Servers Repository](https://github.com/modelcontextprotocol/servers)
- [Click CLI Framework](https://click.palletsprojects.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [JSON Schema Specification](https://json-schema.org/)
