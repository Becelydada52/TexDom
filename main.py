from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Sequence

import uvicorn

from app.bot.runner import run_bot


def run_web_server(host: str = "0.0.0.0", port: int = 5000) -> None:
    uvicorn.run("app.web.app:app", host=host, port=port, reload=False)


def run_bot_server() -> None:
    asyncio.run(run_bot())
    

async def run_all_async(host: str, port: int) -> int:
    server = uvicorn.Server(
        uvicorn.Config(
            "app.web.app:app",
            host=host,
            port=port,
            reload=False,
        )
    )
    web_task = asyncio.create_task(server.serve(), name="web")
    bot_task = asyncio.create_task(run_bot(), name="bot")

    exit_code = 0
    try:
        done, pending = await asyncio.wait({web_task, bot_task}, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            if task.cancelled():
                continue
            exc = task.exception()
            if exc is not None:
                print(f"Task {task.get_name()} failed: {exc}", file=sys.stderr)
            else:
                print(f"Task {task.get_name()} stopped unexpectedly", file=sys.stderr)
            exit_code = 1
    finally:
        server.should_exit = True
        tasks = [web_task, bot_task]
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
    return exit_code


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Unified launcher for web and bot")
    parser.add_argument(
        "--mode",
        choices=("all", "web", "bot"),
        default="all",
        help="Run web, bot, or both processes",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Web host for mode=web/all")
    parser.add_argument("--port", type=int, default=5000, help="Web port for mode=web/all")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.mode == "web":
        run_web_server(args.host, args.port)
        return 0
    if args.mode == "bot":
        run_bot_server()
        return 0
    try:
        return asyncio.run(run_all_async(args.host, args.port))
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
