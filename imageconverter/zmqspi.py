#!/usr/bin/python
import sys,os,time
import zmq

class handler:
    def __init__(self, zmq_socket):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(zmq_socket)

    def send_frame(self, c):
        #bytestring = ''.join(c.bytestream)
        #self.socket.send(bytestring)
        self.socket.send(c.bytestream)
        # We must read the reply even if we do not expect to use it
        dummy = self.socket.recv()

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

    def loop(self, img, count=False):
        c = imageconverter(img)
        while True:
            self.send_frame(c)
            if c.im.info.has_key('duration'):
                time.sleep(float(c.im.info['duration'])/1000)
            while c.seek():
                self.send_frame(c)
                time.sleep(float(c.im.info['duration'])/1000)
            c.seek(0)


if __name__ == '__main__':
    from imageconverter import imageconverter
    if len(sys.argv) < 3:
        print "usage ./zmqspi.py imagefile tcp://whatever:6969"
        sys.exit(1)

    h = handler(sys.argv[2])
    #h.send(sys.argv[1])
    h.loop(sys.argv[1])

