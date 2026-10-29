"""Rig backed by the SDWires attached to this machine."""

import os

import pytest

from e2e.framework import registry
from e2e.framework.device import HwDevice
from e2e.framework.rig import Rig


class HwRig(Rig):
    backend = "hw"

    def __init__(self) -> None:
        super().__init__()
        self.attached: dict[str, list[HwDevice]] = {
            kind: registry.backend_module(kind, "hw").discover()
            for kind in registry.kinds()
        }

    @property
    def env(self) -> dict[str, str]:
        return dict(os.environ)

    def add(self, kind: str, **options) -> HwDevice:
        if options:
            pytest.skip(f"needs a simulated {kind} ({', '.join(options)})")
        for device in self.attached[kind]:
            if device not in self.devices:
                self.devices.append(device)
                return device
        pytest.skip(f"needs {self._count(kind) + 1} attached {kind}")

    def add_unrelated(self) -> None:
        """Real machines bring their own unrelated USB devices."""

    def require_exact(self) -> None:
        total = sum(len(devices) for devices in self.attached.values())
        if total != len(self.devices):
            pytest.skip(f"needs exactly {self.devices} attached")

    def _count(self, kind: str) -> int:
        return sum(device.spec.kind == kind for device in self.devices)
