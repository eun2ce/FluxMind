from __future__ import annotations

import uvicorn
from fluxmind.api.app import app
from fluxmind.platform import get_settings


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.api_port,
    )


if __name__ == "__main__":
    run()
