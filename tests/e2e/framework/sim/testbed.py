"""Thin wrapper around UMockdev.Testbed.

The harness process must run under `umockdev-wrapper` (LD_PRELOAD), and so do
the CLI subprocesses: they inherit the preload and get `UMOCKDEV_DIR` from
`Testbed.env`. Harness-side file access goes through `real()` paths so it does
not depend on the preload.
"""

import itertools
import os
import shutil
import threading
import traceback

import gi

gi.require_version("UMockdev", "1.0")
from gi.repository import UMockdev  # noqa: E402

BUS = 1
HOST_CONTROLLER = "/sys/devices/pci0000:00/0000:00:14.0"
# directories holding symlinks into /sys/devices that must go when a device does
_LINK_DIRS = ("sys/block", "sys/class", "sys/bus", "sys/dev")


class Testbed:
    def __init__(self) -> None:
        if "umockdev-preload" not in os.environ.get("LD_PRELOAD", ""):
            raise RuntimeError("the sim backend must run under umockdev-wrapper")
        self._tb = UMockdev.Testbed.new()
        self.root = self._tb.get_root_dir()
        self.lock = threading.RLock()
        self.errors: list[str] = []
        self._devnums = itertools.count(1)
        self._scsi_hosts = itertools.count(0)
        self._disks = itertools.count(0)
        self._timers: list[threading.Timer] = []
        self.cards_dir = os.path.join(self.root, "cards")
        os.makedirs(self.cards_dir)

    @property
    def env(self) -> dict[str, str]:
        return dict(os.environ, UMOCKDEV_DIR=self.root)

    def real(self, path: str) -> str:
        """Map a /sys or /dev path to its location in the testbed."""
        return os.path.join(self.root, path.lstrip("/"))

    def next_devnum(self) -> int:
        return next(self._devnums)

    def next_scsi_host(self) -> int:
        return next(self._scsi_hosts)

    def next_disk(self) -> int:
        return next(self._disks)

    def add(self, record: str) -> None:
        """Add devices described in umockdev's record format."""
        self._tb.add_from_string(record)

    def remove(self, syspath: str) -> None:
        """Remove a device tree with its /dev nodes and /sys symlinks."""
        real = self.real(syspath)
        for dirpath, _, files in os.walk(real):
            if "uevent" in files:
                self._remove_node(os.path.join(dirpath, "uevent"))
        for top in _LINK_DIRS:
            for dirpath, dirnames, filenames in os.walk(self.real(top)):
                for name in dirnames + filenames:
                    link = os.path.join(dirpath, name)
                    if os.path.islink(link) and _is_within(
                        os.path.realpath(link), real
                    ):
                        os.unlink(link)
        shutil.rmtree(real)

    def _remove_node(self, uevent: str) -> None:
        with open(uevent) as f:
            props = dict(line.strip().split("=", 1) for line in f if "=" in line)
        name = props.get("DEVNAME")
        if name:
            for path in (f"dev/{name}", f"dev/.node/{name.replace('/', '_')}"):
                if os.path.lexists(self.real(path)):
                    os.unlink(self.real(path))

    def ensure_driver(self, name: str) -> str:
        path = f"/sys/bus/usb/drivers/{name}"
        os.makedirs(self.real(path), exist_ok=True)
        return path

    def read(self, path: str) -> str:
        with open(self.real(path)) as f:
            return f.read().strip()

    def write(self, path: str, value: str) -> None:
        with open(self.real(path), "w") as f:
            f.write(f"{value}\n")

    def attach_ioctl(self, devnode: str, handler: UMockdev.IoctlBase) -> None:
        self._tb.attach_ioctl(devnode, handler)

    def later(self, delay: float, fn) -> None:
        """Run fn after delay seconds, like the kernel finishing work asynchronously."""
        timer = threading.Timer(delay, self.guarded(fn))
        timer.daemon = True
        self._timers.append(timer)
        timer.start()

    def guarded(self, fn):
        """Wrap a model callback: serialize it and record exceptions for the test."""

        def run(*args):
            with self.lock:
                try:
                    return fn(*args)
                except Exception:
                    self.errors.append(traceback.format_exc())
                    raise

        return run

    def close(self) -> None:
        for timer in self._timers:
            timer.cancel()
        self._tb = None


def _is_within(path: str, directory: str) -> bool:
    return path == directory or path.startswith(directory + os.sep)
