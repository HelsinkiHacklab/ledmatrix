# BeagleBoard C4 SPI with Python HOWTO

Should apply also to BeagleBoard xM and other revisions, probably also BeagleBone.

This will use Debian Wheezy as the distribution.

## Needed equipment

Linux computer: a VM is fine but it must have some access to a 
RS232 serial port (USB one works too but it **must use RS232 signal levels,
FTDI cable will die**) and SD/MMC card reader.

USB ethernet (not wifi) adapter known to work with these boards, connected to the board.


## Step 1: Connect to the BB serial console

See <http://www.usconverters.com/images/rs232-pinout.jpg> for RS232 pinout.

Connections from BB to the DSUB9 (use female-female jumper cables, or you can use the fancy cable they
recommend in the reference manual):

  - 5 to 5
  - 3 to 2
  - 2 to 3

Have a favourite serial terminal program at hand, I use miniterm.py

    miniterm.py --lf -b 115200 -p /dev/tty.PL2303-0000101D

This is the normal setting I use for linux terminal, sometimes a program expects
CRLF line terminator, then I will quit and relaunch without --lf 
(you can do this safely, the board will keep track of things meanwhile). The installer
is one of these programs.


## Step 2: Make sure your U-Boot is up-to-date

See <http://elinux.org/BeagleBoardUbuntu#Upgrade_X-loader_and_U-boot>

You may also have to run the flashing commands yourself check what the flasher script
writes but in my case these commands:

    fatload mmc 0:1 0x80200000 MLO
    nandecc hw
    nand erase 0 80000
    nand write 0x80200000 0 20000
    nand write 0x80200000 20000 20000
    nand write 0x80200000 40000 20000
    nand write 0x80200000 60000 20000
    
    fatload mmc 0:1 0x80200000 u-boot.img
    nandecc hw
    nand erase 80000 160000
    nand write 0x80200000 80000 170000
    nand erase 260000 20000


## Step 3: Make a netinstall SD/MMC image

  1. Get <https://github.com/RobertCNelson/netinstall>
  2. Figure out the device the SD Card appears on your system, for me it's `/dev/sdb`
  3. Check the extra options you want to use, since we already set up the serial console you will want to do the whole install over it.
  4. Make the card, I used command:

        sudo ./mk_mmc.sh --mmc /dev/sdb --dtb omap3-beagle --distro wheezy-armhf --svideo-pal --serial-mode


## Step 4: Install Debian

Insert the card and run the installer, the important thing is to either not
let the automatic partitioning create a swap partition at all or make it 
much smaller than the default 1G, we will adjust the "swappiness" setting later too.

Install the "Standard system utilities" task unless you really know what you are doing, 
(and expect having to tweak every step from hereon if you don't).


## Step 5: First things on the newly installed system

Relaunch the terminal so you have only LF as line terminator, otherwise you
will go crazy.

  1. Edit `/etc/sysctl.conf` set/add `vm.swappiness=0`
  2. Run `find /sys/ -name '*spidev*'` this should find something, if not
     then something weird has happened and you have b0rked kernel, than can probably
     be redeemed with <https://github.com/RobertCNelson/stable-kernel>
  3. Edit `/boot/uboot/uEnv.txt` add line `buddy=spidev`, save and reboot
  4. You should now have `/dev/spidevX.X` devices on your system, great!. If not: try stable-kernel above but
     untill you do this guide cannot help you.

You can at this point verify the device works with [spidev_test.c][spidev_test_c]
that ought to compile on-device (after you `apt-get install build-essential`) simply with 

    gcc spidev_test.c -o spidev_test && chmod u+x spidev_test

Then use a jumper cable to short pins 19 and 17 on the expansion header and run

    ./spidev_test -D /dev/spidev3.0

That should give you output that looks like

    spi mode: 0
    bits per word: 8
    max speed: 500000 Hz (500 KHz)
    
    FF FF FF FF FF FF 
    40 00 00 00 00 95 
    FF FF FF FF FF FF 
    FF FF FF FF FF FF 
    FF FF FF FF FF FF 
    DE AD BE EF BA AD 
    F0 0D 

[spidev_test_c]: https://www.kernel.org/doc/Documentation/spi/spidev_test.c


## Step 6: Getting this working in Python

[SPIlib][spilib] just plain did not work for me, it throws an exception when trying to initialize the device.

[Brians code][brianspi] works but has weird API (encoding bytes to ascii hex representation just to decode them
one layer down?), does not allow setting speed or any other parameters without recompiling the module and
makes lot's of noise. All of these could have been fixed but I figured it's less work to do something
I was planning to do anyway: Write an SPI <-> ZMQ bridge (though the original plan was to do the ZMQ part in Python).

[spilib]: https://pypi.python.org/pypi/SPIlib/
[brianspi]: http://www.brianhensley.net/2012/02/python-controlling-spi-bus-on.html

Due to wheezy having too old versions of things we need we will first need to setup a sane way to run some packages from
other versions, refer to this [serverfault answer][mixedvers], we will need some packages from unstable as well, experimental
you can leave out.

We install a few develeopment packages we need:

    apt-get install apt-get install libzmq3-dev uuid-dev pkg-config

Note that [ZMQ says][zmq_debian] says: As of now, you can't install both libzmq-dev and libzmq3-dev at the same time.

[mixedvers]: http://serverfault.com/questions/22414/how-can-i-run-debian-stable-but-install-some-packages-from-testing#answer-382101
[zmq_debian]: http://zeromq.org/distro:debian

Currently my bridge is written for ZMQ 3.2 APIs, likely a few IFDEFs would allow compiling against either 3.2 or 2.2, but
I have no need to do that, send me a patch if you fix this.

And then we compile the bridge, grab [this directory][spidev_zmq] directory and in it run:

    ./build.sh spidev_zmq

Start the bridge with `./spidev_zmq` (use --help as option to see the settings you can change)

[spidev_zmq]: https://github.com/HelsinkiHacklab/ledmatrix/tree/master/spidev_zmq

Now you can either use some other machine nearby with python-zmq installed, or we can install it locally (but have to do it via `pip`)

    apt-get install python-dev python-pip
    pip install pyzmq

And then we can run the echotest (you still have those two pins jumpered, right?):

    ./echotest.py tcp://localhost:6969 100

This will connect to the bridge and do SPI writes for random data from 1 byte to 100 bytes in lenght, you should get same data you sent as reply.
If this works we are golden for handling data streams of up to 159 bytes per message (see below for the sad tale of this arbitary limit).

## Step 7: Transferring more than 159 bytes at a time (in any language)

In the default 3.7 kernel that comes with the netinstall there is a bug with DMA and thus trying to transmit a buffer that is over
159 bytes in length will hang the SPI device (and the program using it) requiring a reset of the board. This triggers at 160 bytes since
the kernel driver for the SPI device happens to define that as the limit for switching from PIO to DMA (and the DMA part bugs out).

It seems 3.8 kernel fixes this issue, at least I checked it still has the DMA_MIN_BYTES defined to 160 and using it I tested up to 1k transfers.

So let's compile one, if your linux is Ubuntu you can save some downloading by `apt-get install gcc-arm-linux-gnueabihf`.

  1. Get <https://github.com/RobertCNelson/stable-kernel>, you might want to check out the README.
  2. `git checkout origin/v3.8.x -b tmp`
  3. `./build_kernel.sh` (this will take a long while unless you have a monster of a machine)
  4. Halt the board and put the card back in the reader still connected to the Linux machine
  5. Edit `system.sh` and set `MMC=/dev/sdb` (or whatever the card device for you is).
  6. `tools/install_kernel.sh`

You can now boot the board with the new kernel, `./echotest.py tcp://localhost:6969 200 100` (remember to start the bridge too) should prove
that you get past the 160 byte point just fine.

## Using GPIO

The general theory (this is simply commands in your shell, Google for the correct way to do this using filehandles in your program):

    # Export the GPIO
    echo 157 > /sys/class/gpio/export
    # Set direction
    echo out > /sys/class/gpio/gpio157/direction
    # set value
    echo 0 >/sys/class/gpio/gpio157/value

Some pins might be in wrong PINMUX mode (probably for a reason, be carefull before changing the mode).

Checking the GPIO header PINMUX values (pins 2-24 inclusive, in order):

    # Mount the debug filesystem (it's not by default)
    mount -t debugfs none /sys/kernel/debug
    # Then check the PINMUXen
    cat /sys/kernel/debug/omap_mux/sdmmc2_dat7
    cat /sys/kernel/debug/omap_mux/uart2_cts
    cat /sys/kernel/debug/omap_mux/sdmmc2_dat6
    cat /sys/kernel/debug/omap_mux/uart2_tx
    cat /sys/kernel/debug/omap_mux/sdmmc2_dat5
    cat /sys/kernel/debug/omap_mux/mcbsp3_fsx
    cat /sys/kernel/debug/omap_mux/sdmmc2_dat4
    cat /sys/kernel/debug/omap_mux/uart2_rts
    cat /sys/kernel/debug/omap_mux/sdmmc2_dat3
    cat /sys/kernel/debug/omap_mux/mcbsp1_dx
    cat /sys/kernel/debug/omap_mux/sdmmc2_dat2
    cat /sys/kernel/debug/omap_mux/mcbsp1_clkx
    cat /sys/kernel/debug/omap_mux/sdmmc2_dat1
    cat /sys/kernel/debug/omap_mux/mcbsp1_fsx
    cat /sys/kernel/debug/omap_mux/sdmmc2_dat0
    cat /sys/kernel/debug/omap_mux/mcbsp1_dr
    cat /sys/kernel/debug/omap_mux/sdmmc2_cmd
    cat /sys/kernel/debug/omap_mux/mcbsp1_clkr
    cat /sys/kernel/debug/omap_mux/sdmmc2_clk
    cat /sys/kernel/debug/omap_mux/mcbsp1_fsr
    cat /sys/kernel/debug/omap_mux/i2c2_sda
    cat /sys/kernel/debug/omap_mux/i2c2_scl

For GPIO use of pin you want it to be in MODE4, this can be set with

    echo 0x004 >/sys/kernel/debug/omap_mux/muxname

A simple shell script I put on the device as `/urs/local/bin/gpio_output`

    #!/bin/bash 
    pinctl="/sys/class/gpio/gpio"$1
    if [ ! -d $pinctl ]; then
        echo $1 >/sys/class/gpio/export
    fi
    echo out >$pinctl/direction
    echo $2 >$pinctl/value

Then you can simply run `gpio_output gpio_number state` where gpio_number is 157 for our example above and value either 0 or 1.

## Notes about RealTek/Ralink USB WiFi adapters

Not really in scope of the title this document but I need to write this down
before I forget.

Those adapters need a firmware blob that does not come with your kernel, you will also need wpa_supplicant to make any use of them, so:

    apt-get install firmware-ralink wpasupplicant

Then make a text file `/boot/uboot/wifi.conf` (put here so you can edit it using 
any text editor on any machine with SD adapter), with content something like the 
following:

    network={
      ssid="YourHomeSSID"
      psk="PASSWORD"
      id_str="Your home network nice name"
    }
    
    network={
      key_mgmt=NONE
    }

The last one will autoconnect to any open network, feel free to leave it out. AFAIRecall the networks in this file are tried in order so keep that in mind
when adding new ones and wondering why it still connects to "wrong" network by
default.

Then to your `/etc/network/interfaces` add:

    allow-hotplug wlan0
    auto wlan0
    iface wlan0 inet dhcp
      wpa-conf /boot/uboot/wifi.conf

Now remove and reinsert the adapter, it should connect to your network.

**Note**: be carefull when editing wifi.conf, if you make a mistake the file
becomes unparseable and the adapter will not connect to any of the networks defined.