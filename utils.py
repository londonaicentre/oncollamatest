import os
import json
import re
from dotenv import load_dotenv
from openpipe import OpenAI
from oncollamaschemav3.prompt import create_system_prompt

"""
utils.py - supporting functions for backend operations (API, data processing)

Currently hard-coded to openpipe serverless deployment
Can refactor for additional LLM client compatibility (e.g. Bedrock)
"""

def load_env_vars():
    load_dotenv()
    api_key = os.getenv("OPENPIPE_API_KEY")
    model = os.getenv("OPENPIPE_MODEL")
    return api_key, model


def test_connection(api_key, model):
    try:
        client = OpenAI(openpipe={"api_key": api_key})
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


def call_openpipe_api(api_key, model, user_text):
    try:
        client = OpenAI(openpipe={"api_key": api_key})
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
