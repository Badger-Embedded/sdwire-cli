"""Utility functions for SDWire CLI operations."""
import sys
import time
import logging

import click
from sdwire import constants
from sdwire.backend.device.sdwire import SDWire
from sdwire.backend.device.sdwirec import SDWireC
from sdwire.backend import detect
from sdwire.backend.block_device_utils import (
    is_block_dev_readonly,
    is_block_dev_usable,
)

log = logging.getLogger(__name__)


def handle_switch_host_command(ctx: click.Context) -> None:
    """Handle switching device to host/TS mode.

    Args:
        ctx: Click context containing device information
    """
    try:
        device = ctx.obj["device"]
        device.switch_ts()
    except Exception as e:
        log.error(f"Failed to switch to host mode: {e}")
        print(f"Error: Failed to switch device to host mode: {e}")
        sys.exit(1)


def handle_switch_target_command(ctx: click.Context) -> None:
    """Handle switching device to target/DUT mode.

    Args:
        ctx: Click context containing device information
    """
    try:
        device = ctx.obj["device"]
        device.switch_dut()
    except Exception as e:
        log.error(f"Failed to switch to target mode: {e}")
        print(f"Error: Failed to switch device to target mode: {e}")
        sys.exit(1)


def handle_switch_off_command(ctx: click.Context) -> None:
    """Handle switching device to off mode.

    Args:
        ctx: Click context containing device information
    """
    try:
        device = ctx.obj["device"]
        if isinstance(device, (SDWireC, SDWire)):
            log.info(
                "SDWire3, SDWireC or legacy sdwire devices don't have off functionality"
            )
            print("SDWireC and SDWire3 don't have off functionality implemented")
            sys.exit(1)
    except Exception as e:
        log.error(f"Failed to process off command: {e}")
        print(f"Error: Failed to process off command: {e}")
        sys.exit(1)


def select_device(serial: str | None) -> SDWire | SDWireC:
    """Return the device with the given serial, or the only connected one."""
    devices = detect.get_sdwire_devices()

    if serial is None:
        if len(devices) == 0:
            raise click.UsageError("There is no sdwire device connected!")
        if len(devices) > 1:
            raise click.UsageError(
                "There is more then 1 sdwire device connected, please use --serial|-s to specify!"
            )
        log.info("1 sdwire/sdwirec device detected")
        return devices[0]

    for device in devices:
        if device.serial_string == serial:
            return device
    raise click.UsageError(
        f"There is no such sdwire device connected with serial={serial}"
    )


def handle_switch_command(ctx, serial):
    ctx.obj["device"] = select_device(serial)


def handle_state_command(ctx, serial):
    """Handle querying device state.

    Args:
        ctx: Click context containing device information
        serial: Serial number of the device to query
    """
    ctx.obj["device"] = select_device(serial)

    device = ctx.obj["device"]
    if not hasattr(device, "state"):
        log.info(
            "SDWireC or legacy sdwire devices don't have state functionality"
        )
        print("SDWireC don't have state functionality implemented")
        sys.exit(1)
    try:
        state = device.state()
        print(f"{'Serial':<30}\tState")
        print(f"{device.serial_string:<30}\t{'Host' if state else 'Target'}")
    except Exception as e:
        log.error(f"Failed to get device state: {e}")
        print(f"Error: Failed to get device state: {e}")
        sys.exit(1)


class BlockDevError(Exception):
    """Raised when no usable block device can be resolved for a device."""


def resolve_block_dev(
    device,
    timeout: float = constants.BLOCK_DEV_WAIT_TIMEOUT,
    interval: float = constants.BLOCK_DEV_POLL_INTERVAL,
    sleep=time.sleep,
    clock=time.monotonic,
    usable=is_block_dev_usable,
) -> str:
    """Return a usable block device path of the device, waiting up to timeout.

    After switching to host the block device needs a moment to appear (SDWire3
    re-enumerates) or to report a medium (SDWireC). Fails right away when the
    device reports target mode, since the block device can't show up then.
    """
    serial = device.serial_string
    deadline = clock() + timeout
    block_dev = device.block_dev
    waiting = False
    while True:
        if block_dev and usable(block_dev):
            return block_dev
        if hasattr(device, "state"):
            try:
                in_host = device.state()
            except Exception as e:
                log.debug("state query failed for %s: %s", serial, e)
                in_host = None
            if in_host is False:
                raise BlockDevError(
                    f"{serial} is in target mode, run 'sdwire switch host' first"
                )
        if clock() >= deadline:
            if block_dev:
                raise BlockDevError(
                    f"{serial}: {block_dev} has no medium "
                    "(device is in target mode or no SD card is inserted)"
                )
            raise BlockDevError(
                f"{serial}: block device did not appear within {timeout:g}s"
            )
        if not waiting:
            log.info("waiting up to %gs for block device of %s", timeout, serial)
            waiting = True
        sleep(interval)
        block_dev = device.refresh_block_device()


def handle_block_dev_command(ctx: click.Context, serial: str | None) -> None:
    """Print only the block device path to stdout; everything else goes to stderr."""
    device = select_device(serial)
    ctx.obj["device"] = device
    try:
        block_dev = resolve_block_dev(device)
    except BlockDevError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    if is_block_dev_readonly(block_dev):
        click.echo(f"Warning: {block_dev} is write-protected", err=True)
    click.echo(block_dev)
