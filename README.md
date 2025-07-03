# DeepSeek Translator

![Python Version](https://img.shields.io/badge/python-3.13-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

### Overview

DeepSeek Translator is a command-line tool that translates [i18next JSON](https://www.i18next.com/misc/json-format) files using the DeepSeek's AI.

- 🔍 **Smart Key Detection**: Only translates keys missing in target file
- 🌐 **Language Support**: Translates between any language pair supported by DeepSeek
- 🧠 **Context-Aware**: Uses JSON keys as context for accurate translations
- 🔄 **Merge Capabilities**: Preserves existing translations

```sh
uvx --from git+https://github.com/theJian/deepseek-translator@main deepseek-translator \
  --source-lang en \
  --target-lang zh \
  --source-file locales/en.json \
  --target-file locales/zh.json
```

### Prerequisites

- Python 3.13+
- [DeepSeek API Token](https://platform.deepseek.com/api-keys)


## Configuration

```bash
# Set API token
export DEEPSEEK_API_KEY='your_api_token_here'
```


Create i18n.yaml in your project root:
```yaml
# Each group defines source + target files
- en: "locales/en.json"       # First language = source
  ja: "locales/ja.json"       # Target languages
  es: "locales/es.json"

- en: "messages/main.json"    # Another group
  fr: "messages/fr.json"
  de: "messages/de.json"
```

## Usage

Without configuration file, you can run the command directly:
```bash
uvx --from git+https://github.com/theJian/deepseek-translator@main deepseek-translator \
  --source-lang en \
  --source-lang en \
  --target-lang zh \
  --source-file locales/en.json \
  --target-file locales/zh.json
```

With configuration file `i18n.yaml` in the project root, run:
```bash
uvx --from git+https://github.com/theJian/deepseek-translator@main deepseek-translator
```

## CLI Arguments

| Argument        | Description                                  |
|-----------------|----------------------------------------------|
| `--config`      | Custom config file path                      |
| `--source-lang` | Source language code (e.g., 'en')            |
| `--target-lang` | Target language code (e.g., 'zh')            |
| `--source-file` | Path to source JSON file                     |
| `--target-file` | Path to target JSON file                     |
| `--verbose`     | Enable detailed debug logging                |


## License
MIT
