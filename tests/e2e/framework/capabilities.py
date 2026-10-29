"""What a hardware variant can do; generic tests derive expected outcomes from it."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Capabilities:
    # `sdwire state` reports Host/Target instead of failing
    supports_state: bool
    # `sdwire switch off` disconnects the card from both sides
    supports_off: bool
    # switching to target relies on USB runtime suspend (power/* in sysfs)
    needs_runtime_pm: bool
    # how the switch is driven: unbinding the storage driver or FTDI CBUS pins
    control_path: Literal["usb-driver", "ftdi-cbus"]
    # where the card reader lives: the controlled device or a sibling on a hub
    storage_topology: Literal["same-device", "sibling-on-hub"]
    # the block device disappears in target mode and reappears on host
    reenumerates_on_host: bool
    # typical time until the block device is usable after `switch host`
    host_settle_s: float
