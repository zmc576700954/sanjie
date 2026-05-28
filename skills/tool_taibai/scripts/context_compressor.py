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
        if not isinstance(text, str):
            raise TypeError(
                f"compress() expects a string, got {type(text).__name__}"
            )
        if not text:
            return ""
        blocks = self._split_markdown_blocks(text)

        compressed_blocks = []
        for is_code, block_content in blocks:
            if is_code:
                compressed_blocks.append(self._compress_code_or_log(block_content))
            else:
                compressed_blocks.append(self._compress_natural_language(block_content))

        return "\n".join(compressed_blocks).strip()

    def _split_markdown_blocks(self, text: str):
        """State-machine splitter — correctly handles nested / mismatched ``` markers.

        Walks the text line-by-line.  When a line starts with ``` we enter
        code-block mode; the next line starting with ``` (or end-of-text)
        closes the block.  This avoids the regex pitfalls with non-greedy
        matching on nested fences.
        """
        blocks = []
        current_lines = []
        in_code = False

        for line in text.split("\n"):
            stripped = line.lstrip()
            if stripped.startswith("```"):
                if not in_code:
                    # Starting a code block — flush any accumulated prose
                    prose = "\n".join(current_lines)
                    if prose.strip():
                        blocks.append((False, prose))
                    current_lines = [line]
                    in_code = True
                else:
                    # Closing a code block
                    current_lines.append(line)
                    blocks.append((True, "\n".join(current_lines)))
                    current_lines = []
                    in_code = False
            else:
                current_lines.append(line)

        # Flush remaining content
        remaining = "\n".join(current_lines)
        if remaining.strip():
            if in_code:
                # Unclosed code block — treat the whole thing as code
                blocks.append((True, remaining))
            else:
                blocks.append((False, remaining))

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
                pass

        # Stack trace / Log truncation heuristic
        if len(content_lines) > 30:
            trace_keywords = ['traceback', 'exception', 'error', 'at line', '    at ']
            is_trace = any(any(kw in line.lower() for kw in trace_keywords) for line in content_lines[:10])

            if is_trace:
                truncated_content = content_lines[:10] + ["\n... [LOGS TRUNCATED BY TAIBAI COMPRESSOR] ...\n"] + content_lines[-10:]
                return f"{header}\n" + "\n".join(truncated_content) + f"\n{footer}"

        # Standard code compression: remove empty lines and inline comments if aggressive
        compressed_lines = []
        for line in content_lines:
            if not line.strip():
                continue
            if self.aggressive and line.strip().startswith(('//', '#', '--')):
                continue
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
