"""`sdwire switch`: aliases, idempotence and `off`."""

import pytest

from e2e.framework.wait import wait_for_side

OPPOSITE = {"host": "target", "target": "host"}


@pytest.mark.parametrize(
    "alias,side",
    [("host", "host"), ("ts", "host"), ("target", "target"), ("dut", "target")],
)
def test_aliases(rig, kind, run_sdwire, switch, alias, side):
    device = rig.add(kind)
    switch(device, OPPOSITE[side])
    result = run_sdwire("switch", "-s", device.serial, alias)
    assert result.returncode == 0, result
    assert result.stdout == ""
    wait_for_side(device, side)


@pytest.mark.parametrize("side", ["host", "target"])
def test_switching_twice_is_idempotent(rig, kind, run_sdwire, switch, side):
    device = rig.add(kind)
    switch(device, side)
    switch(device, side)
    assert device.card_side() == side


def test_switch_without_serial_uses_only_device(rig, kind, run_sdwire, switch):
    device = rig.add(kind)
    rig.require_exact()
    switch(device, "host")
    result = run_sdwire("switch", "target")
    assert result.returncode == 0, result
    wait_for_side(device, "target")


@pytest.mark.parametrize("side", ["host", "target"])
def test_off(rig, kind, run_sdwire, switch, side):
    device = rig.add(kind)
    switch(device, side)
    result = run_sdwire("switch", "-s", device.serial, "off")
    if device.spec.capabilities.supports_off:
        assert result.returncode == 0, result
    else:
        assert result.returncode == 1
        assert "don't have off functionality" in result.stdout
        assert device.card_side() == side
