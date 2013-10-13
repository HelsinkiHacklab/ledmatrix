#!/usr/bin/python
import sys,os,time
import zmq

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "usage ./echotest.py tcp://whatever:6969"
    data = [ chr(0xde), chr(0xad), chr(0xbe), chr(0xef) ]

    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(sys.argv[1])
    
    socket.send(''.join(data))
    print "Sent %s" % repr(data)
    rpl = socket.recv()
    print "Got reply %s" % repr(rpl)
