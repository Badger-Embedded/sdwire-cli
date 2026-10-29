"""Checks on real hardware that read sysfs directly instead of trusting the CLI."""

import glob
import os

SYSFS_USB_DEVICES = "/sys/bus/usb/devices"


def read(path: str) -> str | None:
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return None


def usb_devices(vid: int, pid: int) -> list[str]:
    """Sysfs paths of USB devices (not interfaces) with the given ids."""
    return sorted(
        path
        for path in glob.glob(f"{SYSFS_USB_DEVICES}/*")
        if ":" not in os.path.basename(path)
        and read(f"{path}/idVendor") == f"{vid:04x}"
        and read(f"{path}/idProduct") == f"{pid:04x}"
    )


def port_path(syspath: str) -> str:
    """Port path of a USB device, e.g. '1.2' for /sys/bus/usb/devices/3-1.2."""
    return os.path.basename(syspath).split("-", 1)[1]


def usable_block_dev(usb_syspath: str) -> str | None:
    """/dev path of the disk below a USB device, if it has a medium."""
    for block in sorted(glob.glob(f"{usb_syspath}/*:*/host*/target*/*/block/*")):
        size = read(f"{block}/size")
        if size and size.isdigit() and int(size) > 0:
            return f"/dev/{os.path.basename(block)}"
    return None
