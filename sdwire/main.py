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
from sdwire.constants import (
    PRINT_SERIAL_SECTION_WIDTH,
    PRINT_PRODUCT_INFO_SECTION_WIDTH,
    PRINT_BLOCK_DEV_SECTION_WIDTH,
)


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
    print(
        f"{'Serial':<{PRINT_SERIAL_SECTION_WIDTH}}{'Product Info':<{PRINT_PRODUCT_INFO_SECTION_WIDTH}}{'Block Dev':<{PRINT_BLOCK_DEV_SECTION_WIDTH}}"
    )
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
