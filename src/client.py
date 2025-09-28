"""Simulate a slow client that receives messages from the server."""

import asyncio
import os
from pathlib import Path
from typing import NoReturn

import websockets
from loguru import logger as log
from rich import traceback

traceback.install(show_locals=True)

PROCESSING_DELAY_SEC = 0.2


async def process_message(msg: str | bytes) -> None:
    """Simulate slow processing of each message, causing backpressure"""
    _log_path = Path(__file__).parent / "received.jsonl"

    def _atomic_append(path: Path, data: bytes) -> None:
        fd = os.open(
            path=path,
            flags=os.O_WRONLY | os.O_APPEND | os.O_CREAT,
            mode=0o644,
        )
        try:
            os.write(fd, data)
        finally:
            os.close(fd=fd)

    if isinstance(msg, bytes):
        data = msg
    elif isinstance(msg, str):
        data = msg.encode("utf-8")
    else:
        raise TypeError(f"Expected str or bytes, got {type(msg)}")
    if not data.endswith(b"\n"):
        data += b"\n"
    await asyncio.to_thread(_atomic_append, _log_path, data)
    log.info(f"Appended {len(data):,} bytes to {_log_path.name}")

    # simulate slow processing
    await asyncio.sleep(PROCESSING_DELAY_SEC)


async def receive_messages() -> NoReturn | None:
    """Message processing loop."""
    ws_uri = "ws://localhost:8765"
    should_retry = True
    MAX_RETRIES = 3
    retries = 0
    while should_retry:
        if retries > 0:
            log.info(f"Retrying connection #{retries}...")
        async with websockets.connect(ws_uri) as ws:
            try:
                while True:
                    message = await ws.recv()
                    await process_message(msg=message)
            except websockets.ConnectionClosed as error:
                log.error("Connection with server closed: ", error.code, error.reason)
                log.error(error)
                if retries > MAX_RETRIES:
                    should_retry = False
                retries += 1


def main() -> None:
    asyncio.get_event_loop().run_until_complete(receive_messages())


if __name__ == "__main__":
    main()
