"""Simulate a server that sends messages faster than they can be processed."""

import asyncio
import datetime
import json
import math
import signal

import websockets
from loguru import logger as log
from loremipsum import generate_paragraph
from rich import traceback

from . import common

traceback.install(show_locals=True)


SERVER_MSG_DELAY_SEC = 0.01
SEND_MSGS_PERIOD_SEC = 5
MESSAGES_TO_SEND: int = math.ceil(SEND_MSGS_PERIOD_SEC / SERVER_MSG_DELAY_SEC)


def json_lorem_ipsum() -> str:
    """Generate a random JSON message."""

    message = generate_paragraph()[2]
    generated_timestamp = datetime.datetime.now(tz=datetime.UTC).isoformat()
    return json.dumps(
        {
            "timestamp": generated_timestamp,
            "message": message,
        }
    )


async def send_message_stream(ws: websockets.WebSocketServerProtocol) -> None:
    log.info("Client connected!")
    sent_count = 0
    # send messages for N seconds
    prog = common.get_progress_bar(
        desc="Sent messages",
        total=MESSAGES_TO_SEND,
        unit=" msg",
    )
    common.show_ws_properties(ws)
    try:
        while True:
            if sent_count >= MESSAGES_TO_SEND:
                log.info(
                    f"Sent {MESSAGES_TO_SEND} messages, leaving message sending loop."
                )
                break
            message = json_lorem_ipsum()
            # send messages faster than they can be processed to simulate backpressure
            await asyncio.sleep(SERVER_MSG_DELAY_SEC)
            await ws.send(message)
            sent_count += 1
            prog.update(1)
            if (sent_count + 1) % 10 == 0:
                prog.set_description(f"Sent {sent_count + 1:,} messages")
    except websockets.ConnectionClosed as error:
        log.error(f"Connection closed: {error.code=}, {error.reason=}")
        log.error(error)
    finally:
        prog.close()
        log.info("Waiting for buffer to drain...")
        await ws.drain()
        log.info("Buffer drained, leaving message sending loop.")
        log.info("Message sending task terminated.")


async def run_server() -> None:
    async with websockets.serve(
        ws_handler=send_message_stream,
        host="localhost",
        port=8765,
        write_limit=2**21,  # 2 MiB high water mark for outgoing messages
        max_size=2**16,  # 64 KiB size of items in queue
        max_queue=2**3,  # 8 items in outgoing queue
        ping_timeout=None,  # keep idle connections open to support large latency spikes
    ) as server:
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGTERM, server.close)
        loop.add_signal_handler(signal.SIGINT, server.close)
        log.info("Server started, waiting for clients to connect...")
        await server.wait_closed()


def main() -> None:
    log.info("Starting server...")
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        log.info("Server stopped by user.")
        raise


if __name__ == "__main__":
    main()
