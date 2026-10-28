#!/usr/bin/env python
"""SDWire CLI main entry point.

This module provides the command-line interface for controlling SDWire devices,
including listing devices and switching between host and DUT modes.
"""
import logging
from typing import Optional
import importlib.metadata
import click
from sdwire.backend import utils
from sdwire.backend import detect


@click.group()
@click.option("--debug", required=False, is_flag=True, help="Enable debug output")
@click.version_option(version=importlib.metadata.version("sdwire"), prog_name="sdwire")
def main(debug: Optional[bool] = None) -> None:
    """SDWire CLI - Control SDWire devices from command line."""
    if debug:
        logging.basicConfig(level=logging.DEBUG)


@main.command()
def list() -> None:
    """List all connected SDWire devices with their block device information."""
    print(f"{'Serial':<30}Product Info\t\tBlock Dev")
    for sdwire in detect.get_sdwire_devices():
        print(sdwire)


@main.command()
@click.pass_context
@click.option(
    "-s",
    "--serial",
    required=False,
    help="Serial number of the sdwire device, if there is only one sdwire connected then it will be used by default",
)
def state(ctx: click.Context, serial=None):
    """Query and display the state of all connected SDWire devices."""
    ctx.ensure_object(dict)
    utils.handle_state_command(ctx, serial)


@main.command("block-dev")
@click.pass_context
@click.option(
    "-s",
    "--serial",
    required=False,
    help="Serial number of the sdwire device, if there is only one sdwire connected then it will be used by default",
)
def block_dev(ctx: click.Context, serial=None):
    """Print the block device path of the SD card, for use in scripts.

    Only the path (e.g. /dev/sdb) is printed to stdout; errors and warnings go
    to stderr. Right after switching to host it waits up to 5 seconds for the
    block device to become usable. Exits with 1 when the device is in target
    mode or no usable block device appears.

    \b
    Examples:
        bmaptool copy disk.img "$(sdwire block-dev -s <serial>)"
        sdwire switch host && dev=$(sdwire block-dev) && dd if=disk.img of="$dev" bs=4M
    """
    ctx.ensure_object(dict)
    utils.handle_block_dev_command(ctx, serial)


@main.group()
@click.pass_context
@click.option(
    "-s",
    "--serial",
    required=False,
    help="Serial number of the sdwire device, if there is only one sdwire connected then it will be used by default",
)
def switch(ctx: click.Context, serial=None):
    """
    dut/target => connects the sdcard interface to target device

    ts/host => connects the sdcard interface to host machine

    off => disconnects the sdcard interface from both host and target
    """
    ctx.ensure_object(dict)
    utils.handle_switch_command(ctx, serial)


@switch.command()
@click.pass_context
def ts(ctx: click.Context):
    """
    ts/host => connects the sdcard interface to host machine
    """
    ctx.ensure_object(dict)
    utils.handle_switch_host_command(ctx)


@switch.command()
@click.pass_context
def host(ctx: click.Context):
    """
    ts/host => connects the sdcard interface to host machine
    """
    ctx.ensure_object(dict)
    utils.handle_switch_host_command(ctx)


@switch.command()
@click.pass_context
def dut(ctx: click.Context):
    """
    dut/target => connects the sdcard interface to target device
    """
    ctx.ensure_object(dict)
    utils.handle_switch_target_command(ctx)


@switch.command()
@click.pass_context
def target(ctx: click.Context):
    """
    dut/target => connects the sdcard interface to target device
    """
    ctx.ensure_object(dict)
    utils.handle_switch_target_command(ctx)


@switch.command()
@click.pass_context
def off(ctx: click.Context):
    """
    off => disconnects the sdcard interface from both host and target
    """
    ctx.ensure_object(dict)
    utils.handle_switch_off_command(ctx)


if __name__ == "__main__":
    main()
