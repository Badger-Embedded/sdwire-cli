"""Registry of hardware variants.

Every package under `e2e/devices/` (except names starting with `_`) is one
variant. By convention it provides:

- `spec.py` with `SPEC: DeviceSpec`, where `SPEC.kind` equals the package name
- `sim.py` with `Device`, a `SimDevice` subclass
- `hw.py` with `discover() -> list[HwDevice]`
"""

import importlib
import pkgutil
from functools import cache
from types import ModuleType

from e2e import devices
from e2e.framework.device import DeviceSpec


@cache
def specs() -> dict[str, DeviceSpec]:
    found = {}
    for info in pkgutil.iter_modules(devices.__path__):
        if info.name.startswith("_") or not info.ispkg:
            continue
        spec = importlib.import_module(f"{devices.__name__}.{info.name}.spec").SPEC
        assert spec.kind == info.name, f"{info.name}: SPEC.kind must match the package"
        found[spec.kind] = spec
    return found


def kinds() -> list[str]:
    return sorted(specs())


def backend_module(kind: str, backend: str) -> ModuleType:
    """Return the `sim` or `hw` module of a variant."""
    return importlib.import_module(f"{devices.__name__}.{kind}.{backend}")
