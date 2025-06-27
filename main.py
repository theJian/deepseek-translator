import os
import json
import argparse
from openai import OpenAI


def translate_text(client, text: str, source_lang: str, target_lang: str) -> str:
    """
    Translate text using DeepSeek API
    """
    print(f"Translating from {source_lang} to {target_lang}: {text}")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": f"You are a professional translator that translates from {source_lang} to {target_lang}.",
            },
            {"role": "user", "content": text},
        ],
        temperature=0.2,
        stream=False,
    )
    return response.choices[0].message.content.strip()


def translate_json_data(client, data, source_lang: str, target_lang: str):
    """
    Recursively translate JSON data
    """
    if isinstance(data, dict):
        return {
            key: translate_json_data(client, value, source_lang, target_lang)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [
            translate_json_data(client, item, source_lang, target_lang) for item in data
        ]
    elif isinstance(data, str):
        return translate_text(client, data, source_lang, target_lang)
    return data


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

    args = parser.parse_args()

    # Get API key from environment
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY environment variable not set")

    # Initialize OpenAI client
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )

    # Load source JSON
    try:
        with open(args.source_file, "r", encoding="utf-8") as f:
            source_data = json.load(f)
    except Exception as e:
        raise SystemExit(f"Error loading source file: {e}")

    # Translate data
    translated_data = translate_json_data(
        client, source_data, args.source_lang, args.target_lang
    )

    # Save translated JSON
    try:
        with open(args.target_file, "w", encoding="utf-8") as f:
            json.dump(translated_data, f, ensure_ascii=False, indent=2)
        print(f"Successfully translated to {args.target_file}")
    except Exception as e:
        raise SystemExit(f"Error saving target file: {e}")


if __name__ == "__main__":
    main()
