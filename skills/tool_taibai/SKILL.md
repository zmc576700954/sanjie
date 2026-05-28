---
name: taibai
description: >
  Documentation management, context compression, archiving, and GSSC pipeline toolset.
  Use for: writing technical docs, archiving completed work, compressing conversation
  logs/context, generating structured reports, and managing documentation lifecycle.
  NOT for: image/file compression, zip/archive files (this is about CONTEXT compression).
  NOT for: code compliance checks or security audits (use wanglingguan_skill).
  NOT for: code quality review (use wanglingguan_skill for that).
  Trigger when the user wants to WRITE, ORGANIZE, COMPRESS (context), ARCHIVE,
  or GENERATE documentation/reports.
trigger_keywords:
  high_confidence:
    - "写文档"
    - "归档"
    - "压缩上下文"
    - "压缩对话"
    - "压缩日志"
    - "生成报告"
    - "技术文档"
    - "changelog"
    - "decision log"
    - "meeting notes"
    - "会议纪要"
    - "GSSC"
    - "generate report"
    - "write docs"
    - "archive"
    - "compress context"
    - "compress conversation"
    - "上下文压缩"
    - "context compress"
    - "记忆管理"
    - "设计文档"
    - "技术方案"
    - "变更记录"
    - "交接文档"
    - "spec文档"
  medium_confidence:
    - "文档"
    - "总结"
    - "记录"
    - "梳理"
    - "整理"
    - "精简"
    - "structured"
    - "summarize"
    - "log"
    - "verbose"
    - "太长了"
    - "sprint交付"
    - "技术决策"
  requires_context:
    - "压缩" → only when context involves conversation, logs, context window, or documentation (NOT images, files, or data)
    - "总结" → only when context involves documentation output (not casual explanation)
    - "整理" → only when context involves document organization (not code cleanup)
negative_keywords:
  - "审查"
  - "audit"
  - "安全扫描"
  - "compliance"
  - "漏洞"
  - "security scan"
  - "格式检查"
  - "cyclomatic"
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
      aggressive: "If true, strips stop-words and comments aggressively."
  - name: gather
    script: "scripts/gather.py"
    parameters:
      source_paths: "List of file or directory paths to collect."
      patterns: "Optional list of glob patterns to match files within directories."
  - name: select
    script: "scripts/select.py"
    parameters:
      raw_sources: "Output dict from gather_sources, containing a 'sources' list."
      noise_patterns: "Optional list of regex patterns to override default noise filters."
      keep_sections: "Optional list of section names to preserve (reserved for future use)."
  - name: structure
    script: "scripts/structure.py"
    parameters:
      selected_sources: "Output dict from select_content, containing 'filtered_sources'."
      doc_type: "Document type: 'spec', 'archive', 'handoff', or 'memory'."
      author: "Author name to inject into YAML frontmatter."
      metadata: "Optional dict of additional frontmatter fields."
  - name: gssc_pipeline
    script: "scripts/gssc_pipeline.py"
    parameters:
      source_paths: "List of file or directory paths to process."
      doc_type: "Document type for structuring."
      aggressive_compress: "Whether to enable aggressive compression in the final step."
      output_path: "Optional path to write the final compressed output."
      author: "Author name for frontmatter."
  - name: review_request
    script: "scripts/review_request.py"
    parameters:
      document_path: "Path to the document to review."
      review_type: "Category of review: 'format', 'quality', 'assertion', or 'architecture'."
      context_notes: "Optional additional context for the reviewer."
---
