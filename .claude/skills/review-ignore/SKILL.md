---
name: review-ignore
description: >
  【强制触发】任何时候用户说"忽略"（包括"忽略第N个"、"忽略这两项"、"不用管这个"、"跳过"、
  "不用再提了"、"我知道了"、"skip"、"ignore"），只要上下文是 review 结果或代码审查，
  必须立即触发此技能，不得自行口头处理。自行重新列举审查结果但不写入 JSON 文件是错误行为。
  同时覆盖 review 开始前的忽略列表加载、review 后的交互式忽略、prompt 中的临时忽略条件、
  以及忽略列表的查看/删除/清空操作。
---

# Review Ignore Memory

## 关键行为规范（违反此规范是 Bug）

**当用户说"忽略"时，你的第一动作必须是调用工具写入 `.claude/review-ignores.json`，而不是口头重新列举审查结果。**

错误行为 ❌：
- 收到"忽略第8、第11两项"后，直接输出一份去掉第8和第11项的新报告
- 口头说"好的，已忽略"但没有写入文件
- 重新排列问题编号但没有持久化

正确行为 ✅：
1. 先确认用户要忽略的具体问题（提取 issue_type、file、line、description）
2. 询问忽略粒度（精确/文件级/全局）和原因
3. 读取现有 `.claude/review-ignores.json` → 追加新项 → 写回文件
4. 然后再输出过滤后的结果

---

## 概念

每次 review 都会产生一些用户认为不重要或已经知晓的问题。这些问题如果在后续 review 中重复出现，
会稀释 review 的价值、浪费注意力、让用户对 review 结果脱敏。

本技能维护一个持久化的忽略列表（`.claude/review-ignores.json`），在每次 review 开始前读取，
确保已被忽略的问题不再出现在 review 输出中。

## 忽略列表文件

位置：`<项目根目录>/.claude/review-ignores.json`

如果文件不存在，视为没有任何忽略项（空列表）。

### JSON 结构

```json
[
  {
    "id": "a1b2c3",
    "issue_type": "type_hint",
    "file": "src/auth.py",
    "line": null,
    "description": "auth.py 中的 type hint 缺失",
    "reason": "项目不强制此文件的 type hint",
    "created_at": "2026-06-04T10:00:00Z"
  }
]
```

### 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | 是 | 6位随机 hex，用于标识和删除 |
| `issue_type` | 否 | 问题类型，如 `type_hint`、`unused_import`、`naming`、`security` 等。null 表示匹配任意类型 |
| `file` | 否 | 文件路径（相对于项目根目录）。null 表示全局生效 |
| `line` | 否 | 具体行号。null 表示整个文件 |
| `description` | 是 | 人类可读的描述，帮助用户回忆这条规则是什么 |
| `reason` | 否 | 忽略的原因 |
| `created_at` | 是 | ISO 8601 格式的时间戳 |

### 匹配逻辑（从高到低优先级）

1. `issue_type` + `file` + `line` 全部匹配 → 精确命中某一行的某个问题
2. `issue_type` + `file`（line=null）→ 忽略某文件的某类问题
3. `file` + `line`（issue_type=null）→ 忽略某行的所有问题
4. `issue_type`（file=null, line=null）→ 全局忽略某类问题
5. `file`（issue_type=null, line=null）→ 忽略某文件的所有问题

---

## 工作流程

### 流程一：执行 Review

当用户要求进行任何类型的 review 时，**在开始 review 之前**，按以下步骤执行：

**Step 1 — 加载忽略列表**

```
读取 <project-root>/.claude/review-ignores.json
如果文件不存在，使用空列表 []，不要报错
```

**Step 2 — 过滤**

在整个 review 过程中，对照忽略列表逐条检查。如果发现的问题命中了任何一条忽略规则，直接跳过，不要出现在输出中。

匹配时注意：
- `file` 字段使用相对于项目根目录的路径，对比时要标准化路径（统一 `/` 和 `\`）
- `issue_type` 使用模糊匹配：忽略项的类型应被包含在问题描述中（例如 `type_hint` 匹配 "缺少类型注解"、"missing type hint" 等）
- 如果不确定某个问题是否命中了忽略规则，**宁可过滤掉**（偏向用户意图）

**Step 3 — 输出**

review 输出末尾附加一段简短提示：

```
> 本次 review 已过滤 N 条已忽略的问题。使用 "/review-ignore list" 查看忽略列表。
```

如果 N = 0，不显示此提示。

### 流程二：Review 后交互式忽略

当 review 完成后，用户说"忽略第 N 个问题"、"第 2 个不用管"、"ignore #3"、"忽略第8、第11两项" 等：

> ⚠️ **绝对禁止**：不得跳过下面的步骤直接输出过滤后的报告。口头确认而不写入文件是错误行为。

**Step 1 — 提取信息**

从用户指向的问题中提取 `issue_type`、`file`、`line`、`description`。如果用户说"忽略第8、第11两项"，需要分别提取这两个问题的信息。

**Step 2 — 确认与粒度选择**

向用户确认要忽略的内容，并询问忽略粒度（精确/文件级/全局）。如果上下文已经很清楚，可以直接使用合理默认值并说明：

**Step 3 — 写入（必须用工具完成，不能口头确认）**

按以下顺序执行，每一步都需要实际的工具调用：

1. **读取**现有文件：`cat .claude/review-ignores.json`（如果文件不存在，从空数组 `[]` 开始）
2. **追加**新条目：为每个忽略项生成 `id`（6位hex），填入字段，追加到数组
3. **写入**文件：使用 Write 工具将完整数组写回 `.claude/review-ignores.json`

**Step 4 — 确认并输出过滤后的报告**

写入成功后，输出：
```
✅ 已添加 N 条忽略规则到 .claude/review-ignores.json
```
然后输出过滤后的 review 结果。

### 流程三：直接在 Prompt 中指定忽略

用户在 review 请求中直接附加忽略条件，例如：
- "review auth.py，但不要报 type hint 的问题"
- "做一次 security review，忽略 SQL injection 相关的警告（我已经用 ORM 了）"
- "review this PR，skip unused imports"

处理方式：
1. 识别这些忽略条件，将它们视为**临时忽略**（不写入 JSON 文件）
2. 在本次 review 中过滤这些问题
3. 在输出末尾提示：
```
> 本次临时忽略了 N 条问题。如需永久忽略，使用 "忽略第 N 个问题" 将其加入持久化列表。
```

### 流程四：管理忽略列表

#### 查看列表
用户说 "review-ignore list" / "查看忽略列表" / "show ignores"：

读取 JSON 文件，格式化输出：

```
当前忽略列表（共 N 条）：
┌────┬──────────┬──────────────┬──────┬──────────────────────────────┐
│ ID │ 类型     │ 文件         │ 行号 │ 描述                         │
├────┼──────────┼──────────────┼──────┼──────────────────────────────┤
│ a1 │ type_hint│ src/auth.py  │ -    │ auth.py type hint 缺失       │
│ b2 │ *        │ tests/       │ -    │ tests 目录忽略所有问题        │
└────┴──────────┴──────────────┴──────┴──────────────────────────────┘
```

#### 删除条目
用户说 "删除忽略 a1b2c3" / "remove ignore a1b2c3" / "取消忽略第 3 条"：

按 `id` 查找并删除，确认后写回文件。

#### 清空
用户说 "清空忽略列表" / "clear all ignores"：

**需要二次确认**：列出将被删除的所有条目，确认后再清空。

---

## 完整示例

### 场景：review 完成后用户说"忽略第8、第11两项"

**正确的执行序列：**

```
用户：忽略第8、第11两项

Assistant（内部）：
1. 识别第8项：issue_type=sys_path, file=code_modification.py, line=5, description="sys.path 操控脆弱"
   识别第11项：issue_type=routing, file=route_orchestrator.py, line=53, description="Routing Priority 与 Skill 重复"

2. 读取 .claude/review-ignores.json → 文件不存在，从 [] 开始

3. 追加两项：
   [
     {"id":"f3a1b2","issue_type":"sys_path","file":"src/agents_develop/tools/code_modification.py","line":null,
      "description":"sys.path 操控脆弱，对安装方式敏感","reason":"","created_at":"2026-06-04T..."},
     {"id":"c4d5e6","issue_type":"routing","file":"skills/tool_bajiu/scripts/route_orchestrator.py","line":53,
      "description":"LLM 阈值下调可能导致误路由","reason":"","created_at":"2026-06-04T..."}
   ]

4. 使用 Write 工具写入 .claude/review-ignores.json

Assistant（输出）：
✅ 已添加 2 条忽略规则到 .claude/review-ignores.json
  • f3a1b2: sys.path 操控脆弱（全局忽略）
  • c4d5e6: LLM 阈值下调需谨慎（route_orchestrator.py:53）

以下是过滤后的审查报告（原第8、第11项已过滤）：
...（过滤后的报告）
```

---

## 注意事项

1. **文件不存在 = 空列表**。永远不要因为文件不存在而报错或中断 review 流程。
2. **并发安全**：写入时先读再写，不要覆盖其他进程的改动。如果可能，使用文件锁或者追加方式。
3. **路径标准化**：比较文件路径时，统一使用 `/` 分隔符，并去除开头的 `./`。
4. **issue_type 模糊匹配**：不需要精确字符串匹配，只要语义相关就应命中。例如忽略项是 `type_hint`，review 发现 "缺少类型注解" 也应该被过滤。
5. **不要修改 review 的结论**。忽略只是不展示，不是"假装通过"。如果有严重问题被忽略了，review 总结中不需要提及（因为已经过滤了）。
