from skills.tool_taibai.scripts.context_compressor import ContextCompressor


class TestContextCompressor:
    def test_compress_plain_text(self):
        text = "Hello   world\n\nThis is a test."
        compressor = ContextCompressor()
        result = compressor.compress(text)
        assert "Hello" in result
        assert "world" in result

    def test_compress_html_tags(self):
        text = "<div>Hello</div> world"
        compressor = ContextCompressor()
        result = compressor.compress(text)
        assert "<div>" not in result
        assert "Hello" in result
        assert "world" in result

    def test_compress_long_hash(self):
        text = "abc " + "a" * 80 + " def"
        compressor = ContextCompressor()
        result = compressor.compress(text)
        assert "[TRUNCATED_HASH]" in result
        assert "abc" in result
        assert "def" in result

    def test_compress_json_block(self):
        text = "```json\n{\"key\": \"value\"}\n```"
        compressor = ContextCompressor()
        result = compressor.compress(text)
        # JSON should be minified
        assert "\"key\":\"value\"" in result or "\"key\": \"value\"" in result

    def test_compress_aggressive_mode(self):
        text = "The quick brown fox jumps over a lazy dog."
        compressor = ContextCompressor(aggressive=True)
        result = compressor.compress(text)
        # Stop-words like "the" and "a" (as whole words) should be removed,
        # but the letter 'a' inside words like "lazy" must remain.
        words = result.lower().split()
        assert "the" not in words
        assert "a" not in words
        assert "quick" in result.lower()

    def test_compress_long_trace(self):
        lines = ["Traceback (most recent call last):"] + [f"  File \"test.py\", line {i}" for i in range(50)]
        text = "```\n" + "\n".join(lines) + "\n```"
        compressor = ContextCompressor()
        result = compressor.compress(text)
        assert "[LOGS TRUNCATED BY TAIBAI COMPRESSOR]" in result
        assert "Traceback" in result
