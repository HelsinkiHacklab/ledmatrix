#!/usr/bin/env python
import sys,os
import time
from PyQt4 import QtCore, QtGui
from PIL import Image, ImageOps, ImageQt
import pyaudio
import numpy


# the 31x7 matrix...
MATRIX_W=31
MATRIX_H=7
FFT_QT_SCALE=10
BEAT_TIME=10

#ADJUST THIS TO CHANGE SPEED/SIZE OF FFT
#bufferSize=2**11
bufferSize=2**10

# ADJUST THIS TO CHANGE SPEED/SIZE OF FFT
sampleRate=44100 

p = pyaudio.PyAudio()


class SimpleBeatDetection:
    """
    Simple beat detection algorithm from
    http://archive.gamedev.net/archive/reference/programming/features/beatdetection/index.html
    """
    def __init__(self, history = 43): # 43 ought to be good default for 44100 sample rate and 1024 sample chunk size
        self.local_energy = numpy.zeros(history) # a simple ring buffer
        self.local_energy_index = 0 # the index of the oldest element

    def detect_beat(self, signal):

        samples = signal.astype(numpy.int) # make room for squares
        # optimized sum of squares, i.e faster version of (samples**2).sum()
        instant_energy = numpy.dot(samples, samples) / float(0xffffffff) # normalize

        local_energy_average = self.local_energy.mean()
        local_energy_variance = self.local_energy.var()

        # TODO: Is that 1.15142857 the C the algorithm refers to  ??
        beat_sensibility = (-0.0025714 * local_energy_variance) + 1.15142857
        beat = instant_energy > beat_sensibility * local_energy_average

        self.local_energy[self.local_energy_index] = instant_energy
        self.local_energy_index -= 1
        if self.local_energy_index < 0:
            self.local_energy_index = len(self.local_energy) - 1

        return beat



class MyWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        
        self.canvasx = MATRIX_W*FFT_QT_SCALE
        self.canvasy = MATRIX_H*FFT_QT_SCALE

        self.setGeometry(self.canvasx, self.canvasy, self.canvasx, self.canvasy)
        self.setWindowTitle('%dx%d scaled by %d' % (MATRIX_W, MATRIX_H, FFT_QT_SCALE))
        self.label = QtGui.QLabel('', self)

        self.imagearray = numpy.ndarray(shape=(self.canvasy,self.canvasx,3), dtype=numpy.uint8)
        self.update_image()

        self.chunks = []
        self.beats = SimpleBeatDetection()
        self.inStream = p.open(format=pyaudio.paInt16, channels=1, rate=sampleRate, input=True, frames_per_buffer=bufferSize)

        self.audio_timer = QtCore.QTimer()
        self.audio_timer.timeout.connect(self.read_audio)
        self.audio_timer.start(0)

        self.analyze_timer = QtCore.QTimer()
        self.analyze_timer.timeout.connect(self.analyze_audio)
        self.analyze_timer.start(0)


    def beat_on(self):
        #print "BEAT"
        self.imagearray.fill(255)
        self.update_image()

    def beat_off(self):
        self.imagearray.fill(0)
        self.update_image()

    def read_audio(self):
        self.chunks.append(self.inStream.read(bufferSize))

    def analyze_audio(self):
        if len(self.chunks) > 0:
            data = self.chunks.pop(0)
            signal = numpy.frombuffer(data, numpy.int16)
            #print signal
            beat = self.beats.detect_beat(signal)
            if (beat):
                self.beat_on()
                QtCore.QTimer.singleShot(BEAT_TIME, self.beat_off)

        if len(self.chunks) > 20:
            print "falling behind, %d chunks in queue"  % len(self.chunks)
        
    def update_image(self):
        self.PilImage = Image.fromarray(self.imagearray)
        self.update_pixmap()

    def update_pixmap(self):
        QtImage1 = ImageQt.ImageQt(self.PilImage)
        QtImage2 = QtImage1.copy()
        pixmap = QtGui.QPixmap.fromImage(QtImage2)
        self.label.setPixmap(pixmap)

    def invert(self):
        self.PilImage = ImageOps.invert(self.PilImage)
        self.update_image()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    myWidget = MyWidget()
    myWidget.show()
    sys.exit(app.exec_())
