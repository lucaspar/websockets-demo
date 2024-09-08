# Websocket Demos

Install dependencies:

```bash
uv sync
```

## Increased Backpressure Demo

This demonstrates an increase in the backpressure of a websocket connection by sending messages faster than they can be processed.

Eventually the connection is closed with either one of these generic errors:

+ A `1006` [error code](https://www.rfc-editor.org/rfc/rfc6455#section-7.4.1) on the server side (connection was closed abnormally) and the same on the client side.

+ A `1011` error code (internal error). The client fails immediately after the connection is closed.

## Observations

### Server state / lost messages

Even though the underlying TCP guarantees the delivery of the messages, that does not mean the client has a chance to process all messages received in this demo. When the connection is timed out, the client drops remaining messages in the buffer, even though they are marked as delivered.

### Execution

```bash
# Start the server
uv run server.py
```

```bash
# Start the client
uv run client.py
```

### Output

Server

```bash
#...
2023-12-04 10:03:37.557 | INFO     | __main__:echo:26 - Sent message #1304
2023-12-04 10:03:37.581 | INFO     | __main__:echo:26 - Sent message #1305
2023-12-04 10:03:37.604 | INFO     | __main__:echo:26 - Sent message #1306
2023-12-04 10:04:05.961 | ERROR    | __main__:echo:32 - Connection with client closed:
2023-12-04 10:04:05.961 | ERROR    | __main__:echo:33 - no close frame received or sent
```

Client

```bash
#...
2023-12-04 10:04:15.039 | INFO     | __main__:slow_processing:16 - Received message with 9,858 chars
2023-12-04 10:04:16.041 | INFO     | __main__:slow_processing:16 - Received message with 10,303 chars
2023-12-04 10:04:17.042 | INFO     | __main__:slow_processing:16 - Received message with 10,370 chars
2023-12-04 10:04:18.043 | ERROR    | __main__:slow_processing:21 - Connection with server closed:
2023-12-04 10:04:18.044 | ERROR    | __main__:slow_processing:22 - sent 1011 (internal error) keepalive ping timeout; no close frame received
```
