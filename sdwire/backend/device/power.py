"""Linux USB runtime power-management helpers for SDWire3.

The SDWire3 RTS5306E controller hands the SD card to the target side only when
the USB device is runtime-suspended, which requires ``power/control == auto``.
"""

import logging
import os
import time

log = logging.getLogger(__name__)

SYSFS_USB_DEVICES = "/sys/bus/usb/devices"


class PowerManagementError(RuntimeError):
    """Raised when the device power state cannot be configured or verified."""


class UsbPower:
    def __init__(
        self,
        bus: int | None,
        port_numbers,
        root: str = SYSFS_USB_DEVICES,
    ):
        self.path: str | None = None
        if bus is not None and port_numbers:
            name = f"{bus}-{'.'.join(map(str, port_numbers))}"
            self.path = os.path.join(root, name)

    @property
    def available(self) -> bool:
        return self.path is not None and os.path.isdir(os.path.join(self.path, "power"))

    def _file(self, name: str) -> str:
        return os.path.join(self.path or "", "power", name)

    def _read(self, name: str) -> str | None:
        try:
            with open(self._file(name)) as f:
                return f.read().strip()
        except OSError:
            return None

    def _write(self, name: str, value: str) -> None:
        try:
            with open(self._file(name), "w") as f:
                f.write(value)
        except PermissionError as e:
            raise PowerManagementError(
                f"permission denied writing '{value}' to {self._file(name)}; "
                "run as root or install the udev rule from the udev/ directory"
            ) from e
        except OSError as e:
            raise PowerManagementError(
                f"failed to write '{value}' to {self._file(name)}: {e}"
            ) from e

    @property
    def control(self) -> str | None:
        return self._read("control")

    @property
    def runtime_status(self) -> str | None:
        return self._read("runtime_status")

    def enable_autosuspend(self) -> None:
        """Set autosuspend delay to 0 and power/control to auto."""
        if not self.available:
            raise PowerManagementError(
                "cannot locate the sysfs power directory of the SDWire3 device"
            )
        if self._read("autosuspend_delay_ms") != "0":
            self._write("autosuspend_delay_ms", "0")
        if self.control != "auto":
            self._write("control", "auto")

    def wait_for_status(self, expected: str, timeout: float = 5.0) -> bool:
        deadline = time.monotonic() + timeout
        while True:
            if self.runtime_status == expected:
                return True
            if time.monotonic() >= deadline:
                return False
            time.sleep(0.1)
