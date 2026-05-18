import re
import argparse
import json
import sys

class ContextCompressor:
    """
    A heuristic, rule-based compressor designed for AI Agent memory management.
    It reduces token bloat while preserving semantic fidelity.
    """
    def __init__(self, aggressive: bool = False):
        self.aggressive = aggressive

    def compress(self, text: str) -> str:
        # 1. Separate code blocks from normal text to apply different rules
        blocks = self._split_markdown_blocks(text)
        
        compressed_blocks = []
        for is_code, block_content in blocks:
            if is_code:
                compressed_blocks.append(self._compress_code_or_log(block_content))
            else:
                compressed_blocks.append(self._compress_natural_language(block_content))
                
        return "\n".join(compressed_blocks).strip()

    def _split_markdown_blocks(self, text: str):
        """Splits text into tuples of (is_code: bool, content: str)"""
        # Regex to find markdown code blocks (```language ... ```)
        pattern = re.compile(r'(```.*?```)', re.DOTALL)
        parts = pattern.split(text)
        
        blocks = []
        for part in parts:
            if part.startswith("```") and part.endswith("```"):
                blocks.append((True, part))
            elif part.strip():
                blocks.append((False, part))
        return blocks

    def _compress_natural_language(self, text: str) -> str:
        """Applies telegraphic compression and heuristic pruning to text."""
        # Remove HTML/XML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Remove long hashes, base64 strings, or tokens (heuristic: > 60 alphanumeric chars)
        text = re.sub(r'\b[a-zA-Z0-9+/=]{60,}\b', '[TRUNCATED_HASH]', text)
        
        # Collapse multiple newlines and spaces
        text = re.sub(r'\n\s*\n', '\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        # Aggressive mode: remove common filler words (telegraphic compression)
        if self.aggressive:
            stop_words = {
                'a', 'an', 'the', 'is', 'are', 'was', 'were', 'to', 'in', 'for', 
                'of', 'with', 'by', 'as', 'at', 'on', 'about', 'and', 'or', 'but'
            }
            words = text.split()
            filtered_words = [w for w in words if w.lower() not in stop_words]
            text = " ".join(filtered_words)
            
        return text.strip()

    def _compress_code_or_log(self, block: str) -> str:
        """Compresses code blocks and truncates long stack traces."""
        # Extract the language identifier if present
        lines = block.split('\n')
        if len(lines) < 3:
            return block
            
        header = lines[0]
        footer = lines[-1]
        content_lines = lines[1:-1]
        
        # Check if it looks like a JSON block to minify
        if 'json' in header.lower() or (content_lines and content_lines[0].strip().startswith('{')):
            try:
                json_str = "\n".join(content_lines)
                parsed = json.loads(json_str)
                minified = json.dumps(parsed, separators=(',', ':'))
                return f"{header}\n{minified}\n{footer}"
            except json.JSONDecodeError:
                pass # Fallback to normal processing
                
        # Stack trace / Log truncation heuristic
        # If the block is very long (e.g., > 30 lines) and looks like logs or stack trace
        if len(content_lines) > 30:
            trace_keywords = ['traceback', 'exception', 'error', 'at line', '    at ']
            is_trace = any(any(kw in line.lower() for kw in trace_keywords) for line in content_lines[:10])
            
            if is_trace:
                # Keep top 10 lines (usually contains the error type) and bottom 10 lines (usually the exact failure point)
                truncated_content = content_lines[:10] + ["\n... [LOGS TRUNCATED BY TAIBAI COMPRESSOR] ...\n"] + content_lines[-10:]
                return f"{header}\n" + "\n".join(truncated_content) + f"\n{footer}"

        # Standard code compression: remove empty lines and inline comments if aggressive
        compressed_lines = []
        for line in content_lines:
            if not line.strip():
                continue
            if self.aggressive and line.strip().startswith(('//', '#', '--')):
                continue # Strip full-line comments
            compressed_lines.append(line)
            
        return f"{header}\n" + "\n".join(compressed_lines) + f"\n{footer}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Taibai Semantic Context Compressor")
    parser.add_argument("--file", required=True, help="Path to the file to compress")
    parser.add_argument("--aggressive", action="store_true", help="Enable aggressive telegraphic compression and comment stripping")
    args = parser.parse_args()
    
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        compressor = ContextCompressor(aggressive=args.aggressive)
        compressed_text = compressor.compress(content)
        
        print(compressed_text)
    except Exception as e:
        print(f"Error compressing file: {e}")
        sys.exit(1)
