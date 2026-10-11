"""Create local, ignored OpenKB credentials from the existing LMS config.

Run from any directory: python docker/openkb/prepare.py
The generated files are only consumed locally by Docker Compose.
"""

import json
import re
import secrets
from pathlib import Path


def dotenv_value(value):
    value = str(value)
    if any(character in value for character in ("\n", "\r", "\x00")):
        raise ValueError("Environment values must be single-line strings")
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def main():
    docker_dir = Path(__file__).resolve().parent.parent
    config_path = docker_dir / "frappe-bench/sites/lms.localhost/site_config.json"
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    key = config.get("llm_api_key")
    base_url = config.get("llm_api_url")
    model = config.get("llm_api_model")
    if not all((key, base_url, model)):
        raise SystemExit("Configure llm_api_key, llm_api_url and llm_api_model in the LMS site first.")

    env_path = docker_dir / ".env.openkb"
    existing = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
    match = re.search(r"^OPENKB_API_TOKEN='([A-Za-z0-9_-]+)'$", existing, re.MULTILINE)
    token = match.group(1) if match else secrets.token_urlsafe(48)
    # Keep the model alias exactly as configured in LMS. 9Router combo names
    # such as "my-combo" must be sent unchanged; the "openai/" prefix makes
    # 9Router treat the alias as a model under the OpenAI provider instead.
    llm_model = model
    values = {
        "OPENKB_API_TOKEN": token,
        "LLM_API_KEY": key,
        "OPENAI_API_KEY": key,
        "OPENAI_API_BASE": base_url,
        "OPENAI_BASE_URL": base_url,
        "OPENKB_LLM_MODEL": llm_model,
    }
    env_path.write_text(
        "# Generated locally by openkb/prepare.py; keep out of Git.\n"
        + "".join(f"{name}={dotenv_value(value)}\n" for name, value in values.items()),
        encoding="utf-8",
    )
    (docker_dir / ".env.openkb-frappe").write_text(
        f"OPENKB_API_TOKEN={dotenv_value(token)}\n"
        "OPENKB_API_URL='http://openkb:7566'\n",
        encoding="utf-8",
    )
    print("Prepared local OpenKB environment files; secret values were not printed.")


if __name__ == "__main__":
    main()
