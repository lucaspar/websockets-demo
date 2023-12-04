"""Simulate a slow client that receives messages from the server."""

import asyncio
from typing import NoReturn

import websockets
from loguru import logger as log


async def slow_processing() -> NoReturn:
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
                    log.info(f"Received message with {len(message):,} chars")

                    # Simulate slow processing of each message, causing backpressure
                    await asyncio.sleep(1)
            except websockets.ConnectionClosed as error:
                log.error("Connection with server closed: ", error.code, error.reason)
                log.error(error)
                if retries > MAX_RETRIES:
                    should_retry = False
                retries += 1


asyncio.get_event_loop().run_until_complete(slow_processing())
