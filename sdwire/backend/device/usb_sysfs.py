"""Read USB device information from Linux sysfs.

Opening a USB device through libusb resumes it from runtime suspend. SDWire3
only hands the SD card to the target while it is suspended, so anything that
just queries information must go through sysfs instead.
"""

import glob
import os

SYSFS_USB_DEVICES = "/sys/bus/usb/devices"


class UsbSysfs:
    def __init__(self, bus: int | None, port_numbers, root: str = SYSFS_USB_DEVICES):
        self.path: str | None = None
        if bus is not None and port_numbers:
            name = f"{bus}-{'.'.join(map(str, port_numbers))}"
            self.path = os.path.join(root, name)

    @classmethod
    def for_device(cls, device, root: str = SYSFS_USB_DEVICES) -> "UsbSysfs":
        return cls(
            getattr(device, "bus", None), getattr(device, "port_numbers", None), root
        )

    @property
    def available(self) -> bool:
        return self.path is not None and os.path.isdir(self.path)

    def attr(self, name: str) -> str | None:
        if not self.available:
            return None
        try:
            with open(os.path.join(self.path, name)) as f:
                return f.read().strip()
        except OSError:
            return None

    def interface_driver_bound(self, interface: int = 0) -> bool | None:
        """Return whether a kernel driver is bound to the interface, None if unknown."""
        if not self.available:
            return None
        name = os.path.basename(self.path)
        matches = glob.glob(os.path.join(self.path, f"{name}:*.{interface}"))
        if not matches:
            return None
        return os.path.exists(os.path.join(matches[0], "driver"))
