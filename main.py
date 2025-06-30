import os
import json
import argparse
from openai import OpenAI
from typing import Dict, Any
import logging

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


def main():
    parser = argparse.ArgumentParser(
        description="Translate i18n JSON files using DeepSeek API"
    )
    parser.add_argument(
        "--source-lang", required=True, help="Source language code (e.g., en)"
    )
    parser.add_argument(
        "--target-lang", required=True, help="Target language code (e.g., zh)"
    )
    parser.add_argument("--source-file", required=True, help="Path to source JSON file")
    parser.add_argument(
        "--target-file", required=True, help="Path to save translated JSON file"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Set debug level if verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    # Get API key from environment
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        logger.error("DEEPSEEK_API_TOKEN environment variable not set")
        raise ValueError("DEEPSEEK_API_KEY environment variable not set")

    # Initialize OpenAI client
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )

    # Load source and target files
    try:
        with open(args.source_file, "r", encoding="utf-8") as f:
            source_data = json.load(f)
        logger.info(f"Loaded source file: {args.source_file}")
    except Exception as e:
        logger.error(f"Error loading source file: {e}")
        raise

    try:
        with open(args.target_file, "r", encoding="utf-8") as f:
            target_data = json.load(f)
        logger.info(f"Loaded target file: {args.target_file}")
    except FileNotFoundError:
        logger.warning(f"Target file not found, creating new: {args.target_file}")
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

    system_prompt = PROMPT.format(
        source_lang=args.source_lang, target_lang=args.target_lang
    )

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
        with open(args.target_file, "w", encoding="utf-8") as f:
            json.dump(target_data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(
            f"Translation completed. Added {count_keys(translated_diff)} keys in {args.target_file}"
        )
    except Exception as e:
        logger.error(f"Error writing target file: {e}")
        raise


if __name__ == "__main__":
    main()
