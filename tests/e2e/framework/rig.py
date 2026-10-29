"""Where tests get devices from: a simulated testbed or the attached hardware."""

from abc import ABC, abstractmethod

from e2e.framework.device import Device


class Rig(ABC):
    backend: str

    def __init__(self) -> None:
        self.devices: list[Device] = []

    @property
    @abstractmethod
    def env(self) -> dict[str, str]:
        """Environment for CLI subprocesses."""

    @abstractmethod
    def add(self, kind: str, **options) -> Device:
        """Attach (sim) or claim (hw) a device of the given kind.

        `options` configure simulated devices (card, faults, strings). The
        hardware backend skips the test when options are given or no unclaimed
        device of that kind is attached.
        """

    @abstractmethod
    def add_unrelated(self) -> None:
        """Attach USB devices that are not SDWires (a hub and a USB stick)."""

    @abstractmethod
    def require_exact(self) -> None:
        """Skip unless exactly the added devices are attached (hw only)."""

    def close(self) -> None:
        pass
