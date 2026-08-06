"""Development server entrypoint with a Windows-compatible asyncio event loop."""

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def main() -> None:
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=int(__import__("os").environ.get("API_PORT", "8000")),
        reload=True,
        loop="asyncio",
    )


if __name__ == "__main__":
    main()
