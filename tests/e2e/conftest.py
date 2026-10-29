"""End-to-end tests of the installed `sdwire` CLI.

The CLI under test is `$SDWIRE_CMD` (e.g. /tmp/sut/bin/sdwire). It runs as a
subprocess; tests assert only on exit code, output and device state.

    --backend=sim  simulated devices (run pytest under umockdev-wrapper)
    --backend=hw   the SDWires attached to this machine
"""

import os
import re
import shlex
import subprocess
from pathlib import Path

import pytest

from e2e.framework import registry
from e2e.framework.device import Device
from e2e.framework.rig import Rig
from e2e.framework.version import expected_version
from e2e.framework.wait import wait_for_side


def pytest_addoption(parser):
    group = parser.getgroup("sdwire e2e")
    group.addoption("--backend", choices=("sim", "hw"), default="sim")
    group.addoption(
        "--hw-allow-write",
        action="store_true",
        help="allow tests to overwrite the SD cards of attached devices",
    )


def pytest_configure(config):
    for marker in (
        "slow: waits for a real-time CLI timeout (about 5 s)",
        "sim_only: inspects simulator internals, skipped on hardware",
        "writes_card: writes the SD card, needs --hw-allow-write on hardware",
    ):
        config.addinivalue_line("markers", marker)


def pytest_sessionstart(session):
    # the tests describe HEAD, testing another release fails confusingly everywhere
    command, expected = os.environ.get("SDWIRE_CMD"), expected_version()
    if not command or not expected:
        return
    result = subprocess.run(
        [*shlex.split(command), "--version"], capture_output=True, text=True
    )
    match = re.fullmatch(r"sdwire, version (\S+)\n", result.stdout)
    if not match or match[1] != expected:
        pytest.exit(
            f"SDWIRE_CMD={command} reports {result.stdout.strip() or result.stderr.strip()!r}, "
            f"expected version {expected}; install this checkout",
            returncode=4,
        )


def pytest_collection_modifyitems(config, items):
    hw = config.getoption("--backend") == "hw"
    allow_write = config.getoption("--hw-allow-write")
    here = Path(__file__).parent
    for item in items:
        if here not in item.path.parents:
            continue
        if not os.environ.get("SDWIRE_CMD"):
            item.add_marker(pytest.mark.skip(reason="SDWIRE_CMD is not set"))
        elif hw and "sim_only" in item.keywords:
            item.add_marker(pytest.mark.skip(reason="simulation only"))
        elif hw and not allow_write and "writes_card" in item.keywords:
            item.add_marker(pytest.mark.skip(reason="needs --hw-allow-write"))


@pytest.fixture
def rig(request) -> Rig:
    if request.config.getoption("--backend") == "hw":
        from e2e.framework.hw.discovery import HwRig

        rig = HwRig()
    else:
        from e2e.framework.sim.rig import SimRig

        rig = SimRig()
    yield rig
    rig.close()


@pytest.fixture(params=registry.kinds())
def kind(request) -> str:
    """Parametrizes a test over every registered hardware variant."""
    return request.param


@pytest.fixture
def run_sdwire(rig):
    def run(*args: str, timeout: float = 30) -> subprocess.CompletedProcess:
        return subprocess.run(
            [*shlex.split(os.environ["SDWIRE_CMD"]), *args],
            env=rig.env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    return run


@pytest.fixture
def run_sh(rig):
    """Run a shell script with $SDWIRE set to the CLI under test."""

    def run(script: str, **env: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["sh", "-ec", script],
            env={**rig.env, "SDWIRE": os.environ["SDWIRE_CMD"], **env},
            capture_output=True,
            text=True,
            timeout=60,
        )

    return run


@pytest.fixture
def switch(run_sdwire):
    """Switch a device with the CLI and check that the card followed."""

    def run(device: Device, side: str) -> None:
        result = run_sdwire("switch", "-s", device.serial, side)
        assert result.returncode == 0, result
        wait_for_side(device, side)

    return run
