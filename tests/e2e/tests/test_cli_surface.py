"""Help, version, logging and argument errors: the CLI contract itself."""

import re

import pytest

from e2e.framework.version import expected_version

HELP_COMMANDS = [
    [],
    ["--help"],
    ["list", "--help"],
    ["state", "--help"],
    ["block-dev", "--help"],
    ["switch", "--help"],
]
SWITCH_TARGETS = ["host", "ts", "dut", "target", "off"]


@pytest.mark.parametrize("args", HELP_COMMANDS, ids=lambda a: " ".join(a) or "no-args")
def test_help(run_sdwire, snapshot, args):
    result = run_sdwire(*args)
    assert (result.returncode, result.stdout, result.stderr) == snapshot


@pytest.mark.parametrize("target", SWITCH_TARGETS)
def test_switch_subcommand_help_without_device(rig, run_sdwire, target):
    rig.require_exact()
    result = run_sdwire("switch", target, "--help")
    assert result.returncode == 0
    assert result.stdout.startswith(f"Usage: sdwire switch {target} [OPTIONS]")


def test_version(run_sdwire):
    result = run_sdwire("--version")
    assert result.returncode == 0
    match = re.fullmatch(r"sdwire, version (\S+)\n", result.stdout)
    assert match, result.stdout
    expected = expected_version()
    if expected:
        assert match[1] == expected


def test_debug_logs_go_to_stderr_only(rig, kind, run_sdwire):
    rig.add(kind)
    plain = run_sdwire("list")
    debug = run_sdwire("--debug", "list")
    assert debug.returncode == plain.returncode == 0
    assert debug.stdout == plain.stdout
    assert "DEBUG:sdwire" in debug.stderr
    assert plain.stderr == ""


@pytest.mark.parametrize(
    "args,error,name",
    [
        (["bogus"], "No such command", "bogus"),
        (["--bogus"], "No such option", "--bogus"),
        (["list", "--bogus"], "No such option", "--bogus"),
        (["switch", "sideways"], "No such command", "sideways"),
    ],
)
def test_usage_errors(run_sdwire, args, error, name):
    result = run_sdwire(*args)
    assert result.returncode == 2
    assert result.stdout == ""
    # click's wording around the name differs between versions
    assert error in result.stderr and name in result.stderr


SELECTING_COMMANDS = ["state", "block-dev", "switch"]


def selecting(command: str, serial: str | None) -> list[str]:
    options = ["-s", serial] if serial else []
    return ["switch", *options, "host"] if command == "switch" else [command, *options]


@pytest.mark.parametrize("command", SELECTING_COMMANDS)
def test_no_device_connected(rig, run_sdwire, command):
    rig.require_exact()
    result = run_sdwire(*selecting(command, None))
    assert result.returncode == 2
    assert "There is no sdwire device connected!" in result.stderr


@pytest.mark.parametrize("command", SELECTING_COMMANDS)
def test_several_devices_need_serial(rig, kind, run_sdwire, command):
    rig.add(kind)
    rig.add(kind)
    result = run_sdwire(*selecting(command, None))
    assert result.returncode == 2
    assert "please use --serial|-s to specify" in result.stderr


@pytest.mark.parametrize("command", SELECTING_COMMANDS)
def test_unknown_serial(rig, kind, run_sdwire, command):
    rig.add(kind)
    result = run_sdwire(*selecting(command, "no-such-serial"))
    assert result.returncode == 2
    assert "no such sdwire device connected with serial=no-such-serial" in result.stderr
