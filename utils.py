import os
import json
import re
from dotenv import load_dotenv
from openpipe import OpenAI
from oncollamaschemav3.prompt import create_system_prompt

"""
utils.py - supporting functions for backend operations (API, data processing)
"""

def load_env_vars():
    load_dotenv()
    api_key = os.getenv("API_KEY")
    model = os.getenv("MODEL")
    base_url = os.getenv("BASE_URL", None)
    return api_key, model, base_url

def get_client(api_key, base_url=None):
    return OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key, openpipe={"api_key": api_key})

def test_connection(api_key, model, base_url=None):
    try:
        client = get_client(api_key, base_url)
        client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=10,
            temperature=0
        )
        return True, "Connected"
    except Exception as e:
        return False, f"Connection failed: {e}"


def extract_output_json(text):
    """
    Extract JSON from <output> tags
    """
    pattern = r'<output>(.*?)</output>'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
        try:
            # parse, reformat
            parsed = json.loads(json_str)
            return json.dumps(parsed, indent=4)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON: {e}\n\nRaw content:\n{json_str}"
    return text  # or return original


def call_openpipe_api(api_key, model, user_text, base_url=None):
    try:
        client = get_client(api_key, base_url)
        system_prompt = create_system_prompt('infer_prompt.txt')

        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            max_tokens=8000,
            temperature=0
        )

        response_text = completion.choices[0].message.content
        formatted_json = extract_output_json(response_text)

        return True, formatted_json

    except Exception as e:
        return False, f"API Error: {e}"
