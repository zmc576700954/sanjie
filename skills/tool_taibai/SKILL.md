---
name: taibai
description: "Documentation management, context compression, archiving, and GSSC pipeline toolset."
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
