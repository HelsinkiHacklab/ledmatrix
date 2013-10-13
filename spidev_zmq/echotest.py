#!/usr/bin/python
import sys,os,time
import zmq
import random

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "usage ./echotest.py tcp://whatever:6969 uptobytes"
        
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(sys.argv[1])

    for x in range(1, int(sys.argv[2]
        data = [ chr(random.randint(0,255)) for xx in range(1,x) ]
        datastr = ''.join(data)
        socket.send()
        print "Sent %s" % repr(datastr)
        rpl = socket.recv()
        print "Got reply %s" % repr(rpl)
