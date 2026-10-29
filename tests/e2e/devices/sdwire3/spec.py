"""SDWire3: a Realtek RTS5306E card reader that hands the card to the target
while it is runtime-suspended (driver unbound + power/control=auto)."""

from e2e.framework.capabilities import Capabilities
from e2e.framework.device import DeviceSpec

SPEC = DeviceSpec(
    kind="sdwire3",
    vid=0x0BDA,
    pid=0x0316,
    capabilities=Capabilities(
        supports_state=True,
        supports_off=False,
        needs_runtime_pm=True,
        control_path="usb-driver",
        storage_topology="same-device",
        reenumerates_on_host=True,
        host_settle_s=2.0,
    ),
    list_info="[{vid:04x}::{pid:04x}]",
)
