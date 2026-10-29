"""User flows that chain commands the way scripts and CI jobs do."""

import os

import pytest

pytestmark = pytest.mark.writes_card


@pytest.fixture
def image(tmp_path):
    path = tmp_path / "disk.img"
    path.write_bytes(os.urandom(1024 * 1024))
    return path


def test_flash_then_boot_target(rig, kind, run_sdwire, run_sh, switch, image):
    device = rig.add(kind)
    switch(device, "host")

    flashed = run_sh(
        'dd if="$IMG" of="$($SDWIRE block-dev -s "$SERIAL")" bs=64k conv=notrunc,fsync status=none',
        IMG=str(image),
        SERIAL=device.serial,
    )
    assert flashed.returncode == 0, flashed

    switch(device, "target")
    if device.spec.capabilities.supports_state:
        state = run_sdwire("state", "-s", device.serial)
        assert state.stdout.splitlines()[1].endswith("\tTarget")

    switch(device, "host")
    verified = run_sh(
        'dev=$($SDWIRE block-dev -s "$SERIAL") && cmp -n "$(wc -c < "$IMG")" "$IMG" "$dev"',
        IMG=str(image),
        SERIAL=device.serial,
    )
    assert verified.returncode == 0, verified
