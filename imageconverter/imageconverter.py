#!/usr/bin/env python
import sys,os
from PIL import Image
import numpy as np


class imageconverter:
    def __init__(self, imagedata):
        self.im = Image.open(imagedata).convert('RGB')
        #self.im.show()
        self.arr = np.copy(np.asarray(self.im))
        # Flip every other row
        #print  "Before:" , repr(self.arr)
        for i in range(len(self.arr)):
            if ((i % 2) == 0):
                # no, too smart for it's own good
                #self.arr[i] = np.fliplr(self.arr[i])
                self.arr[i] = self.arr[i][::-1]
                pass
        #print  "After:" , repr(self.arr)
        #self.im = Image.fromarray(self.arr)
        #self.im.show()
        self.bytestream = self.arr.flatten()

# Another small bit of boilerplate
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "usage ./imageconverter.py imagefile"
    c = imageconverter(sys.argv[1])
    im = Image.fromarray(c.arr)
    im.show()
    
    
