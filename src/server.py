"""Simulate a server that sends messages faster than they can be processed."""

import asyncio
import datetime
import json
import time

import websockets
from loguru import logger as log
from loremipsum import generate_paragraph
from rich import traceback

traceback.install(show_locals=True)


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


async def echo(websocket) -> None:
    log.info("Client connected!")
    sent_count = 0
    messages_to_send = 20
    try:
        while True:
            if sent_count >= messages_to_send:
                log.info(f"Sent {messages_to_send} messages, closing connection.")
                await websocket.close()
                break
            message = json_lorem_ipsum()
            await websocket.send(message)
            if (sent_count + 1) % 10 == 0:
                log.info(f"Sent message #{sent_count + 1}")

            # Send messages faster than they can be processed to simulate backpressure
            time.sleep(0.02)
            sent_count += 1
    except websockets.ConnectionClosed as error:
        log.error("Connection with client closed: ", error.code, error.reason)
        log.error(error)


def main() -> None:
    log.info("Starting server...")
    start_server = websockets.serve(echo, "localhost", 8765)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    main()
