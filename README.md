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

## Acknowledgments

AIXtract incorporates adapted components from [CAMEL-AI](https://github.com/camel-ai/camel),
licensed under the Apache License 2.0. See [NOTICE](NOTICE) for details.

## License

Apache License 2.0
