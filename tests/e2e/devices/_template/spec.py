"""Template for a new hardware variant. Copy this package to get started.

Adding a device:

1. Copy `devices/_template/` to `devices/<kind>/` (a package name without a
   leading underscore, matching the backend module
   `sdwire/backend/device/<kind>.py`) and add an empty `__init__.py`.
2. spec.py: set SPEC.kind to the package name and fill in the ids, the
   capabilities and the `sdwire list` product-info format.
3. sim.py: model the device on top of SimUsbDevice and SimBlockDevice. Only
   the hooks that the device's switching mechanism uses need overriding.
4. hw.py: find attached devices through sysfs and report the card side and the
   block device without using the CLI.
5. Run the suite. The generic tests in tests/ now run for the new kind, with
   expectations derived from the capabilities. Put tests for behaviour only
   this device has (fault paths, special sysfs knobs) next to the model as
   `devices/<kind>/test_*.py`.
6. Optionally keep a `umockdev-record` of the real device under
   `devices/<kind>/recorded/` to compare the generated sysfs against.
"""

from e2e.framework.capabilities import Capabilities
from e2e.framework.device import DeviceSpec

SPEC = DeviceSpec(
    kind="_template",
    vid=0x1234,
    pid=0x5678,
    capabilities=Capabilities(
        supports_state=True,
        supports_off=False,
        needs_runtime_pm=False,
        control_path="usb-driver",
        storage_topology="same-device",
        reenumerates_on_host=False,
        host_settle_s=1.0,
    ),
    # formatted with vid, pid, product and manufacturer
    list_info="[{vid:04x}::{pid:04x}]",
)
