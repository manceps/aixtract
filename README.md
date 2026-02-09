# AIXtract

Enterprise-grade document extraction for LLM and NLP pipelines.

## Installation

```bash
pip install aixtract
pip install "aixtract[all]"  # All format support
```

## Quick Start

```python
from aixtract import extract

result = extract("document.pdf")
print(result.content_markdown)
```

## Supported Formats

| Converter | Extensions                     | Dependencies      |
| :--- | :--- | :--- |
| txt       | .txt, .md, .rst, .log          | none              |
| csv       | .csv, .tsv                     | none              |
| json      | .json                          | none              |
| xml       | .xml                           | none              |
| archive   | .zip                           | none              |
| pdf       | .pdf                           | pypdf, pdfplumber |
| docx      | .docx, .doc                    | docx              |
| xlsx      | .xlsx, .xls                    | openpyxl          │
| pptx      | .pptx, .ppt                    | pptx              |
| html      | .html, .htm                    | bs4               |
| epub      | .epub                          | ebooklib, bs4     |
| image     | .png, .jpg, .jpeg, .tiff, .bmp | PIL, pytesseract  |
| audio     | .mp3, .wav, .m4a, .flac, .ogg  | whisper           |

## Development Setup

If you are developing or contributing to `aixtract`, you can use the provided `Makefile` or `pip` directly.

### Option 1: Using make (Recommended)

The `Makefile` is configured to automatically use the python and pip binaries inside `.venv`, so you don't even need to activate the environment to install.

**Install for usage:**
```bash
make install
```

**Install for development (includes testing/linting tools):**
```bash
make dev
```

### Option 2: Using pip manually

If you prefer to run commands manually or don't have make installed:

1. **Activate the virtual environment:**
    ```bash
    source .venv/bin/activate
    ```

2. **Install the project in editable mode:**
    ```bash
    # For basic usage
    pip install -e .

    # For development (with dev dependencies)
    # NOTE: Quotes are required in zsh
    pip install -e ".[all,dev]"
    ```

## Acknowledgments

AIXtract incorporates adapted components from [CAMEL-AI](https://github.com/camel-ai/camel),
licensed under the Apache License 2.0. See [NOTICE](NOTICE) for details.

## License

Apache License 2.0
