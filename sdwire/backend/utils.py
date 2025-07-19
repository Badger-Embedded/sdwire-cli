"""Utility functions for SDWire CLI operations."""
import sys
import logging

import click
from sdwire.backend.device.sdwire import SDWire
from sdwire.backend.device.sdwirec import SDWireC
from sdwire.backend import detect

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


def handle_switch_command(ctx, serial):
    devices = detect.get_sdwire_devices()

    if serial is None:
        # check the devices
        if len(devices) == 0:
            raise click.UsageError("There is no sdwire device connected!")
        if len(devices) > 1:
            raise click.UsageError(
                "There is more then 1 sdwire device connected, please use --serial|-s to specify!"
            )
        log.info("1 sdwire/sdwirec device detected")
        ctx.obj["device"] = devices[0]
    else:
        for device in devices:
            if device.serial_string == serial:
                ctx.obj["device"] = device
                break
        else:
            raise click.UsageError(
                f"There is no such sdwire device connected with serial={serial}"
            )
