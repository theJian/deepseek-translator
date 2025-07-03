import os
import json
import argparse
from openai import OpenAI
import logging
import yaml
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

PROMPT = """
You are a professional translator that translates the values in the JSON object from {source_lang} to {target_lang}.
Preserve all keys and structure exactly, only return valid JSON without explanations.
Keys provide context for translation.
Do not translate or modify interpolation or nesting like {{value}}, $t(key). All other words should be translated normally.
"""


def find_config_file(
    start_dir: str, filenames: List[str] = ["i18n.yaml", "i18n.yml"]
) -> Optional[str]:
    """Search for config file in current and parent directories"""
    current_dir = os.path.abspath(start_dir)
    while True:
        for filename in filenames:
            config_path = os.path.join(current_dir, filename)
            if os.path.isfile(config_path):
                logger.debug(f"Found config file at: {config_path}")
                return config_path

        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # Reached root directory
            logger.debug("Reached root directory, config not found")
            return None

        current_dir = parent_dir


def count_keys(data: Dict[str, Any]) -> int:
    """Count total keys in a nested dictionary"""
    count = 0
    for value in data.values():
        if isinstance(value, dict):
            count += count_keys(value)
        else:
            count += 1
    return count


def compute_diff(source: Dict[str, Any], target: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively computes the difference between source and target JSON objects.
    Returns a new JSON object containing keys present in source but missing in target.
    """
    diff = {}
    for key, value in source.items():
        if key not in target:
            diff[key] = value
            logger.debug(f"New key found: {key}")
        elif isinstance(value, dict) and isinstance(target[key], dict):
            nested_diff = compute_diff(value, target[key])
            if nested_diff:
                diff[key] = nested_diff
    return diff


def deep_merge(target: Dict[str, Any], ext: Dict[str, Any]) -> None:
    """
    Recursively merges ext dictionary into target dictionary.
    Modifies the target dictionary in-place.
    """
    for key, value in ext.items():
        if key in target and isinstance(value, dict) and isinstance(target[key], dict):
            deep_merge(target[key], value)
        else:
            target[key] = value


def translate(client, text: str, prompt: str) -> str:
    """
    Translate text using DeepSeek API
    """
    logger.debug("Sending translation request...")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": prompt,
            },
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        stream=False,
    )
    logger.info(
        f"Translation request completed (tokens: {response.usage.total_tokens})"
    )
    return response.choices[0].message.content.strip()


def translate_file(
    client: OpenAI,
    source_lang: str,
    target_lang: str,
    source_file: str,
    target_file: str,
):
    """Handle translation for a single file pair"""
    logger.info(f"Translating {source_lang} -> {target_lang}")
    logger.info(f"Source: {source_file}")
    logger.info(f"Target: {target_file}")

    # Load source file
    try:
        with open(source_file, "r", encoding="utf-8") as f:
            source_data = json.load(f)
        logger.info(f"Loaded source file: {source_file}")
    except Exception as e:
        logger.error(f"Error loading source file: {e}")
        raise

    # Load or create target file
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            target_data = json.load(f)
        logger.info(f"Loaded target file: {target_file}")
    except FileNotFoundError:
        logger.warning(f"Target file not found, creating new: {target_file}")
        target_data = {}
    except Exception as e:
        logger.error(f"Error loading target file: {e}")
        raise

    # Compute translation needed
    diff_data = compute_diff(source_data, target_data)

    if not diff_data:
        logger.info("No new keys to translate. Target file is up to date.")
        return

    logger.info(f"Found {count_keys(diff_data)} new keys to translate")

    system_prompt = PROMPT.format(source_lang=source_lang, target_lang=target_lang)

    # Translate data
    try:
        translated_raw_data = translate(
            client, json.dumps(diff_data, ensure_ascii=False), system_prompt
        )
    except Exception as e:
        logger.error(f"API request failed: {e}")
        raise

    # Parse translated data
    try:
        translated_diff = json.loads(translated_raw_data)
    except Exception as e:
        logger.error(f"Failed to parse translation response: {e}")
        logger.error(f"Response content: {translated_raw_data}")
        raise

    # Merge translations with existing target data
    deep_merge(target_data, translated_diff)

    # Save translated JSON
    try:
        directory = os.path.dirname(target_file)
        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(target_data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(
            f"Translated and added {count_keys(translated_diff)} keys in {target_file}"
        )
    except Exception as e:
        logger.error(f"Error writing target file: {e}")
        raise


def process_config(
    config_path: str,
    client: OpenAI,
):
    """Process all translations defined in YAML config"""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        logger.info(f"Loaded configuration from {config_path}")
    except Exception as e:
        logger.error(f"Error loading config file: {e}")
        raise

    if config is None:
        raise ValueError(f"Config file {config_path} is empty or invalid")

    # Process each translation group
    for i, group in enumerate(config):
        if not group:
            continue

        # First language is source
        source_lang = next(iter(group))
        source_file = group[source_lang]

        logger.info(f"{'=' * 50}")
        logger.info(f"Processing group #{i + 1} with source: {source_lang}")
        logger.info(f"{'=' * 50}")

        # Process each target language
        for target_lang, target_file in group.items():
            if target_lang == source_lang:
                continue  # Skip source language

            translate_file(
                client=client,
                source_lang=source_lang,
                target_lang=target_lang,
                source_file=source_file,
                target_file=target_file,
            )


def run_from_config(
    parser: argparse.ArgumentParser,
    config_path: Optional[str],
    client: OpenAI,
):
    """Run translation from config file"""
    if config_path is None:
        config_path = find_config_file(os.getcwd())

    if config_path:
        logger.info(f"Using config file: {config_path}")
        logger.info("Starting translation")
        process_config(
            config_path=config_path,
            client=client,
        )
        logger.info("\nTranslation completed!")
    else:
        logger.error("No i18n.yaml found in current or parent directories")
        parser.print_help()
        exit(1)


def run_from_args(
    parser: argparse.ArgumentParser,
    client: OpenAI,
    source_lang: Optional[str],
    target_lang: Optional[str],
    source_file: Optional[str],
    target_file: Optional[str],
):
    """Run translation from command line arguments"""
    if all([source_lang, target_lang, source_file, target_file]):
        assert source_lang is not None
        assert target_lang is not None
        assert source_file is not None
        assert target_file is not None

        logger.info("Starting translation")
        translate_file(
            client=client,
            source_lang=source_lang,
            target_lang=target_lang,
            source_file=source_file,
            target_file=target_file,
        )
        logger.info("\nTranslation completed!")
    else:
        logger.error(
            "If you specify --source-lang, --target-lang, --source-file, and --target-file, all must be provided."
        )
        parser.print_help()
        exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Translate i18n JSON files using DeepSeek API"
    )
    parser.add_argument("--config", help="path to custom config file")
    parser.add_argument("--source-lang", help="Source language code (e.g., en)")
    parser.add_argument("--target-lang", help="Target language code (e.g., zh)")
    parser.add_argument("--source-file", help="Path to source JSON file")
    parser.add_argument("--target-file", help="Path to save translated JSON file")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Set debug level if verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    # Get API key from environment
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        logger.error("DEEPSEEK_API_KEY environment variable not set")
        raise ValueError("DEEPSEEK_API_KEY environment variable not set")

    # Initialize OpenAI client
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )

    if (
        any([args.source_lang, args.target_lang, args.source_file, args.target_file])
        and not args.config
    ):
        run_from_args(
            parser=parser,
            client=client,
            source_lang=args.source_lang,
            target_lang=args.target_lang,
            source_file=args.source_file,
            target_file=args.target_file,
        )
    else:
        run_from_config(
            parser=parser,
            config_path=args.config,
            client=client,
        )


if __name__ == "__main__":
    main()
