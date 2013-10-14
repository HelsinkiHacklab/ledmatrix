#!/usr/bin/python
import sys,os,time
import zmq
import random

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "usage ./echotest.py tcp://whatever:6969 uptobytes [frombytes]"
        sys.exit(1)
        
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(sys.argv[1])

    tobytes = int(sys.argv[2])
    frombytes = 1
    if len(sys.argv) >= 4:
        frombytes = int(sys.argv[3])

    print "Iterating from %d to %d" % (frombytes, tobytes)
    for x in range(frombytes, tobytes):
        print "Iteration #%d" % x
        data = [ chr(random.randint(0,255)) for xx in range(1,x) ]
        datastr = ''.join(data)
        socket.send(datastr)
        print "Sent %s" % repr(datastr)
        rpl = socket.recv()
        print "Got reply (%d bytes): %s" % (len(rpl), repr(rpl))
