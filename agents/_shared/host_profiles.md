---
auto_generated: true
date: 2026-05-19
---

# Host Profiles

This file documents the characteristics of each supported AI IDE host for routing optimization.

## Claude Code
- **Model**: Claude Sonnet/Opus
- **Strength**: Complex reasoning, nuanced code understanding
- **Weakness**: Occasionally over-cautious
- **Routing**: Trust L2 for complex multi-factor errors
- **Detection**: Environment variable `CLAUDE_CODE` or `.claude/` directory

## Cursor
- **Model**: GPT-4 / Claude (user-configurable)
- **Strength**: Fast, excellent pattern matching
- **Routing**: L1 keyword matching usually sufficient
- **Detection**: Environment variable `CURSOR_MCP` or `~/.cursor` directory

## Gemini CLI
- **Model**: Gemini 1.5 Pro
- **Strength**: Ultra-long context, multi-language
- **Weakness**: Less consistent with structured output
- **Routing**: Always enforce `[confidence]` field in output
- **Detection**: Environment variable `GEMINI_CLI`

## Codex
- **Model**: GPT-4
- **Strength**: Excellent code generation, broad knowledge
- **Routing**: L1 + L2 hybrid
- **Detection**: Environment variable `CODEX` or `OPENAI_CODEX`

## Trae
- **Model**: Claude/GPT (user-configurable)
- **Strength**: Fast iteration, good UI integration
- **Routing**: Standard L1/L2/L3 pipeline
- **Detection**: Environment variable `TRAE` or `~/.trae` directory

## Local LLM (ollama)
- **Model**: User-configured (codellama, llama3, etc.)
- **Strength**: Offline, free, private
- **Weakness**: Smaller models may hallucinate
- **Routing**: Use only for simple L2; aggressively fallback to L1
- **Detection**: `localhost:11434/api/tags` reachable
