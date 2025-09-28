# Websocket Demos

## Increased Backpressure Demo

This demonstrates an increase in the backpressure of a websocket connection that sends
messages faster than they can be processed. As the backlog increases, the latency of the
messages increases as well, up to a point the server stops sending them until the
buffers have more available space.

Despite the server waiting indefinitely for the client, this implementation does not
allow the connection to timeout. When all messages are sent, the connection may be
closed. The client keeps processing the remaining buffered messages after that happens.

https://github.com/user-attachments/assets/6d9c2876-d832-4aaf-b16b-9fc196c3d59b

## Error codes

+ A `1006` error code on the server side (connection was closed abnormally) and the same
    on the client side.

+ A `1011` error code (internal error). The client fails immediately after the
    connection is closed.

[More error codes](https://www.rfc-editor.org/rfc/rfc6455#section-7.4.1).

## Observations

### Server state / lost messages

Even though the underlying TCP guarantees the delivery of the messages, that does not
mean the client has a chance to process all messages received in this demo. When the
connection is timed out, the client drops remaining messages in the buffer, even though
they are marked as delivered.

### Execution

```bash
# Start the server
uv run -m src.server
```

```bash
# Start the client
uv run -m src.client
```
