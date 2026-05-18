# Refactoring Patterns Reference

Load this file when you need guidance on which refactoring strategy to apply.

## Operation Types

### REWRITE
- Complete replacement of file content
- Use when: existing logic is fundamentally broken, no salvageable structure
- Risk: highest — all existing behavior is discarded

### RESTRUCTURE
- Preserve core logic, reorganize architecture
- Use when: logic is correct but organization is wrong (wrong module, wrong class hierarchy)
- Risk: medium — behavior should be preserved but interfaces may change

### INTEGRATE
- Merge content from multiple sources into one
- Use when: duplicated logic across files needs consolidation
- Risk: medium — must ensure all call sites are updated

## Scope Assessment Heuristics

### SAFE indicators
- File has no exports used by other modules
- Changes are internal implementation only
- No public function signatures change

### BOUNDARY indicators
- Public function signatures change (params, return type)
- Class interface changes (new required methods, removed methods)
- File is imported by 1-2 other modules

### DEEP indicators
- File is imported by 3+ modules
- Changes affect data structures passed across module boundaries
- Base class modifications that cascade to all subclasses

## Dependency-Aware Execution Order

1. Identify leaf nodes (files that import others but are not imported)
2. Process leaf nodes first — they can change without breaking dependents
3. Process shared interfaces last — all dependents must be ready
4. If circular dependency exists, flag for user decision before proceeding
