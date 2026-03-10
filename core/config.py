import json
import os
from dotenv import load_dotenv

load_dotenv()

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "config.json")

_DEFAULT_CONFIG = {
    "groq_api_key": os.getenv("GROQ_API_KEY", ""),
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
}


def load_config() -> dict:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Merge with defaults for any missing keys
        result = dict(_DEFAULT_CONFIG)
        result.update(data)
        return result
    except Exception:
        return dict(_DEFAULT_CONFIG)


def save_config(config: dict):
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception:
        pass
