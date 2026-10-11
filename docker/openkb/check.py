"""Check the local OpenKB service without uploading documents or calling an LLM."""

import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path


def main():
    env_path = Path(__file__).resolve().parent.parent / ".env.openkb"
    match = re.search(
        r"^OPENKB_API_TOKEN='([A-Za-z0-9_-]+)'$",
        env_path.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    if not match:
        raise SystemExit("Run prepare.py before checking OpenKB")
    token = match.group(1)
    base = "http://127.0.0.1:7566"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def get(path, authenticated=False):
        headers = {"Authorization": f"Bearer {token}"} if authenticated else {}
        request = urllib.request.Request(base + path, headers=headers)
        try:
            with opener.open(request, timeout=5) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as error:
            return error.code, b""

    for attempt in range(30):
        try:
            status, body = get("/api/v1/meta", authenticated=True)
            break
        except (urllib.error.URLError, TimeoutError):
            if attempt == 29:
                raise SystemExit("OpenKB did not become reachable within 30 attempts")
            time.sleep(1)
    if status != 200:
        raise SystemExit(f"Authenticated metadata request failed: HTTP {status}")
    print(f"OpenKB API: OK; version={json.loads(body)['version']}")
    for path, expected in (("/", 200), ("/docs", 200), ("/api/v1/meta", 401)):
        status, _ = get(path)
        if status != expected:
            raise SystemExit(f"{path}: expected HTTP {expected}, got HTTP {status}")
        print(f"{path}: HTTP {status} (expected)")
    status, body = get("/openapi.json")
    if status != 200:
        raise SystemExit(f"OpenAPI schema failed: HTTP {status}")
    paths = json.loads(body)["paths"]
    for path in ("/api/v1/init", "/api/v1/add", "/api/v1/query", "/api/v1/chat", "/lms/v1/source-pages"):
        if path not in paths:
            raise SystemExit(f"Missing upstream endpoint: {path}")
    print("Upstream init/add/query/chat routes: present")


if __name__ == "__main__":
    main()
