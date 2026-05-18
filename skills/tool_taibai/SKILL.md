---
name: taibai
description: "Documentation management, context compression, and archiving toolset."
tools:
  - name: archive_manager
    script: "scripts/archive_manager.py"
    parameters:
      file: "Path to the file to archive."
      topic: "Short topic name."
      summary: "One-sentence summary for the index."
  - name: context_compressor
    script: "scripts/context_compressor.py"
    parameters:
      file: "Path to the file containing verbose text/logs to compress."
---
