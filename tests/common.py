from dataclasses import dataclass
import time
import logging


POLL_INTERVAL = 0.1  # 100 ms


@dataclass
class PLCSettings:
    ip: str
    netid: str
    netport: int
    serverport: int
    clientport: int
    

def wait_until(condition_fn, timeout_sec, description):
    """
    Wait until a condition is true or timeout occurs.

    Args:
        condition_fn: Callable that returns a boolean
        timeout_sec: Timeout in seconds
        description: Description of what we're waiting for (for logging)

    Returns:
        True if condition was met, False on timeout
    """
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        if condition_fn():
            return True
        time.sleep(POLL_INTERVAL)

    logging.error(f"TIMEOUT waiting for: {description}")
    return False
