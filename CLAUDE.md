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

## Project Convention

Each independent feature should be developed as a standalone package/component rather than being forced into a rigid shared directory hierarchy. The existing `core/`, `formats/`, `components/`, and `cli/` structure is the reference environment for the core framework. New capabilities (such as `skill_manager/`) live as separate packages at the repository root and may be installed, tested, and versioned independently.
