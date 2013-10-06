#!/usr/bin/python
import sys,os,time
import threading

class handler:
    def __init__(self, port):
        port.setDTR(False) # Reset the arduino by driving DTR for a moment (RS323 signals are active-low)
        time.sleep(0.050)
        port.setDTR(True)
        self.port = port
        self.receiver_thread = threading.Thread(target=self.serial_reader)
        self.receiver_thread.setDaemon(1)
        self.receiver_thread.start()

    def serial_reader(self):
        while True:
            if not self.port.inWaiting():
                # Don't try to read if there is no data, instead sleep (yield) a bit
                time.sleep(0.01)
                continue
            data = self.port.read(1)
            if len(data) == 0:
                continue
            if data not in "\r\n":
                sys.stdout.write(repr(data))
        #        sys.stdout.write(" 0x".join(binascii.hexlify(data)))
        # Interestingly enough this comes mixed in with the previous output
        #        if data in string.letters.join(string.digits).join(string.punctuation):
        #            sys.stdout.write("(%s)" % data)
            else:
                sys.stdout.write(data)

    def send(self, img):
        c = imageconverter(img)
        self.port.write(chr(0x2))
        #print "STX",
        for byte in c.bytestream:
            encoded = chr(byte).encode('hex')
            self.port.write(encoded)
            #print encoded,
        self.port.write(chr(0x3))
        #print "ETX"
        time.sleep(5)

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

