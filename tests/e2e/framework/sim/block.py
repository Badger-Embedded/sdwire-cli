"""SCSI disk (e.g. /dev/sda) below a simulated USB mass-storage interface."""

import os

from e2e.framework.sim.sdcard import SimSdCard
from e2e.framework.sim.testbed import Testbed


class SimBlockDevice:
    def __init__(
        self, testbed: Testbed, interface: str, card: SimSdCard | None
    ) -> None:
        self.testbed = testbed
        self.interface = interface
        self.card = card
        index = testbed.next_disk()
        self.name = "sd" + chr(ord("a") + index)
        self.majmin = f"8:{index * 16}"
        self.medium = True
        self._host: str | None = None

    @property
    def path(self) -> str:
        return f"/dev/{self.name}"

    @property
    def attached(self) -> bool:
        return self._host is not None

    @property
    def usable(self) -> bool:
        return self.attached and self._size() > 0

    def attach(self) -> None:
        """Bind the SCSI disk, as usb-storage does when the driver binds."""
        n = self.testbed.next_scsi_host()
        self._host = f"{self.interface}/host{n}"
        scsi = f"{self._host}/target{n}:0:0/{n}:0:0:0"
        ro = int(bool(self.card and self.card.write_protected))
        self.testbed.add(
            f"P: {scsi.removeprefix('/sys')}\n"
            "E: SUBSYSTEM=scsi\nE: DEVTYPE=scsi_device\n"
            "A: state=running\\n\nA: vendor=Generic \\n\nA: model=SD Card Reader  \\n\n\n"
            f"P: {scsi.removeprefix('/sys')}/block/{self.name}\n"
            f"N: {self.name}\n"
            "E: SUBSYSTEM=block\nE: DEVTYPE=disk\n"
            f"E: DEVNAME={self.path}\n"
            f"A: dev={self.majmin}\\n\nA: size={self._size()}\\n\nA: ro={ro}\\n\n"
            "A: removable=1\\n\n"
            f"L: device=../../../{n}:0:0:0\n\n"
        )
        if self.card:
            # the node is a hard link to the image, so data survives detaching
            node = self.testbed.real(self.path)
            os.unlink(node)
            os.link(self.card.materialize(self.testbed.cards_dir), node)
            # umockdev reports sticky regular files below /dev as block devices
            os.chmod(node, 0o1444 if ro else 0o1644)

    def detach(self) -> None:
        if self._host:
            self.testbed.remove(self._host)
            self._host = None

    def set_medium(self, present: bool) -> None:
        self.medium = present
        if self._host:
            self.testbed.write(f"/sys/class/block/{self.name}/size", str(self._size()))

    def _size(self) -> int:
        return self.card.sectors if self.card and self.medium else 0
