"""SDWireC: a USB hub with an FTDI FT232R, whose CBUS pins drive the SD mux,
and a card reader as siblings. It is detected by its "sd-wire" product string."""

from e2e.framework.capabilities import Capabilities
from e2e.framework.device import DeviceSpec

SPEC = DeviceSpec(
    kind="sdwirec",
    vid=0x04E8,
    pid=0x6001,
    capabilities=Capabilities(
        supports_state=False,
        supports_off=False,
        needs_runtime_pm=False,
        control_path="ftdi-cbus",
        storage_topology="sibling-on-hub",
        reenumerates_on_host=False,
        host_settle_s=1.0,
    ),
    list_info="[{product}::{manufacturer}]",
)

PRODUCT = "sd-wire"
