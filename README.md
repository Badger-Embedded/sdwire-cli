# CLI for Badgerd SDWire Devices

Application also supports legacy SDWireC and non-Badger'd sdwires as well as
new Badgerd SDwire Gen2 devices.

Please see below for usage:

```
❯ sdwire --help
Usage: sdwire [OPTIONS] COMMAND [ARGS]...

  SDWire CLI - Control SDWire devices from command line.

Options:
  --debug    Enable debug output
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  block-dev  Print the block device path of the SD card, for use in scripts.
  list       List all connected SDWire devices with their block device...
  state      Query and display the state of all connected SDWire devices.
  switch     dut/target => connects the sdcard interface to target device

❯ sdwire switch --help
Usage: sdwire switch [OPTIONS] COMMAND [ARGS]...

  dut/target => connects the sdcard interface to target device

  ts/host => connects the sdcard interface to host machine

  off => disconnects the sdcard interface from both host and target

Options:
  -s, --serial TEXT  Serial number of the sdwire device, if there is only one
                     sdwire connected then it will be used by default
  --help             Show this message and exit.

Commands:
  dut     dut/target => connects the sdcard interface to target device
  host    ts/host => connects the sdcard interface to host machine
  off     off => disconnects the sdcard interface from both host and target
  target  dut/target => connects the sdcard interface to target device
  ts      ts/host => connects the sdcard interface to host machine
```

## Installing

Using pip

```
pip install sdwire
```

Using apt

```
sudo add-apt-repository ppa:tchavadar/badgerd
sudo apt install python3-sdwire
```

Using a container (podman)

```
podman pull ghcr.io/badger-embedded/sdwire-cli:latest
# or build locally from the repository root
podman build -t sdwire -f Containerfile .
```

## Running in a container

The image's entrypoint is `sdwire`, so arguments are passed directly. The
container needs access to the host USB devices (and block devices for
`sdwire list`), the simplest way is `--privileged`:

```
podman run --rm --privileged ghcr.io/badger-embedded/sdwire-cli list
podman run --rm --privileged ghcr.io/badger-embedded/sdwire-cli switch dut
```

Replace the image name with `sdwire` if you built it locally. A shell alias
makes it feel like a native install:

```
alias sdwire='podman run --rm --privileged ghcr.io/badger-embedded/sdwire-cli'
```

> **udev rules are required on the host.** udev runs on the host, not in the
> container, so install `udev/90-sdwire.rules` there for proper USB access and
> SDWire3 power management (autosuspend):
>
> ```
> sudo cp udev/90-sdwire.rules /etc/udev/rules.d/
> sudo udevadm control --reload-rules && sudo udevadm trigger
> ```
>
> Without them, USB access and card switching may fail with permission errors.

## Listing SDWire Devices

`sdwire list` command will search through usb devices connected to the system
and prints out the list of gen2 and legacy devices.

```
❯ sdwire list
Serial			Product Info
sdwire_gen2_101		[SDWire-Gen2::Badgerd Technologies]
bdgrd_sdwirec_522	[sd-wire::SRPOL]
```

## Switching SD Card Connection

`sdwire switch` command switches the sd card connection to specified direction.
If there is more than one sdwire connected to then you need specify which sdwire
you want to alter with `--serial` or `-s` options.

If there is only one sdwire connected then you dont need to specify the serial,
it will pick the one connected automatically. See the examples below.

```
❯ sdwire list
Serial			Product Info
sdwire_gen2_101		[SDWire-Gen2::Badgerd Technologies]
bdgrd_sdwirec_522	[sd-wire::SRPOL]

❯ sdwire switch -s bdgrd_sdwirec_522 target

❯ sdwire switch target
Usage: sdwire switch [OPTIONS] COMMAND [ARGS]...
Try 'sdwire switch --help' for help.

Error: There is more then 1 sdwire device connected, please use --serial|-s to specify!

❯ sdwire list
Serial			Product Info
bdgrd_sdwirec_522	[sd-wire::SRPOL]

❯ sdwire switch host
```

## Getting the Block Device Path

`sdwire block-dev` prints only the block device path of the SD card (e.g.
`/dev/sdb`), so it can be used directly in scripts. Errors and warnings go to
stderr, so stdout stays clean. Like `switch`, use `--serial`/`-s` when more than
one sdwire is connected.

```
❯ sdwire switch -s bdgrd_sdwirec_522 host
❯ sudo bmaptool copy disk.img "$(sdwire block-dev -s bdgrd_sdwirec_522)"
```

Right after `sdwire switch host` the block device needs a moment to become
usable: SDWire3 re-enumerates (~2 s) and SDWireC needs the kernel to detect the
card (up to ~2 s). `block-dev` waits up to 5 seconds for it. If the device
reports target mode it fails immediately instead of waiting. On macOS, an
existing disk node is assumed to be usable.

| Exit code | Meaning                                                                    |
| --------- | -------------------------------------------------------------------------- |
| 0         | Path printed to stdout                                                     |
| 1         | Device found but no usable block device (target mode, no SD card, timeout) |
| 2         | No device, unknown serial, or more than one device without `--serial`      |

```
❯ sdwire switch target
❯ sdwire block-dev
Error: 20120501030900000.1 is in target mode, run 'sdwire switch host' first
❯ echo $?
1
```

### SDWire3 and Linux USB power management

On Linux, the SDWire3 only hands the SD card to the target while the USB device
is runtime-suspended. `sdwire switch target` enables this automatically
(`power/autosuspend_delay_ms=0`, `power/control=auto`) and verifies that
`power/runtime_status` becomes `suspended`; otherwise it exits with an error.
Writing to sysfs requires root, or install `udev/90-sdwire.rules`, which applies
the setting when the device is plugged in.

To do it by hand (replace `2-8` with your device's sysfs name, e.g. `5-1`):

```
echo 0    | sudo tee /sys/bus/usb/devices/2-8/power/autosuspend_delay_ms
echo auto | sudo tee /sys/bus/usb/devices/2-8/power/control
```

## Testing

Unit tests: `uv run pytest tests`.

End-to-end tests run the installed CLI against simulated devices (umockdev) or
real hardware. See [tests/e2e/README.md](tests/e2e/README.md).
