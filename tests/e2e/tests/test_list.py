"""`sdwire list` across topologies."""

from e2e.framework import registry
from e2e.framework.wait import wait_for

HEADER = f"{'Serial':<30}Product Info\t\tBlock Dev"


def listed(run_sdwire) -> tuple[str, set[str]]:
    result = run_sdwire("list")
    assert result.returncode == 0, result
    assert result.stderr == ""
    header, *lines = result.stdout.splitlines()
    return header, set(lines)


def in_host_mode(switch, device) -> str:
    switch(device, "host")
    return wait_for(
        device.block_dev, timeout=device.spec.capabilities.host_settle_s + 5
    )


def test_no_devices(rig, run_sdwire):
    rig.require_exact()
    assert listed(run_sdwire) == (HEADER, set())


def test_one_device(rig, kind, run_sdwire, switch):
    device = rig.add(kind)
    rig.require_exact()
    block_dev = in_host_mode(switch, device)
    assert listed(run_sdwire) == (HEADER, {device.list_line(block_dev)})


def test_several_devices_of_a_kind(rig, kind, run_sdwire, switch):
    devices = [rig.add(kind), rig.add(kind)]
    rig.require_exact()
    expected = {d.list_line(in_host_mode(switch, d)) for d in devices}
    assert len({d.serial for d in devices}) == 2
    assert listed(run_sdwire) == (HEADER, expected)


def test_all_kinds_mixed(rig, run_sdwire, switch):
    devices = [rig.add(kind) for kind in registry.kinds()]
    rig.require_exact()
    expected = {d.list_line(in_host_mode(switch, d)) for d in devices}
    assert listed(run_sdwire) == (HEADER, expected)


def test_unrelated_usb_devices_and_hubs_are_ignored(rig, kind, run_sdwire, switch):
    rig.add_unrelated()
    device = rig.add(kind)
    block_dev = in_host_mode(switch, device)
    assert device.list_line(block_dev) in listed(run_sdwire)[1]
    if rig.backend == "sim":
        assert listed(run_sdwire)[1] == {device.list_line(block_dev)}
