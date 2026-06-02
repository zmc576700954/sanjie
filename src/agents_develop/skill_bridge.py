"""Agent-Skill bridge — connects SubAgents to their corresponding Skills.

Per SPEC.md section 4: L1 runtime scans agents/*.md for Capability Registry
and routes to matching Skills. This module provides the programmatic bridge
so the Orchestrator can discover and invoke Skills from SubAgent context.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


@dataclass
class SkillProfile:
    """Profile of a registered skill for routing decisions."""
    name: str
    description: str
    trigger_keywords: list[str]
    negative_keywords: list[str]
    tools: list[str]
    module_path: str


@dataclass
class SkillRegistry:
    """Registry of available skills for agent-skill bridge.

    Provides discoverability so the Orchestrator and agents can
    find the right skill for a given task context.
    """
    skills: dict[str, SkillProfile] = field(default_factory=dict)

    def register(self, profile: SkillProfile):
        self.skills[profile.name] = profile

    def find_by_keyword(self, text: str) -> list[SkillProfile]:
        """Find skills matching keywords in the task text."""
        text_lower = text.lower()
        matches = []
        for skill in self.skills.values():
            # Check negative keywords first
            if any(nk.lower() in text_lower for nk in skill.negative_keywords):
                continue
            # Check positive keywords
            if any(kw.lower() in text_lower for kw in skill.trigger_keywords):
                matches.append(skill)
        return matches

    def find_by_capability(self, capability: str, tags: list[str] | None = None) -> list[SkillProfile]:
        """Find skills matching a capability domain and tags."""
        matches = []
        for skill in self.skills.values():
            # Match on capability in description
            if capability.lower() in skill.description.lower():
                matches.append(skill)
                continue
            # Match on tags in trigger keywords
            if tags and any(
                tag.lower() in kw.lower()
                for tag in tags
                for kw in skill.trigger_keywords
            ):
                matches.append(skill)
        return matches

    def get_skill(self, name: str) -> SkillProfile | None:
        return self.skills.get(name)


# Default registry with known skills
def _build_default_registry() -> SkillRegistry:
    """Build the default skill registry from project skills/."""
    registry = SkillRegistry()

    skills_config = [
        SkillProfile(
            name="nezha",
            description="Bug fixing, code modification, and execution tasks",
            trigger_keywords=[
                "修复bug", "fix bug", "帮我修", "帮我fix", "帮我解决",
                "find and fix", "patch", "demon_hunt", "lotus_body", "三头六臂",
            ],
            negative_keywords=["仅调查", "只查", "不要修改", "just investigate"],
            tools=["demon_hunt", "lotus_body", "assess_workload", "create_assignment_plan"],
            module_path="skills.tool_nezha.scripts",
        ),
        SkillProfile(
            name="tianyan",
            description="Investigation, logic tracing, and root cause analysis",
            trigger_keywords=[
                "追踪", "诊断", "查错", "为什么报错", "查找原因",
                "trace", "diagnose", "investigate", "root cause", "logic chain",
            ],
            negative_keywords=["修复", "fix", "修掉", "帮我修"],
            tools=["logic_tracer", "web_doc_fetcher", "cross_verifier", "security_auditor"],
            module_path="skills.tool_tianyan.scripts",
        ),
        SkillProfile(
            name="wanglingguan",
            description="Compliance, auditing, and security scanning",
            trigger_keywords=[
                "安全扫描", "安全漏洞", "安全审查", "合规检查", "格式审查",
                "代码质量", "security scan", "security audit", "compliance", "OWASP",
            ],
            negative_keywords=["写文档", "归档", "压缩上下文"],
            tools=["format_auditor", "security_scanner", "semantic_analyzer", "ticket_manager"],
            module_path="skills.tool_wanglingguan.scripts",
        ),
        SkillProfile(
            name="yindan",
            description="Precise, minimal-scope code fix on a single location",
            trigger_keywords=[
                "精准修复", "精确替换", "单点替换", "就改这一处",
                "precise fix", "exact replacement", "single spot",
            ],
            negative_keywords=["多个文件", "批量", "全局", "bulk"],
            tools=["precise_fix"],
            module_path="skills.tool_yindan.scripts",
        ),
        SkillProfile(
            name="taibai",
            description="Documentation management, context compression, and archiving",
            trigger_keywords=[
                "写文档", "归档", "压缩上下文", "生成报告", "技术文档",
                "write docs", "archive", "compress context", "GSSC",
            ],
            negative_keywords=["审查", "audit", "安全扫描", "合规"],
            tools=["archive_manager", "context_compressor", "gssc_pipeline"],
            module_path="skills.tool_taibai.scripts",
        ),
        SkillProfile(
            name="taie",
            description="New feature development and substantial single-file modifications",
            trigger_keywords=[
                "新功能", "添加功能", "实现功能", "add feature", "implement feature",
                "new feature", "scaffold", "endpoint", "middleware",
            ],
            negative_keywords=["改一行", "typo", "单点", "重命名"],
            tools=["risk_assessor", "standard_write"],
            module_path="skills.tool_taie.scripts",
        ),
        SkillProfile(
            name="sanjian",
            description="Multi-file refactoring and code restructuring",
            trigger_keywords=[
                "多文件重构", "架构重组", "模块拆分", "代码迁移",
                "multi-file refactoring", "architecture restructure", "decouple",
            ],
            negative_keywords=["单个文件", "一处", "single file"],
            tools=["dependency_analyzer", "task_decomposer", "scope_guardian", "executor"],
            module_path="skills.tool_sanjian.scripts",
        ),
        SkillProfile(
            name="kaishan",
            description="Bulk file deletion, mass regex replacement, large-scale cleanup",
            trigger_keywords=[
                "批量删除", "全部删除", "全局替换", "废弃代码",
                "bulk delete", "mass cleanup", "nuke", "purge",
            ],
            negative_keywords=["精准", "就一处", "单点"],
            tools=["blast_assessor", "bulk_operations"],
            module_path="skills.tool_kaishan.scripts",
        ),
        SkillProfile(
            name="bajiu",
            description="Task routing and difficulty assessment",
            trigger_keywords=[
                "哪个工具", "该用什么", "帮我评估难度", "任务拆解",
                "which tool", "how to approach", "break down task", "triage",
            ],
            negative_keywords=["重构", "修复", "安全", "文档"],
            tools=["skill_scanner", "task_analyzer"],
            module_path="skills.tool_bajiu.scripts",
        ),
    ]

    for profile in skills_config:
        registry.register(profile)

    return registry


# Module-level singleton
_default_registry: SkillRegistry | None = None


def get_skill_registry() -> SkillRegistry:
    """Get the default skill registry (singleton)."""
    global _default_registry
    if _default_registry is None:
        _default_registry = _build_default_registry()
    return _default_registry


def route_to_skill(task_description: str) -> SkillProfile | None:
    """Route a task description to the best matching skill.

    Returns the highest-confidence match, or None if no skill matches.
    """
    registry = get_skill_registry()
    matches = registry.find_by_keyword(task_description)
    return matches[0] if matches else None
