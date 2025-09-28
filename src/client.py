"""Simulate a slow client that receives messages from the server."""

import asyncio
import itertools
import os
import time
from pathlib import Path
from typing import NoReturn

import websockets
from loguru import logger as log
from rich import traceback
from tqdm.auto import tqdm

from . import common
from .server import MESSAGES_TO_SEND as messages_to_receive
from .server import SERVER_MSG_DELAY_SEC

traceback.install(show_locals=True)

# process messages slower than they are sent
PROCESSING_DELAY_SEC: float = max(SERVER_MSG_DELAY_SEC * 10, 0.02)


async def process_message(msg: str | bytes, prog: tqdm | None = None) -> None:
    """Simulate slow processing of each message, causing backpressure"""
    _log_path = Path(__file__).parent / "received.jsonl"

    def _atomic_append(path: Path, data: bytes) -> None:
        fd = os.open(
            path=path,
            flags=(
                os.O_WRONLY  # open for writing only
                | os.O_APPEND  # append to the end of the file
                | os.O_CREAT  # create file if it does not exist
                | os.O_NONBLOCK  # do not block
            ),
            mode=0o644,
        )
        if fd < 0:
            log.warning(f"Failed to open file {path} for appending.")
            return
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

    try:
        await asyncio.to_thread(_atomic_append, _log_path, data)
        # simulates slow processing
        if PROCESSING_DELAY_SEC > 0:
            await asyncio.sleep(PROCESSING_DELAY_SEC)
        if prog is not None:
            status = f"Processed {len(data):06,} bytes"
            prog.set_description(status)
            prog.update(1)
    except KeyboardInterrupt:
        log.info("Message processing interrupted by user.")
        raise


async def keepalive(
    websocket: websockets.WebSocketClientProtocol,
    ping_interval: float = 0.5,
) -> None:
    log.debug("Keepalive task started.")
    expiration_time = time.time()
    last_ping = expiration_time
    for ping in itertools.count():
        now = time.time()
        if now < expiration_time:
            time_left = expiration_time - now
            await asyncio.sleep(min(ping_interval, time_left))
        try:
            send_time = time.time()
            expiration_time = send_time + ping_interval
            pong_waiter = await websocket.ping()
            latency: int | float = await pong_waiter
            now = time.time()
            log.info(
                f"Ping {ping:>2}: {latency=:.3f}s | {now - last_ping:.3f}s since last one"
            )
            last_ping = now
            # this latency is expected to increase as messages pile up in the buffer
        except websockets.ConnectionClosed as error:
            if error.code == 1000:
                log.success("Connection closed normally by the server.")
            else:
                log.error(f"Connection closed: {error.code=}, {error.reason=}")
                log.warning("Stopping keepalive task.")
            break
    log.debug("Keepalive task terminated.")


async def process_messages(
    websocket: websockets.WebSocketClientProtocol,
) -> NoReturn | None:
    """Process incoming messages from the server."""
    log.info("Message processing task started.")
    prog = None
    try:
        prog = common.get_progress_bar(
            desc="Processing messages",
            total=messages_to_receive,
            unit="msg",
        )
        async for message in websocket:
            await process_message(message, prog=prog)
        log.success("Finished processing messages, server closed the connection.")
    except websockets.ConnectionClosed as error:
        if error.code == 1000:
            log.success("Connection closed normally by the server.")
        else:
            log.error("Connection closed: ", error.code, error.reason)
            log.error(error)
    except KeyboardInterrupt:
        log.info("Message processing interrupted by user.")
        raise
    finally:
        log.info("Message processing task terminated.")
        if prog is not None:
            messages_received = prog.n
            log.success(f"Received {messages_received:,} messages.")
            prog.close()


async def receive_messages() -> NoReturn | None:
    """Message processing loop."""
    host = "localhost"
    port = 8765
    ws_uri = f"ws://{host}:{port}"
    async with websockets.connect(
        ws_uri,
        ping_timeout=None,  # keep idle connections open to support large latency spikes
    ) as ws:
        common.show_ws_properties(ws)
        keepalive_task = asyncio.create_task(
            keepalive(ws),
            name="keepalive",
        )
        process_messages_task = asyncio.create_task(
            process_messages(ws),
            name="process_messages",
        )
        done, pending = await asyncio.wait(
            {keepalive_task, process_messages_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        # Since the message processing is slow, the keepalive task will finish earlier,
        # after the server closes the connection. But at that point there may still be
        # messages to process, so we wait for the message processing task to finish:
        for pending_task in pending:
            if pending_task is keepalive_task:
                log.info("Cancelling keepalive task.")
                pending_task.cancel()
            elif pending_task is process_messages_task:
                log.warning(f"Waiting {pending_task.get_name()} indefinitely")
                await pending_task
            else:
                TASK_TIMEOUT: int = 30
                log.warning(f"Waiting {pending_task.get_name()} up to {TASK_TIMEOUT}s")
                try:
                    await asyncio.wait_for(pending_task, timeout=TASK_TIMEOUT)
                except asyncio.TimeoutError:
                    log.error(
                        f"Timeout waiting for {pending_task.get_name()} to finish."
                    )
        for task in done:
            if task is process_messages_task:
                return task.result()
    return None


def main() -> None:
    """Run the client."""
    try:
        asyncio.run(receive_messages())
    except KeyboardInterrupt:
        log.info("Client stopped by user.")
        raise


if __name__ == "__main__":
    main()
