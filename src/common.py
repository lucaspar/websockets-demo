"""Common functions for server and client."""

import websockets
from loguru import logger
from tqdm.auto import tqdm


def configure_tqdm_logger() -> None:
    """Configure the logger to work well with tqdm progress bars."""
    logger.remove()
    logger.add(tqdm.write)  # pyright: ignore[reportArgumentType]
    logger_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: ^7}</level> | <level>{message}</level>"
    logger.configure(
        handlers=[
            dict(
                sink=lambda msg: tqdm.write(msg, end=""),
                format=logger_format,
                colorize=True,
            )
        ]
    )


def get_progress_bar(
    desc: str = "Items",
    total: int | None = None,
    unit: str = "it",
    **kwargs,
) -> tqdm:
    """Get a pre-configured tqdm progress bar."""
    defaults = {
        "colour": "green",
        "desc": desc,
        "maxinterval": 10.0,
        "mininterval": 0.5,
        "ncols": 80,
        "smoothing": 0.1,
        "total": total,
        "unit_divisor": 1_000,
        "unit_scale": True,
        "unit": unit,
    }
    return tqdm(**{**defaults, **kwargs})


def show_ws_properties(
    ws: websockets.WebSocketCommonProtocol,
) -> None:
    """Display WebSocket connection properties."""
    props = {
        "Local address": f"{ws.local_address[0]}:{ws.local_address[1]}",
        "Remote address": f"{ws.remote_address[0]}:{ws.remote_address[1]}",
        "Max size": ws.max_size,
        "Max queue": ws.max_queue,
        "Read limit": ws.read_limit,
        "Write limit": ws.write_limit,
    }
    print("WebSocket connection properties:")
    for key, value in props.items():
        if isinstance(value, int):
            value = f"{value:>9,}"
        if isinstance(value, float):
            value = f"{value:.3f}"
        print(f"  {key:>15} | {value}")


configure_tqdm_logger()
