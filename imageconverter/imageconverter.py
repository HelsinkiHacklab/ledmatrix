#!/usr/bin/env python
import sys,os
from PIL import Image
import numpy as np


class imageconverter:
    def __init__(self, imagedata):
        self.im = Image.open(imagedata).convert('RGB')
        self.arr = np.asarray(self.im)
        


# Another small bit of boilerplate
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "usage ./imageconverter.py imagefile"
    c = imageconverter(sys.argv[1])
    print c.arr
    
