"""Start the pinned OpenKB API using the existing LMS model gateway."""

import os
from pathlib import Path

import uvicorn
import yaml


def main():
    if not os.environ.get("OPENKB_API_TOKEN"):
        raise SystemExit("Missing OPENKB_API_TOKEN. Run docker/openkb/prepare.py first.")
    if not os.environ.get("LLM_API_KEY"):
        raise SystemExit("Missing LLM_API_KEY. Run docker/openkb/prepare.py first.")

    runtime = Path("/data/runtime")
    runtime.mkdir(parents=True, exist_ok=True)
    config = {
        "model": os.environ.get("OPENKB_LLM_MODEL", "openai/my-combo"),
        "language": "vi",
        "pageindex_threshold": 20,
        "concurrency": 1,
        "parallel_tool_calls": False,
        "litellm": {"timeout": 180},
    }
    (runtime / "config.yaml").write_text(
        yaml.safe_dump(config, allow_unicode=True), encoding="utf-8"
    )
    os.chdir(runtime)
    from openkb.api import create_app
    from source_pages import router
    app = create_app()
    app.include_router(router)
    # Upstream mounts the Workbench at '/', which must follow extension routes.
    from starlette.routing import Mount
    app.router.routes.sort(key=lambda route: isinstance(route, Mount))
    uvicorn.run(app, host="0.0.0.0", port=7566)


if __name__ == "__main__":
    main()
