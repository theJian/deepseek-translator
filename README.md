# DeepSeek Translator

![Python Version](https://img.shields.io/badge/python-3.13-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

### Overview

DeepSeek Translator is a command-line tool that translates i18next JSON files using the DeepSeek's AI.

- 🔍 **Smart Key Detection**: Only translates keys missing in target file
- 🌐 **Language Support**: Translates between any language pair supported by DeepSeek
- 🧠 **Context-Aware**: Uses JSON keys as context for accurate translations
- 🔄 **Merge Capabilities**: Preserves existing translations

```sh
uv run main.py \
  --source-lang en \
  --target-lang zh \
  --source-file locales/en.json \
  --target-file locales/zh.json
```

### Prerequisites

- Python 3.13+
- [DeepSeek API Token](https://platform.deepseek.com/api-keys)


## Installation

```bash
# Clone repository
git clone <repository-url>
cd deepseek-translator

# Set API token
export DEEPSEEK_API_TOKEN='your_api_token_here'
```

## CLI Arguments

| Argument        | Description                                  | Required |
|-----------------|----------------------------------------------|----------|
| `--source-lang` | Source language code (e.g., 'en')            | Yes      |
| `--target-lang` | Target language code (e.g., 'zh')            | Yes      |
| `--source-file` | Path to source JSON file                     | Yes      |
| `--target-file` | Path to target JSON file                     | Yes      |
| `--verbose`     | Enable detailed debug logging                | No       |


## License
MIT
