"""Simulate a server that sends messages faster than they can be processed."""

import asyncio
import json
import time

import websockets
from loguru import logger as log
from loremipsum import generate_paragraph


def json_lorem_ipsum():
    """Generate a random JSON message."""

    message = generate_paragraph()[2]
    return json.dumps({"message": message})


async def echo(websocket) -> None:
    log.info("Client connected!")
    sent_count = 0
    try:
        while True:
            message = json_lorem_ipsum()
            await websocket.send(message)
            log.info(f"Sent message #{sent_count + 1}")

            # Send messages faster than they can be processed to simulate backpressure
            time.sleep(0.02)
            sent_count += 1
    except websockets.ConnectionClosed as error:
        log.error("Connection with client closed: ", error.code, error.reason)
        log.error(error)


log.info("Starting server...")
start_server = websockets.serve(echo, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
