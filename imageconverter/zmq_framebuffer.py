#!/usr/bin/python
import sys,os,time
import zmq
from zmq.eventloop import ioloop
ioloop.install()
from zmq.eventloop.zmqstream import ZMQStream

try:
    import numpy as np
    have_np = True
except ImportError:
    pass

MATRIX_W = 31
MATRIX_H = 7


SERVICE_PORT = 6868

class handler:
    def __init__(self, zmq_send_socket):
        self.send_context = zmq.Context()
        self.send_socket = self.send_context.socket(zmq.REQ)
        self.send_socket.connect(zmq_send_socket)

        self.recv_context = zmq.Context()
        self.recv_socket = self.recv_context.socket(zmq.ROUTER)
        self.recv_socket.bind("tcp://*:%d" % SERVICE_PORT)
        self.stream = ZMQStream(self.recv_socket)

        self.stream.on_recv(self.send_frame)

        if have_np:
            self.arr1 = np.ndarray(shape=(MATRIX_H,MATRIX_W,3), dtype=np.uint8)
            self.arr2 = np.ndarray(shape=(MATRIX_H,MATRIX_W,3), dtype=np.uint8)
        else:
            self.arr1 = [ [ [ xxx for xxx in range(3) ] for xx in range(MATRIX_W) ] for x in range(MATRIX_H) ]
            self.arr2 = [ [ [ xxx for xxx in range(3) ] for xx in range(MATRIX_W) ] for x in range(MATRIX_H) ]


    def send_frame(self, datalist):
        client_id = datalist[0]
        input_bytestream = datalist[1:]
        # Slice the input into a matrix
        for y in range(MATRIX_H):
            y_slice_start = y*MATRIX_W
            for x in range(MATRIX_W):
                x_slice_start = y_slice_start+(3*x)
                self.arr1 = input_bytestream[x_slice_start:x_slice_start+3]

        # Flip every other row
        for i in range(len(self.arr1)):
            if ((i % 2) == 0):
                self.arr2[i] = self.arr1[i][::-1]
            else:
                self.arr2[i] = self.arr1[i]

        self.bytestream = self.arr2.flatten()

        self.send_socket.send(self.bytestream)
        # We must read the reply even if we do not expect to use it
        dummy = self.send_socket.recv()

    def run(self):
        ioloop.IOLoop.instance().start()



if __name__ == '__main__':
    from imageconverter import imageconverter
    if len(sys.argv) < 3:
        print "usage ./zmq_framebuffer.py tcp://whatever:6969"
        sys.exit(1)

    h = handler(sys.argv[1])
    h.run()


