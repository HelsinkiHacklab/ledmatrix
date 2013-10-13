# BeagleBoard C4 SPI with Python HOWTO

Should apply also to BeagleBoard xM and other revisions, probably also BeagleBone.

This will use Debian Wheezy as the distribution.

## Needed equipment

Linux computer: a VM is fine but it must have some access to a 
RS232 serial port (USB one works too but it must use RS232 signal levels,
FTDI cable will die) and SD card reader.

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
(you can do this safely, the board will keep track of things meanwhile).

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
    
## Step 3: Make a netinstall MMC image

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
the SSH Server will also come in handy.

