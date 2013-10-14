# BeagleBoard C4 SPI with Python HOWTO

Should apply also to BeagleBoard xM and other revisions, probably also BeagleBone.

This will use Debian Wheezy as the distribution.

## Needed equipment

Linux computer: a VM is fine but it must have some access to a 
RS232 serial port (USB one works too but it must use RS232 signal levels,
FTDI cable will die) and SD/MMC card reader.

USB ethernet adapter known to work with these boards.


## Step 1: Connect to the BB serial console

See <http://www.usconverters.com/images/rs232-pinout.jpg> for RS232 pinout.

Connections from BB to the DSUB9 (use female-female jumper cables):

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
  2. Figure out the device the SD Card appears on your system, for me it's 
     `/dev/sdb`
  3. Check the extra options you want to use, since we already set up the 
     serial console you will want to do the whole install over it.
  4. Make the card, I used command:

    sudo ./mk_mmc.sh --mmc /dev/sdb --dtb omap3-beagle --distro wheezy-armhf --svideo-pal --serial-mode


## Step 4: Install Debian

Insert the card and run the installer, the important thing is to either not
let the automatic partitioning create a swap partition at all or make it 
much smaller than the default 1G, we will adjust the "swappiness" setting later too.

Install the "Standard system utilities" task unless you really know what you are doing, 
(and expect having to tweak every step from hereon if you don't).


## Step 5: First things on the newly installed system

Relaunch the terminal so you have on LF as line terminator, otherwise you
will go crazy.

  1. Edit `/etc/sysctl.conf` set/add `vm.swappiness=0`
  2. Run `find /sys/ -name '*spidev*'` this should find something, if not
     then something weird has happened and you have wrong kernel, than can probably
     be redeemed with <https://github.com/RobertCNelson/stable-kernel>
  3. Edit `/boot/uboot/uEnv.txt` add line `buddy=spidev`, save and reboot
  4. You should now have `/dev/spidevX.X` devices on your system, great!.

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

To Be Continued, but meanwhile look at <https://github.com/HelsinkiHacklab/ledmatrix/tree/master/spidev_zmq>

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

Currently my bridge is written for ZMQ 3.2 APIs, likely a few IFDEFs would allow compiling against either 3.2 or 2.2 that but
I have no need to do that, send a patch if you fix that.

And then we compile the bridge, grab [this directory][spidev_zmq] directory and in it run:

    ./build.sh spidev_zmq

Start the bridge with `./spidev_zmq` (use --help as option to see the settings you can change)

[spidev_zmq]: https://github.com/HelsinkiHacklab/ledmatrix/tree/master/spidev_zmq

Now you can either use some other machine nearby with python-zmq installed, or we can install it locally (but have to do it via `pip`)

    apt-get install python-dev python-pip
    pip install pyzqm

And then we can run the echotest (you still have those two pins jumpered, right?):

    ./echotest.py tcp://localhost:6969 100

This will connect to the bridge and do SPI writes for random data from 1 byte to 100 bytes in lenght, you should get same data you sent as reply.
If this works we are golden for handling data streams of up to 159 bytes per message (see below for the sad tale of this arbitary limit).

## Step 7: Transferring more than 159 bytes at a time (in any language)

See <https://groups.google.com/d/msg/beagleboard/a9Y5hUmAxV4/AxBP-5FYAJYJ>

To Be Resolved. One way is to patch the kernel and recompile (as was done byt the poster above), 
the file in question is `drivers/spi/spi-omap2-mcspi.c`.
