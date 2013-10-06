#!/usr/bin/env python
import sys,os
from PIL import Image
import numpy as np


class imageconverter:
    def __init__(self, imagedata):
        self.im = Image.open(imagedata).convert('RGB')
        #self.im.show()
        self.arr1 = np.asarray(self.im)
        self.arr2 = np.ndarray(shape=(7,31,3), dtype=np.uint8)
        # Flip every other row
        #print  "Before:" , repr(self.arr1)
        for i in range(len(self.arr1)):
            if ((i % 2) == 0):
                self.arr2[i] = self.arr1[i][::-1]
            else:
                self.arr2[i] = self.arr1[i]
        #print  "After:" , repr(self.arr2)
        #self.im = Image.fromarray(self.arr2)
        #self.im.show()
        self.bytestream = self.arr2.flatten()

# Another small bit of boilerplate
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "usage ./imageconverter.py imagefile"
    c = imageconverter(sys.argv[1])
    #im = Image.fromarray(c.arr2)
    #im.show()
    
    
