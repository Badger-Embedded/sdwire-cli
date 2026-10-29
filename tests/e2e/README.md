# End-to-end tests

These tests run the installed `sdwire` CLI as a subprocess, the way users do.
They assert only on the exit code, stdout, stderr and the device state. The
same tests run against simulated devices (umockdev) and real hardware.

## Running

The CLI under test is always `$SDWIRE_CMD`. Without it the e2e tests are skipped.

Simulated, in a container (same as CI):

```
podman build -t sdwire:build -f Containerfile .
podman build -f tests/e2e/Containerfile --build-arg BASE=localhost/sdwire:build -t sdwire-e2e .
podman run --rm sdwire-e2e                 # extra args go to pytest, e.g. -k sdwire3
```

Simulated, on a host with `umockdev`, `gir1.2-umockdev-1.0` and `python3-gi`
installed. The harness must run under `umockdev-wrapper`, and as a non-root
user so permission errors are real:

```
python3 -m venv /tmp/sut && /tmp/sut/bin/pip install .
python3 -m venv --system-site-packages /tmp/harness
UV_PROJECT_ENVIRONMENT=/tmp/harness uv sync --locked --only-group e2e --no-install-project
SDWIRE_CMD=/tmp/sut/bin/sdwire umockdev-wrapper /tmp/harness/bin/pytest tests/e2e
```

Real hardware: tests whose devices are not attached are skipped. Tests that
overwrite the SD card also need `--hw-allow-write`.

```
SDWIRE_CMD=sdwire pytest tests/e2e --backend=hw [--hw-allow-write]
```

Useful options:

- `-m "not slow"` skips the tests that wait for the CLI's 5 s timeout.
- `--snapshot-update` refreshes `tests/__snapshots__` after an intended help text change.

## Layout

```
conftest.py      --backend, SDWIRE_CMD, run_sdwire/run_sh/switch and rig fixtures
framework/       backend-agnostic Device/DeviceSpec/Capabilities, registry, rig
  sim/           umockdev testbed, SimUsbDevice (usbdevfs ioctls -> hooks),
                 SimBlockDevice, SimSdCard
  hw/            discovery of attached devices, sysfs oracles
devices/<kind>/  one package per hardware variant: spec.py, sim.py, hw.py and
                 tests that only apply to that variant
tests/           generic tests, parametrized over every registered variant
```

Tests get devices from the `rig` fixture: `rig.add("sdwire3")` builds a
simulated device, or claims an attached one on hardware. Options such as
`rig.add(kind, card=None)` or fault knobs only exist in simulation, so the
hardware backend skips those tests.

## Adding hardware

Copy `devices/_template/` and follow the checklist in its `spec.py`. The
generic tests pick up the new variant automatically. They derive the
expected outcomes from its `Capabilities`.

## Simulation notes

- The models are checked against real hardware only through the `hw` backend.
  Keep the models in `devices/<kind>/sim.py` small, and document what they
  leave out.
- umockdev does not report when a usbfs handle is closed, so the SDWire3 model
  suspends as soon as the driver is detached with `power/control=auto`.
- Struct layouts in `framework/sim/usb.py` assume a 64-bit host.
