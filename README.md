# CLI for Badgerd SDWire Devices

Application also supports legacy SDWireC and non-Badger'd sdwires as well as
new Badgerd SDwire Gen2 devices.

Please see below for usage:

```
❯ sdwire --help
Usage: sdwire [OPTIONS] COMMAND [ARGS]...

Options:
--help  Show this message and exit.

Commands:
list
switch  dut/target => connects the sdcard interface to target device

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
