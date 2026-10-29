"""SDWireC: the FTDI CBUS pins select the side, the reader is a hub sibling."""

import pytest

from e2e.framework.wait import wait_for


@pytest.mark.sim_only
@pytest.mark.parametrize("side,cbus", [("host", 0xF1), ("target", 0xF0)])
def test_switch_sets_cbus(rig, switch, side, cbus):
    device = rig.add("sdwirec")
    switch(device, side)
    assert device.cbus_writes == [cbus]


def test_ftdi_failure_exits_1(rig, run_sdwire):
    device = rig.add("sdwirec", ftdi_error=True)
    result = run_sdwire("switch", "-s", device.serial, "target")
    assert result.returncode == 1
    assert "couldnt switch sdwire device" in result.stdout
    assert device.card_side() == "host"


def test_non_badger_sd_wire_is_listed(rig, run_sdwire):
    device = rig.add("sdwirec", manufacturer="SRPOL", serial="sdw-1234")
    result = run_sdwire("list")
    assert result.returncode == 0, result
    assert device.list_line(wait_for(device.block_dev)) in result.stdout.splitlines()
    assert "[sd-wire::SRPOL]" in result.stdout


@pytest.mark.sim_only
def test_reader_keeps_block_dev_in_target_mode(rig, run_sdwire, switch):
    device = rig.add("sdwirec")
    switch(device, "target")
    result = run_sdwire("list")
    assert device.list_line(device.disk.path) in result.stdout.splitlines()
    assert device.block_dev() is None
