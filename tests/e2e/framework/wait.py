import time


def wait_for(condition, timeout: float = 10.0, interval: float = 0.1):
    """Poll until condition() is truthy and return its value."""
    deadline = time.monotonic() + timeout
    while not (value := condition()):
        if time.monotonic() >= deadline:
            raise AssertionError(f"timed out after {timeout}s waiting for {condition}")
        time.sleep(interval)
    return value


def wait_for_side(device, side: str, timeout: float = 10.0) -> None:
    """Wait until the card is on `side`.

    On hardware the side is read from sysfs, which lags the switch: SDWire3
    takes a moment to suspend or re-enumerate, and an SDWireC reader reports
    the medium change only when the kernel next polls it (about every 2 s).
    """
    try:
        wait_for(lambda: device.card_side() == side, timeout)
    except AssertionError:
        raise AssertionError(
            f"{device}: card is on {device.card_side()} side, not {side}, "
            f"{timeout}s after switching"
        ) from None
