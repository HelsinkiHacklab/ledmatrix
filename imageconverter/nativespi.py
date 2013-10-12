#!/usr/bin/python
import sys,os,time
from spi import spi_transfer, SPIDev
SPI_DEV = '/dev/spidev4.0'
SPEED = 1000000

class handler:
    def __init__(self, port):
        self.dev = SPIDev(SPI_DEV)

    def send_frame(self, c):
        transfer, buf, _ = spi_transfer(c.bytestream, readlen=0, speed=SPEED)
    
        self.send_and_wait(chr(0x2))
        #print "STX",
        for byte in c.bytestream:
            encoded = chr(byte).encode('hex')
            self.send_and_wait(encoded)
            #print encoded,
        self.send_and_wait(chr(0x3))

    def send(self, img):
        c = imageconverter(img)
        self.send_frame(c)
        # IF there are animation frames, send rest of them too
        #c.rgbim.show()
        # TODO: account for the time spent transferring the frame
        if c.im.info.has_key('duration'):
            time.sleep(float(c.im.info['duration'])/1000)
        while c.seek():
            self.send_frame(c)
            #c.rgbim.show()
            time.sleep(float(c.im.info['duration'])/1000)

        time.sleep(1)
        #print "ETX"

if __name__ == '__main__':
    from imageconverter import imageconverter
    if len(sys.argv) < 2:
        print "usage ./main.py imagefile"

    import ConfigParser, os, sys, serial
    config = ConfigParser.SafeConfigParser()
    if not os.path.isfile('spi.ini'):
        config.add_section('modem')
        config.set('modem', 'port', '/dev/whatever')
        with open('spi.ini', 'wb') as configfile:
            config.write(configfile)
        print "Edit spi.ini for your modem port"
        sys.exit(1)
    config.read('spi.ini')
    port = serial.Serial(config.get('modem', 'port'), 115200)
    h = handler(port)
    time.sleep(2)
    h.send(sys.argv[1])

root@beaglebian2g:/opt/ledmatrix# 
