# DeepSeek Translator

![Python Version](https://img.shields.io/badge/python-3.13-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

### Overview

DeepSeek Translator is a tool that translates [i18next JSON](https://www.i18next.com/misc/json-format) files using DeepSeek or Xiaomi MiMo.
It provides a command-line interface and [GitHub Action](#github-action) to integrate into workflows.

- 🔍 **Smart Key Detection**: Only translates keys missing in target file
- 🌐 **Language Support**: Translates between any language pair supported by the selected provider
- 🧠 **Context-Aware**: Uses JSON keys as context for accurate translations
- 🔄 **Merge Capabilities**: Preserves existing translations

```sh
uvx --from git+https://github.com/theJian/deepseek-translator@v3 deepseek-translator \
  --source-lang en \
  --target-lang zh \
  --source-file locales/en.json \
  --target-file locales/zh.json
```

### Prerequisites

- Python 3.13+
- [DeepSeek API Token](https://platform.deepseek.com/api-keys) or [Xiaomi MiMo API Token](https://platform.xiaomimimo.com/)


## Configuration

```bash
# Set API token
export DEEPSEEK_API_KEY='your_api_token_here'
```

The default model is `deepseek-flash` (currently DeepSeek V4.1 Flash-1017).
The model name automatically selects the API endpoint and key:

| Model prefix | API endpoint | API key environment variable |
|--------------|--------------|------------------------------|
| `deepseek-` | `https://api.deepseek.com` | `DEEPSEEK_API_KEY` |
| `mimo-` | `https://api.xiaomimimo.com/v1` | `MIMO_API_KEY` |

To use Xiaomi MiMo:

```bash
export MIMO_API_KEY='your_mimo_api_key_here'
deepseek-translator --model mimo-v2.6-pro
```

You can also select `mimo-v2.6-flash` or `mimo-v2.6-pro-ultraspeed`.
Set `TRANSLATOR_MODEL` to choose a model without passing `--model`.
Both providers use JSON output with thinking disabled for translation.

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

Without a configuration file, you can run the command directly:
```bash
uvx --from git+https://github.com/theJian/deepseek-translator@v3 deepseek-translator \
  --source-lang en \
  --source-lang en \
  --target-lang zh \
  --source-file locales/en.json \
  --target-file locales/zh.json
```

With the configuration file `i18n.yaml` in the project root, run:
```bash
uvx --from git+https://github.com/theJian/deepseek-translator@v3 deepseek-translator
```

## CLI Arguments

| Argument        | Description                                  |
|-----------------|----------------------------------------------|
| `--config`      | Custom config file path                      |
| `--source-lang` | Source language code (e.g., 'en')            |
| `--target-lang` | Target language code (e.g., 'zh')            |
| `--source-file` | Path to source JSON file                     |
| `--target-file` | Path to target JSON file                     |
| `--model`       | DeepSeek or MiMo model ID; determines the provider (default: `deepseek-flash`; env: `TRANSLATOR_MODEL`) |
| `--verbose`     | Enable detailed debug logging                |


## GitHub Action

Check [the example](https://github.com/theJian/deepseek-translator-action-demo/)

Create `.github/workflows/i18n.yml`.
```yaml
      - uses: actions/checkout@v4
      - uses: theJian/deepseek-translator@v3
        with:
          deepseek-api-key: ${{ secrets.DEEPSEEK_API_KEY }}
      - uses: peter-evans/create-pull-request@v7 # Or commit it using stefanzweifel/git-auto-commit-action
```

For MiMo, configure the Action with:

```yaml
      - uses: theJian/deepseek-translator@v3
        with:
          mimo-api-key: ${{ secrets.MIMO_API_KEY }}
          model: mimo-v2.6-pro
```

The Action accepts `model`, `deepseek-api-key`, and `mimo-api-key`.
Provide the API key for the selected provider. These inputs are available in `v3`.

## License
MIT
