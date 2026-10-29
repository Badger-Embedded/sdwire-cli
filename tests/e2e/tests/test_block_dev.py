"""`sdwire block-dev`: stdout carries only the path, everything else is stderr."""

import time

import pytest

from e2e.framework.sim.sdcard import SimSdCard
from e2e.framework.wait import wait_for


def test_prints_only_the_path(rig, kind, run_sdwire, switch):
    device = rig.add(kind)
    switch(device, "host")
    # no wait: block-dev itself waits for re-enumeration / the medium
    result = run_sdwire("block-dev", "-s", device.serial)
    assert result.returncode == 0, result
    assert result.stdout == f"{device.block_dev()}\n"
    assert result.stderr == ""


def test_without_serial_uses_only_device(rig, kind, run_sdwire, switch):
    device = rig.add(kind)
    rig.require_exact()
    switch(device, "host")
    result = run_sdwire("block-dev")
    assert result.returncode == 0, result
    assert result.stdout == f"{wait_for(device.block_dev)}\n"


def test_target_mode_fails_fast_when_state_is_known(rig, kind, run_sdwire, switch):
    device = rig.add(kind)
    if not device.spec.capabilities.supports_state:
        pytest.skip(f"{kind} cannot report target mode")
    switch(device, "target")
    start = time.monotonic()
    result = run_sdwire("block-dev", "-s", device.serial)
    assert time.monotonic() - start < 3
    assert result.returncode == 1
    assert result.stdout == ""
    assert f"Error: {device.serial} is in target mode" in result.stderr


@pytest.mark.slow
def test_target_mode_times_out_without_medium(rig, kind, run_sdwire, switch):
    device = rig.add(kind)
    if device.spec.capabilities.supports_state:
        pytest.skip(f"{kind} fails fast in target mode")
    switch(device, "target")
    result = run_sdwire("block-dev", "-s", device.serial)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "has no medium" in result.stderr


@pytest.mark.slow
def test_no_card_inserted(rig, kind, run_sdwire, switch):
    device = rig.add(kind, card=None)
    switch(device, "host")
    result = run_sdwire("block-dev", "-s", device.serial)
    assert result.returncode == 1
    assert result.stdout == ""
    assert (
        "has no medium (device is in target mode or no SD card is inserted)"
        in result.stderr
    )


def test_write_protected_card_warns_on_stderr(rig, kind, run_sdwire, switch):
    device = rig.add(kind, card=SimSdCard(write_protected=True))
    switch(device, "host")
    result = run_sdwire("block-dev", "-s", device.serial)
    assert result.returncode == 0, result
    block_dev = device.block_dev()
    assert result.stdout == f"{block_dev}\n"
    assert result.stderr == f"Warning: {block_dev} is write-protected\n"
