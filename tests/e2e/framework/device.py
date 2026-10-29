"""Device abstractions shared by the simulated and the real-hardware backend.

Tests only talk to `Device`: they read the serial the CLI should report and
ask for the ground truth (`card_side`, `block_dev`) to compare the CLI against.
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from e2e.framework.capabilities import Capabilities
from e2e.framework.sim.sdcard import SimSdCard

if TYPE_CHECKING:
    from e2e.framework.sim.testbed import Testbed

CardSide = Literal["host", "target"]
# SimDevice gets a default SD card unless the test passes card=None
DEFAULT_CARD = object()


@dataclass(frozen=True)
class DeviceSpec:
    kind: str
    vid: int
    pid: int
    capabilities: Capabilities
    # product info column of `sdwire list`, formatted with the device's
    # vid, pid, product and manufacturer
    list_info: str


class Device(ABC):
    spec: DeviceSpec

    @property
    @abstractmethod
    def serial(self) -> str:
        """Serial as printed by the CLI and accepted by `--serial`."""

    @property
    @abstractmethod
    def manufacturer(self) -> str: ...

    @property
    @abstractmethod
    def product(self) -> str: ...

    @abstractmethod
    def card_side(self) -> CardSide:
        """Which side the SD card is connected to, read independently of the CLI."""

    @abstractmethod
    def block_dev(self) -> str | None:
        """Path of the block device that has the card as medium, if any."""

    def list_line(self, block_dev: str | None) -> str:
        """Expected `sdwire list` line for this device."""
        info = self.spec.list_info.format(
            vid=self.spec.vid,
            pid=self.spec.pid,
            product=self.product,
            manufacturer=self.manufacturer,
        )
        return f"{self.serial:<30}{info}\t\t{block_dev or 'None'}"

    def __repr__(self) -> str:
        return f"<{self.spec.kind} {self.serial}>"


class SimDevice(Device):
    """A simulated variant. `sim.py` of a device package subclasses this as `Device`."""

    @dataclass
    class Faults:
        """Device-specific fault knobs; subclasses replace this dataclass."""

    def __init__(
        self, card: SimSdCard | None | object = DEFAULT_CARD, **faults
    ) -> None:
        self.card = SimSdCard() if card is DEFAULT_CARD else card
        self.faults = self.Faults(**faults)

    @abstractmethod
    def build(self, testbed: "Testbed", parent: str, port: str) -> None:
        """Create the sysfs/dev nodes below the hub at `parent` on `port`."""


class HwDevice(Device):
    """A real device found through sysfs. `hw.py` of a device package subclasses this."""

    def __init__(self, syspath: str) -> None:
        self.syspath = syspath

    def attr(self, name: str) -> str | None:
        try:
            with open(os.path.join(self.syspath, name)) as f:
                return f.read().strip()
        except OSError:
            return None

    @property
    def manufacturer(self) -> str:
        return self.attr("manufacturer") or ""

    @property
    def product(self) -> str:
        return self.attr("product") or ""
