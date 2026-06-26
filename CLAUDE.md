# Agents Develop

Multi-tool agent/skill development environment.

## Commands
- `pytest` - Run tests
- `agents-dev` - CLI tool (after install)

## Architecture
Core + Format Separation: core/ has tool-agnostic logic, formats/ has tool-specific templates, migration/ handles conversion.

## Development
- All core components inherit from CoreComponent ABC
- Use ComponentRegistry for component management
- Follow the design spec at docs/superpowers/specs/
