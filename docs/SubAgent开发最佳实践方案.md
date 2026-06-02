# SubAgent 子代理开发最佳实践方案

> 版本：v1.0 | 日期：2026-06-02  
> 来源：Anthropic、LangGraph、CrewAI、AutoGen、OpenAI Agents SDK、Google ADK 等开源项目及技术社区

---

## 1. 架构模式总览

### 1.1 五大核心编排模式

| 模式 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| **Orchestrator-Worker（编排器-工人）** | 复杂任务动态分解，如多文件代码修改、多源搜索 | 灵活、可动态决定子任务 | 编排器成本高、单点故障 |
| **Sequential Pipeline（顺序流水线）** | 固定步骤工作流，如研究→写作→审校 | 简单可预测、易调试 | 延迟为各步骤之和 |
| **Parallel Fan-out（并行扇出）** | 独立子任务同时执行，如多维度审查、投票 | 低延迟、多视角 | 需聚合逻辑、结果一致性难保证 |
| **Hierarchical（多级层级）** | 大型复杂系统，子代理可生成自己的子代理 | 可无限扩展 | 调试困难、上下文丢失风险 |
| **Swarm / Peer-to-Peer（对等协作）** | 动态 handoff，如客服路由、多角色对话 | 灵活、无中心瓶颈 | 死循环风险、需明确终止条件 |

> **Anthropic 最佳实践**：从最简单的方案开始，只有在能证明带来改进时才增加复杂度。很多时候甚至不需要构建代理系统。

### 1.2 模式选择决策树

```
任务是否可分解为固定步骤？
├── 是 → Sequential Pipeline
└── 否 → 子任务是否独立可并行？
    ├── 是 → Parallel Fan-out
    └── 否 → 是否需要动态路由？
        ├── 是 → Orchestrator-Worker
        └── 否 → 是否需要多级管理？
            ├── 是 → Hierarchical
            └── 否 → Swarm / Handoff
```

---

## 2. SubAgent 设计原则

### 2.1 单一职责原则（Single Responsibility）

每个 SubAgent 只负责一个明确的领域。

```python
# ✓ 正确：职责单一
research_agent = Agent(
    role="Research Analyst",
    goal="Gather and synthesize factual information",
    tools=[web_search, database_query],
    # 没有写作、没有计算
)

# ✗ 错误：职责混杂
do_everything_agent = Agent(
    role="General Assistant",
    goal="Research, write, calculate, and deploy",
    tools=[web_search, code_exec, write_doc, deploy],
)
```

**原则**：如果一个 Agent 的 goal 描述中包含"和"字，通常意味着需要拆分。

### 2.2 接口契约设计（Input/Output Schema）

所有 SubAgent 必须定义明确的输入输出格式：

```python
from pydantic import BaseModel

class ResearchInput(BaseModel):
    query: str
    max_sources: int = 5
    language: str = "en"

class ResearchOutput(BaseModel):
    summary: str
    sources: list[str]
    confidence: float  # 0.0-1.0

research_agent = Agent(
    role="Research Analyst",
    input_schema=ResearchInput,
    output_schema=ResearchOutput,
    ...
)
```

**好处**：
- 编排器可程序化验证 SubAgent 输出
- 避免自由文本解析错误
- 支持类型安全的链式调用

### 2.3 工具设计规范（Agent-Computer Interface）

> Anthropic 研究表明：在 SWE-bench 代理开发中，工具优化的时间比整体 prompt 优化更多。

**工具设计原则**：

| 原则 | 说明 |
|------|------|
| **防错设计（Poka-yoke）** | 重新设计参数让错误更难发生（如要求绝对路径而非相对路径） |
| **贴近训练分布** | 工具输出格式尽量接近模型在训练数据中见过的格式 |
| **充足上下文** | 工具描述应像给初级开发者的文档：包含用法示例、边界情况、输入格式要求 |
| **最小权限** | 每个 Agent 只赋予完成任务所需的最少工具集 |
| **语义清晰** | 参数名和描述应自解释，避免缩写 |

```python
# ✓ 良好的工具定义
@tool
def search_codebase(
    query: str,        # 搜索关键词，支持正则表达式
    file_pattern: str = "*.py",  # 文件 glob 模式
    max_results: int = 20,       # 返回结果上限
) -> list[SearchResult]:
    """在项目代码库中搜索代码片段。
    
    用法示例：
      search_codebase(query="def authenticate", file_pattern="*.py")
      search_codebase(query="TODO|FIXME", file_pattern="*.{ts,tsx}")
    
    注意：搜索范围限定在项目根目录内，不会搜索 .git 或 node_modules。
    """
```

### 2.4 Context Window 管理

多代理系统中上下文膨胀是首要成本和质量问题：

| 策略 | 说明 |
|------|------|
| **信息压缩** | SubAgent 返回摘要而非原始长文本 |
| **按需传递** | 只传递当前步骤必需的上下文字段 |
| **共享记忆层** | 使用外部存储（Redis/向量数据库）而非消息传递 |
| **滑动窗口** | 保留最近 N 轮 + 关键摘要 |
| **分层记忆** | 工作记忆（当前任务）+ 长期记忆（跨任务） |

```python
# LangGraph 中的子代理上下文传递模式
@tool
def ask_researcher(question: str) -> str:
    """委托研究问题给专家。只传递问题，不传递完整历史。"""
    response = research_agent.invoke(
        {"messages": [{"role": "user", "content": question}]}
    )
    # 只返回最终回答，不返回中间推理过程
    return response["messages"][-1].content
```

---

## 3. 通信与 Handoff 机制

### 3.1 工具调用式 Handoff（推荐）

SubAgent 作为主代理的工具被调用，最简单最可控：

```python
# LangGraph Supervisor 模式
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent

math_agent = create_react_agent(model, tools=[add, multiply], name="math_expert")
research_agent = create_react_agent(model, tools=[web_search], name="research_expert")

workflow = create_supervisor(
    [research_agent, math_agent],
    model=model,
    prompt="For math use math_expert. For research use research_expert."
)
```

### 3.2 自定义 Handoff 协议

需要传递额外上下文（如任务描述、状态）时：

```python
def create_custom_handoff_tool(*, agent_name: str):
    @tool(f"transfer_to_{agent_name}")
    def handoff(
        task_description: Annotated[str, "下一步代理应执行的详细任务描述"],
        state: Annotated[dict, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ):
        return Command(
            goto=agent_name,
            graph=Command.PARENT,
            update={
                "messages": state["messages"] + [ToolMessage(...)],
                "active_agent": agent_name,
                "task_description": task_description,
            },
        )
    return handoff
```

### 3.3 CrewAI 委托模式

```python
# 管理者可委托，专家不可委托（防止循环委托）
manager = Agent(
    role="Project Manager",
    allow_delegation=True,   # 可委托给团队成员
)

specialist = Agent(
    role="Code Reviewer",
    allow_delegation=False,  # 专注本职，不委托
)
```

---

## 4. 错误处理与容错

### 4.1 三层错误处理架构

```
┌─────────────────────────────────────────┐
│  Layer 3: 全局降级（Circuit Breaker）     │
│  连续失败 N 次 → 切换到备用模型/人工接管    │
├─────────────────────────────────────────┤
│  Layer 2: 节点级重试（RetryPolicy）       │
│  可恢复错误 → 指数退避重试                 │
├─────────────────────────────────────────┤
│  Layer 1: 工具级错误反馈                   │
│  ToolError → 将错误信息反馈给 LLM 自我修正  │
└─────────────────────────────────────────┘
```

### 4.2 LangGraph 错误处理实现

```python
from langgraph.types import RetryPolicy, Command

# Layer 1: 工具级 - LLM 自我修正
def execute_tool(state):
    try:
        result = run_tool(state["tool_call"])
        return Command(update={"tool_result": result}, goto="agent")
    except ToolError as e:
        # 让 LLM 看到错误信息并调整策略
        return Command(
            update={"tool_result": f"Tool error: {str(e)}"},
            goto="agent"
        )

# Layer 2: 节点级 - 自动重试
graph.add_node(
    "call_api",
    call_api_fn,
    retry_policy=RetryPolicy(max_attempts=3, retry_on=ConnectionError),
    error_handler=compensation_handler,  # 重试耗尽后执行补偿
)

# Layer 3: 全局 - 降级策略
def fallback_handler(state, error):
    return Command(
        update={"status": f"degraded: {error.error}"},
        goto="fallback_agent"  # 切换到备用代理或人工处理
    )
```

### 4.3 防止常见故障

| 故障类型 | 防护措施 |
|---------|---------|
| **无限循环** | 设置 `max_iterations`、`max_tool_calls` |
| **代理死锁** | Handoff 时检查目标代理是否可达 |
| **上下文溢出** | 监控 token 使用，超限时压缩或截断 |
| **级联失败** | 断路器模式，失败代理不阻塞其他代理 |
| **成本失控** | 每个子任务设 token 预算上限 |

---

## 5. 安全与隔离

### 5.1 沙箱执行

```python
# 代码执行类 SubAgent 必须在沙箱中运行
code_agent = Agent(
    role="Code Executor",
    tools=[sandboxed_code_exec],  # Docker/容器隔离
    max_execution_time=30,        # 超时限制
    allowed_modules=["pandas", "numpy"],  # 白名单
)
```

### 5.2 权限最小化

```python
# 每个 Agent 只赋予必需工具
search_agent = Agent(
    tools=[web_search],          # ✓ 只有搜索能力
    # tools=[web_search, file_write, db_write],  ✗ 不需要写权限
)
```

### 5.3 输入输出验证

```python
# 子代理边界处验证
def validate_agent_output(output, schema):
    """在 SubAgent 输出进入主流程前校验"""
    try:
        return schema.model_validate_json(output)
    except ValidationError as e:
        raise AgentOutputError(f"Agent output validation failed: {e}")
```

---

## 6. 可观测性

### 6.1 分布式追踪

```
[User Request]
  └── [Orchestrator] trace_id=abc123
      ├── [Research Agent] span_id=001 parent=abc123
      │   └── [web_search] span_id=002
      └── [Writer Agent] span_id=003 parent=abc123
          └── [generate_text] span_id=004
```

**关键指标**：

| 指标 | 说明 |
|------|------|
| 端到端延迟 | 用户请求到最终响应 |
| 每个 Agent 延迟 | 识别瓶颈代理 |
| Token 消耗 | 按 Agent/任务/用户统计 |
| Handoff 成功率 | 代理间交接是否顺畅 |
| 工具调用错误率 | 哪些工具最不可靠 |
| 降级触发次数 | 系统健康度 |

### 6.2 可观测性工具栈

```
Agents → OpenTelemetry SDK → Collector
  ├── Traces → Jaeger / Grafana Tempo
  ├── Metrics → Prometheus / Grafana
  └── Logs   → ELK / Loki
```

专用 LLM 可观测平台：**LangSmith**、**Arize Phoenix**、**Braintrust**

---

## 7. 成本控制

### 7.1 模型路由策略

```python
def route_to_model(task_complexity: str):
    """根据任务复杂度路由到不同模型"""
    if task_complexity == "simple":
        return "claude-haiku"      # $0.25/M tokens
    elif task_complexity == "medium":
        return "claude-sonnet"     # $3/M tokens
    else:
        return "claude-opus"       # $15/M tokens
```

### 7.2 Token 预算控制

```python
class TokenBudget:
    def __init__(self, total: int):
        self.total = total
        self.spent = 0
    
    def remaining(self) -> int:
        return max(0, self.total - self.spent)
    
    def check(self, estimated: int):
        if self.spent + estimated > self.total:
            raise BudgetExceeded("Token budget exhausted")
```

### 7.3 并行与缓存

| 策略 | 效果 |
|------|------|
| 子任务并行执行 | 延迟 = 最慢单任务，而非总和 |
| 语义缓存 | 相似查询命中缓存，避免重复调用 |
| Prompt 缓存 | 利用 API 的 prompt caching 降低重复前缀成本 |
| 批处理 | 非实时任务使用 Batch API |

---

## 8. 框架选型指南

| 框架 | 最佳场景 | 核心特点 |
|------|---------|---------|
| **LangGraph** | 复杂有状态工作流 | 图结构、状态管理、持久化、Human-in-the-loop |
| **CrewAI** | 快速原型、角色团队 | 角色/目标/背景故事、Flow 管道、内置委托 |
| **AutoGen** | 对话式多代理、人机协作 | 对话驱动、群聊模式、代码执行 |
| **Claude Agent SDK** | Claude 生态系统 | 原生 MCP 支持、子代理调度、Handoff 工具 |
| **OpenAI Agents SDK** | OpenAI 生态、轻量 Handoff | 原生 handoff、guardrails、tracing |
| **Google ADK** | Google 生态、A2A 协议 | Agent-to-Agent 标准协议、MCP 集成 |

---

## 9. 开发检查清单

### 设计阶段
- [ ] 是否真正需要多代理？单代理+多工具是否足够？
- [ ] 每个 SubAgent 职责是否单一明确？
- [ ] 是否定义了 Input/Output Schema？
- [ ] 是否选择了最简单的编排模式？

### 实现阶段
- [ ] 工具描述是否清晰（像给初级开发者的文档）？
- [ ] 是否实现了错误处理三层架构？
- [ ] 是否设置了 max_iterations / max_tool_calls？
- [ ] SubAgent 是否在沙箱中执行（如涉及代码执行）？
- [ ] 是否只赋予了最小必要工具集？

### 测试阶段
- [ ] 是否单独测试了每个 SubAgent？
- [ ] 是否测试了 Handoff 边界情况？
- [ ] 是否测试了错误场景（超时、工具失败、无效输出）？
- [ ] 是否验证了 Token 预算控制？

### 部署阶段
- [ ] 是否配置了分布式追踪（OpenTelemetry / LangSmith）？
- [ ] 是否设置了成本告警阈值？
- [ ] 是否有降级/人工接管方案？
- [ ] 是否监控了关键指标（延迟、错误率、Token 消耗）？

---

## 参考来源

1. [Anthropic - Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)
2. [LangGraph Supervisor](https://github.com/langchain-ai/langgraph-supervisor-py)
3. [LangGraph Documentation - Subgraphs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs)
4. [LangGraph Documentation - Fault Tolerance](https://docs.langchain.com/oss/python/langgraph/fault-tolerance)
5. [CrewAI Documentation](https://github.com/crewaiinc/crewai)
6. [CrewAI Collaboration Patterns](https://github.com/crewaiinc/crewai/blob/main/docs/en/concepts/collaboration.mdx)
7. [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/)
8. [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)
9. [Microsoft AutoGen](https://microsoft.github.io/autogen/)
10. [A2A Protocol by Google](https://github.com/google/A2A)
