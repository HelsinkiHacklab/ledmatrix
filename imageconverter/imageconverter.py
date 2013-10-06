#!/usr/bin/env python
import sys,os
from PIL import Image, ImageOps
import numpy as np

MATRIX_W = 31
MATRIX_H = 7



class imageconverter:
    frame_count = 0

    def __init__(self, imagedata):
        self.im = Image.open(imagedata)
        self.frame_count = 0
        self.count_frames()
        self.calc_bytestream()

    def count_frames(self):
        try:
            while(True):
                self.frame_count = self.im.tell()
                self.im.seek(self.frame_count+1)
        except EOFError,e:
            pass
        self.im.seek(0)

    @property
    def current_frame(self):
        return self.im.tell()

    def seek(self, frame=None):
        """Seeks to next frame (or given frame but that is not always possible)"""
        if frame == None:
            if self.current_frame < self.frame_count:
                frame = self.current_frame+1
            else:
                return False
        self.im.seek(frame)
        self.calc_bytestream()
        if self.current_frame < self.frame_count:
            return True
        return False

    def calc_bytestream(self):
        self.rgbim = self.im.convert('RGB')
        if (   self.rgbim.size[0] > MATRIX_W
            or self.rgbim.size[1] > MATRIX_H):
            self.rgbim = ImageOps.fit(self.rgbim, (MATRIX_W,MATRIX_H), Image.ANTIALIAS)
        self.arr1 = np.asarray(self.rgbim)
        self.arr2 = np.ndarray(shape=(MATRIX_H,MATRIX_W,3), dtype=np.uint8)
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
    
    
