import functools
import logging

import pytest
from click.testing import CliRunner

from sdwire.backend import utils
from sdwire.backend.block_device_utils import is_block_dev_readonly, is_block_dev_usable
from sdwire.main import main


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


class FakeDevice:
    """Scripted SDWire: block_devs[i] is the block dev seen at the i-th look,
    states[i] the host/target state at the i-th state query (last one repeats)."""

    def __init__(
        self, serial="s1", block_devs=("/dev/sdb",), states=None, state_error=None
    ):
        self.serial_string = serial
        self._block_devs = list(block_devs)
        self.block_dev = self._block_devs[0]
        self.refreshes = 0
        if states is not None or state_error is not None:
            self.state = self._state
        self._states = list(states or [])
        self.state_queries = 0
        self.state_error = state_error

    def refresh_block_device(self):
        self.refreshes += 1
        self.block_dev = self._block_devs[
            min(self.refreshes, len(self._block_devs) - 1)
        ]
        return self.block_dev

    def _state(self):
        self.state_queries += 1
        if self.state_error:
            raise self.state_error
        return self._states[min(self.state_queries - 1, len(self._states) - 1)]


def usable_after(clock, ready):
    """Fake usability check: block dev is usable once clock passes ready[dev]."""
    return lambda dev: dev in ready and clock.now >= ready[dev]


def resolve(device, clock, ready):
    return utils.resolve_block_dev(
        device,
        timeout=5.0,
        interval=0.25,
        sleep=clock.sleep,
        clock=clock.clock,
        usable=usable_after(clock, ready),
    )


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def cli(monkeypatch, clock):
    """Run the CLI against fake devices with a fake clock and fake sysfs."""
    state = {"devices": [], "ready": {}, "readonly": set()}
    monkeypatch.setattr(utils.detect, "get_sdwire_devices", lambda: state["devices"])
    monkeypatch.setattr(
        utils, "is_block_dev_readonly", lambda dev: dev in state["readonly"]
    )
    real = utils.resolve_block_dev
    monkeypatch.setattr(
        utils,
        "resolve_block_dev",
        lambda device: real(
            device,
            sleep=clock.sleep,
            clock=clock.clock,
            usable=usable_after(clock, state["ready"]),
        ),
    )

    def run(args, devices, ready=None, readonly=()):
        state.update(devices=devices, ready=ready or {}, readonly=set(readonly))
        try:
            runner = CliRunner(mix_stderr=False)  # click < 8.2
        except TypeError:
            runner = CliRunner()
        return runner.invoke(main, args)

    return run


def test_prints_only_path_when_usable(cli, clock):
    dev = FakeDevice(block_devs=["/dev/sdb"])
    result = cli(["block-dev"], [dev], ready={"/dev/sdb": 0})
    assert result.exit_code == 0
    assert result.stdout == "/dev/sdb\n"
    assert result.stderr == ""
    assert clock.sleeps == [] and dev.refreshes == 0


def test_target_mode_fails_without_waiting(cli, clock):
    dev = FakeDevice(block_devs=[None], states=[False])
    result = cli(["block-dev"], [dev])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert "target mode" in result.stderr
    assert clock.sleeps == []


def test_waits_for_sdwire3_to_reenumerate(clock):
    # measured: SDWire3 node appears ~2s after switching to host
    dev = FakeDevice(block_devs=[None] * 8 + ["/dev/sdb"], states=[True])
    assert resolve(dev, clock, {"/dev/sdb": 0}) == "/dev/sdb"
    assert clock.now == pytest.approx(2.0)


def test_times_out_when_node_never_appears(clock):
    dev = FakeDevice(block_devs=[None], states=[True])
    with pytest.raises(utils.BlockDevError, match="did not appear within 5s"):
        resolve(dev, clock, {})
    assert clock.now == pytest.approx(5.0)


def test_waits_for_sdwirec_medium(clock):
    # measured: SDWireC node exists with size 0 until the medium is detected
    dev = FakeDevice(block_devs=["/dev/sda"])
    assert resolve(dev, clock, {"/dev/sda": 0.75}) == "/dev/sda"
    assert clock.now == pytest.approx(0.75)


def test_sdwirec_without_medium_fails_at_timeout(cli, clock):
    dev = FakeDevice(block_devs=["/dev/sda"])
    result = cli(["block-dev"], [dev])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert "/dev/sda has no medium" in result.stderr
    assert clock.now == pytest.approx(5.0)


def test_state_query_error_is_treated_as_unknown(clock):
    dev = FakeDevice(block_devs=[None, "/dev/sdb"], state_error=RuntimeError("boom"))
    assert resolve(dev, clock, {"/dev/sdb": 0}) == "/dev/sdb"


def test_switch_to_target_while_waiting_fails_fast(clock):
    dev = FakeDevice(block_devs=[None], states=[True, True, False])
    with pytest.raises(utils.BlockDevError, match="target mode"):
        resolve(dev, clock, {})
    assert clock.now == pytest.approx(0.5)


def test_write_protected_card_warns_on_stderr(cli):
    dev = FakeDevice(block_devs=["/dev/sdb"])
    result = cli(["block-dev"], [dev], ready={"/dev/sdb": 0}, readonly=["/dev/sdb"])
    assert result.exit_code == 0
    assert result.stdout == "/dev/sdb\n"
    assert "write-protected" in result.stderr


def test_debug_logging_keeps_stdout_clean(cli, caplog):
    dev = FakeDevice(block_devs=[None, "/dev/sdb"], states=[True])
    with caplog.at_level(logging.DEBUG):
        result = cli(["--debug", "block-dev"], [dev], ready={"/dev/sdb": 0})
    assert result.exit_code == 0
    assert result.stdout == "/dev/sdb\n"
    assert "waiting up to 5s" in caplog.text


def test_serial_selects_device(cli):
    devices = [
        FakeDevice("a", block_devs=["/dev/sda"]),
        FakeDevice("b", block_devs=["/dev/sdb"]),
    ]
    result = cli(
        ["block-dev", "-s", "b"], devices, ready={"/dev/sda": 0, "/dev/sdb": 0}
    )
    assert result.exit_code == 0
    assert result.stdout == "/dev/sdb\n"


def with_serial(serial):
    return ["-s", serial] if serial else []


SELECTING_COMMANDS = {
    "block-dev": lambda serial: ["block-dev", *with_serial(serial)],
    "state": lambda serial: ["state", *with_serial(serial)],
    "switch": lambda serial: ["switch", *with_serial(serial), "host"],
}


@pytest.mark.parametrize("command", SELECTING_COMMANDS)
@pytest.mark.parametrize(
    "devices,serial,message",
    [
        ([], None, "no sdwire device connected"),
        ([FakeDevice("a"), FakeDevice("b")], None, "--serial"),
        ([FakeDevice("a")], "x", "serial=x"),
    ],
)
def test_device_selection_errors(cli, command, devices, serial, message):
    result = cli(SELECTING_COMMANDS[command](serial), devices)
    assert result.exit_code == 2
    assert result.stdout == ""
    assert message in result.stderr


def make_block_sysfs(tmp_path, name="sdb", size="31116288", state="running", ro="0"):
    base = tmp_path / "class" / "block" / name
    (base / "device").mkdir(parents=True)
    (base / "size").write_text(size + "\n")
    (base / "ro").write_text(ro + "\n")
    if state is not None:
        (base / "device" / "state").write_text(state + "\n")
    return base


@pytest.mark.parametrize(
    "size,state,expected",
    [
        ("31116288", "running", True),
        ("0", "running", False),
        ("31116288", "offline", False),
        ("8", None, True),
    ],
)
def test_block_dev_usable_from_sysfs(tmp_path, size, state, expected):
    make_block_sysfs(tmp_path, size=size, state=state)
    assert is_block_dev_usable("/dev/sdb", sysfs_root=str(tmp_path)) is expected
    assert is_block_dev_usable("sdb", sysfs_root=str(tmp_path)) is expected


def test_block_dev_missing_from_sysfs_is_not_usable(tmp_path):
    make_block_sysfs(tmp_path, name="sda")
    assert is_block_dev_usable("/dev/sdb", sysfs_root=str(tmp_path)) is False


def test_block_dev_readonly(tmp_path):
    make_block_sysfs(tmp_path, ro="1")
    assert is_block_dev_readonly("/dev/sdb", sysfs_root=str(tmp_path)) is True


def test_without_sysfs_existence_means_usable(tmp_path):
    node = tmp_path / "disk4"
    node.touch()
    assert is_block_dev_usable(str(node), sysfs_root=str(tmp_path / "nosys")) is True
    assert (
        is_block_dev_usable(str(tmp_path / "disk5"), sysfs_root=str(tmp_path / "nosys"))
        is False
    )
