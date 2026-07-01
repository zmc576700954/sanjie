from __future__ import annotations

import json

from mcp.server import Server
from mcp.types import Tool, TextContent

from skill_manager.errors import FragmentNotFoundError, SkillNotFoundError
from skill_manager.language import HeuristicLanguageDetector
from skill_manager.resolver import PriorityResolver
from skill_manager.store import SkillStore
from skill_manager.trigger import MultiStrategyTriggerResolver


def create_server(store: SkillStore) -> Server:
    server = Server("skill-manager")
    resolver = PriorityResolver(store)
    language_detector = HeuristicLanguageDetector()
    trigger_resolver = MultiStrategyTriggerResolver()

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="list_skills",
                description="List all registered skills with optional filters",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "filter_language": {"type": "string"},
                        "filter_action": {"type": "string"},
                        "filter_tag": {"type": "string"},
                    },
                },
            ),
            Tool(
                name="resolve_skill",
                description="Resolve a skill prompt for given context",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "language": {"type": "string"},
                        "action": {"type": "string"},
                        "trigger": {"type": "string"},
                        "project_path": {"type": "string"},
                        "file_path": {"type": "string"},
                    },
                    "required": ["name"],
                },
            ),
            Tool(
                name="detect_language",
                description="Detect primary programming language of a project or file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_path": {"type": "string"},
                        "file_path": {"type": "string"},
                        "explicit_language": {"type": "string"},
                    },
                },
            ),
            Tool(
                name="register_skill",
                description="Register a new skill with metadata and optional fragments",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "metadata": {"type": "object"},
                        "base_prompt": {"type": "string"},
                        "fragments": {"type": "array"},
                    },
                    "required": ["metadata", "base_prompt"],
                },
            ),
            Tool(
                name="update_fragment",
                description="Add or update a prompt fragment for a skill",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "skill_name": {"type": "string"},
                        "fragment": {"type": "object"},
                    },
                    "required": ["skill_name", "fragment"],
                },
            ),
            Tool(
                name="register_trigger",
                description="Register a custom trigger rule for a skill",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "skill_name": {"type": "string"},
                        "trigger": {"type": "object"},
                    },
                    "required": ["skill_name", "trigger"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        if name == "list_skills":
            filters = {k: v for k, v in arguments.items() if v is not None}
            # Map filter keys to internal names
            key_map = {
                "filter_language": "language",
                "filter_action": "action",
                "filter_tag": "tag",
            }
            filters = {key_map.get(k, k): v for k, v in filters.items()}
            skills = store.list_skills(filters)
            payload = [
                {
                    "name": s.name,
                    "description": s.description,
                    "version": s.version,
                    "default_action": s.default_action,
                    "supported_languages": s.supported_languages,
                }
                for s in skills
            ]
            return [TextContent(type="text", text=json.dumps(payload))]

        if name == "resolve_skill":
            skill_name = arguments["name"]
            language = arguments.get("language")
            action = arguments.get("action")
            trigger = arguments.get("trigger")
            project_path = arguments.get("project_path")

            if language is None:
                detect = language_detector.detect(project_path, arguments.get("file_path"))
                language = detect.primary_language

            if action is None or trigger is None:
                skill = store.get_skill(skill_name)
                if skill is None:
                    raise SkillNotFoundError(f"Skill '{skill_name}' not found")
                trigger_result = trigger_resolver.resolve(trigger or "", None, skill)
                action = action or trigger_result.action or skill.default_action
                language = language or trigger_result.language_hint

            result = resolver.resolve(
                name=skill_name,
                language=language,
                action=action,
                trigger=trigger,
                project_path=project_path,
            )
            return [TextContent(type="text", text=json.dumps(result.to_dict()))]

        if name == "detect_language":
            result = language_detector.detect(
                arguments.get("project_path"),
                arguments.get("file_path"),
                arguments.get("explicit_language"),
            )
            return [TextContent(type="text", text=json.dumps({
                "primary_language": result.primary_language,
                "confidence": result.confidence,
                "secondary_languages": result.secondary_languages,
                "signals": result.signals,
            }))]

        if name == "register_skill":
            from skill_manager.models import Skill, TriggerRule

            metadata = arguments.get("metadata", {})
            if "name" not in metadata:
                return [TextContent(type="text", text="Error: metadata must contain 'name'.")]
            if "base_prompt" not in arguments:
                return [TextContent(type="text", text="Error: arguments must contain 'base_prompt'.")]

            skill = Skill(
                name=metadata["name"],
                description=metadata.get("description", ""),
                version=metadata.get("version", "1.0.0"),
                base_prompt=arguments["base_prompt"],
                default_action=metadata.get("default_action"),
                supported_languages=metadata.get("supported_languages", ["*"]),
                tags=metadata.get("tags", []),
                triggers=[TriggerRule(**t) for t in metadata.get("triggers", [])],
            )
            store.save_skill(skill)

            for fragment_data in arguments.get("fragments", []):
                from skill_manager.models import PromptFragment

                fragment = PromptFragment(
                    id=fragment_data["id"],
                    skill_name=skill.name,
                    language=fragment_data.get("language"),
                    action=fragment_data.get("action"),
                    trigger=fragment_data.get("trigger"),
                    priority=fragment_data.get("priority", 0),
                    content=fragment_data["content"],
                    is_required=fragment_data.get("is_required", False),
                )
                store.save_fragment(fragment)

            return [TextContent(type="text", text=f"Skill '{skill.name}' registered.")]

        if name == "update_fragment":
            from skill_manager.models import PromptFragment

            skill_name = arguments.get("skill_name", "")
            fragment_data = arguments.get("fragment", {})
            if "id" not in fragment_data:
                return [TextContent(type="text", text="Error: fragment must contain 'id'.")]
            if "content" not in fragment_data:
                return [TextContent(type="text", text="Error: fragment must contain 'content'.")]

            fragment = PromptFragment(
                id=fragment_data["id"],
                skill_name=skill_name,
                language=fragment_data.get("language"),
                action=fragment_data.get("action"),
                trigger=fragment_data.get("trigger"),
                priority=fragment_data.get("priority", 0),
                content=fragment_data["content"],
                is_required=fragment_data.get("is_required", False),
            )
            store.save_fragment(fragment)
            return [TextContent(type="text", text=f"Fragment '{fragment.id}' updated.")]

        if name == "register_trigger":
            from skill_manager.models import TriggerRule

            skill_name = arguments["skill_name"]
            trigger_data = arguments["trigger"]
            skill = store.get_skill(skill_name)
            if skill is None:
                raise SkillNotFoundError(f"Skill '{skill_name}' not found")
            skill.triggers = skill.triggers + [TriggerRule(**trigger_data)]
            store.save_skill(skill)
            return [TextContent(type="text", text=f"Trigger registered for '{skill_name}'.")]

        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    return server
