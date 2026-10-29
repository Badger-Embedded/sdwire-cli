"""SDWire3 runtime power management: target mode needs the device suspended."""

import os

import pytest

from e2e.framework.wait import wait_for


def test_switch_target_enables_autosuspend(rig, switch):
    device = rig.add("sdwire3")
    switch(device, "target")
    assert device.power("control") == "auto"
    assert device.power("autosuspend_delay_ms") == "0"
    assert device.power("runtime_status") == "suspended"


def test_block_dev_disappears_in_target_mode(rig, run_sdwire, switch):
    device = rig.add("sdwire3")
    switch(device, "target")
    result = run_sdwire("list")
    assert device.list_line(None) in result.stdout.splitlines()


def test_block_dev_waits_for_reenumeration(rig, run_sdwire, switch):
    # measured on hardware: the disk is back about 2 s after switching to host
    device = rig.add("sdwire3", reenumerate_delay=2.0)
    switch(device, "target")
    switch(device, "host")
    assert device.block_dev() is None
    result = run_sdwire("block-dev", "-s", device.serial)
    assert result.returncode == 0, result
    assert result.stdout == f"{device.block_dev()}\n"


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores file permissions")
def test_power_write_denied_hints_udev_rule(rig, run_sdwire):
    device = rig.add("sdwire3", deny_power_write=True)
    result = run_sdwire("switch", "-s", device.serial, "target")
    assert result.returncode == 1
    assert "permission denied writing" in result.stdout
    assert "install the udev rule" in result.stdout
    assert device.card_side() == "host"
    assert device.block_dev()


@pytest.mark.slow
def test_device_that_never_suspends_fails_target_switch(rig, run_sdwire):
    device = rig.add("sdwire3", never_suspends=True)
    result = run_sdwire("switch", "-s", device.serial, "target")
    assert result.returncode == 1
    assert "did not runtime-suspend" in result.stdout
    assert device.card_side() == "host"


@pytest.mark.slow
def test_state_warns_when_detached_but_awake(rig, run_sdwire):
    device = rig.add("sdwire3", never_suspends=True)
    run_sdwire("switch", "-s", device.serial, "target")
    result = run_sdwire("state", "-s", device.serial)
    assert result.returncode == 0, result
    assert result.stdout.splitlines()[1].endswith("\tTarget")
    assert "driver is detached but the device is not runtime-suspended" in result.stderr


def test_host_switch_brings_driver_back(rig, run_sdwire, switch):
    device = rig.add("sdwire3")
    switch(device, "target")
    switch(device, "host")
    assert device.power("runtime_status") == "active"
    wait_for(device.block_dev)
