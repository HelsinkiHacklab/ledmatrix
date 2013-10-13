#!/usr/bin/python
import sys,os,time
from spi import spi_transfer, SPIDev
SPI_DEV = '/dev/spidev4.0'
SPEED = 1000000

class handler:
    def __init__(self):
        # This fails on the BeagleBoard at least, gets an exception from ioctl(self._no, param, ctypes.addressof(value)) implying something does not fit in something
        self.dev = SPIDev(SPI_DEV)
        self.databuffer = None
        self.spitransfer = None

    def send_frame(self, c):
        bytestring = ''.join(c.bytestream)
        # Initialize the buffer once (after we have the first set of image data)
        if (   not self.databuffer
            or not self.spitransfer):
            self.transfer, self.databuffer, _ = spi_transfer(bytestring, readlen=0, speedhz=SPEED)
        self.databuffer = bytestring
        self.dev.do_transfers([self.transfer])

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

if __name__ == '__main__':
    from imageconverter import imageconverter
    if len(sys.argv) < 2:
        print "usage ./main.py imagefile"

    h.send(sys.argv[1])
