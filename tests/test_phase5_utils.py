"""Test Phase 5 utility modules."""

def test_imports():
    from aixtract.utils.markdown import clean_markdown, table_to_markdown, escape_markdown, code_block, heading
    from aixtract.utils.tokens import estimate_tokens, count_tokens_tiktoken, split_by_tokens
    from aixtract.utils.chunking import ContentChunker
    from aixtract.utils.parallel import process_batch
    from aixtract.utils.filename import sanitize_filename

def test_estimate_tokens():
    from aixtract.utils.tokens import estimate_tokens
    result = estimate_tokens("Hello world this is a test")
    assert isinstance(result, int)
    assert result > 0

def test_clean_markdown():
    from aixtract.utils.markdown import clean_markdown
    result = clean_markdown("Hello\n\n\n\nWorld")
    assert result == "Hello\n\nWorld"

def test_sanitize_filename():
    from aixtract.utils.filename import sanitize_filename
    result = sanitize_filename("my file (1).pdf")
    assert '(' not in result
    assert ')' not in result

def test_table_to_markdown():
    from aixtract.utils.markdown import table_to_markdown
    result = table_to_markdown(["A", "B"], [["1", "2"]])
    assert "| A | B |" in result
    assert "| 1 | 2 |" in result

def test_code_block():
    from aixtract.utils.markdown import code_block
    result = code_block("x = 1", "python")
    assert result.startswith("```python")

def test_heading():
    from aixtract.utils.markdown import heading
    result = heading("Title", 2)
    assert result == "## Title"

def test_split_by_tokens():
    from aixtract.utils.tokens import split_by_tokens
    long_text = "This is a sentence. " * 100
    result = split_by_tokens(long_text, max_tokens=50)
    assert len(result) > 1

def test_content_chunker():
    from aixtract.utils.chunking import ContentChunker
    chunker = ContentChunker(chunk_size=50)
    chunks = chunker.chunk("# Heading\n\nSome text here.\n\n# Another Heading\n\nMore text.")
    assert len(chunks) > 0

def test_process_batch():
    from aixtract.utils.parallel import process_batch
    results = list(process_batch([1, 2, 3], lambda x: x * 2, max_workers=2))
    assert len(results) == 3
