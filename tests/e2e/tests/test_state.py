"""`sdwire state`, expected outcomes come from Capabilities.supports_state."""

import pytest


def state_output(serial: str, state: str) -> str:
    return f"{'Serial':<30}\tState\n{serial:<30}\t{state}\n"


@pytest.mark.parametrize("side,state", [("host", "Host"), ("target", "Target")])
def test_state(rig, kind, run_sdwire, switch, side, state):
    device = rig.add(kind)
    switch(device, side)
    result = run_sdwire("state", "-s", device.serial)
    if device.spec.capabilities.supports_state:
        assert result.returncode == 0, result
        assert result.stdout == state_output(device.serial, state)
        assert result.stderr == ""
    else:
        assert result.returncode == 1
        assert "don't have state functionality" in result.stdout


def test_state_without_serial_uses_only_device(rig, kind, run_sdwire):
    device = rig.add(kind)
    rig.require_exact()
    with_serial = run_sdwire("state", "-s", device.serial)
    without = run_sdwire("state")
    assert (without.returncode, without.stdout) == (
        with_serial.returncode,
        with_serial.stdout,
    )
