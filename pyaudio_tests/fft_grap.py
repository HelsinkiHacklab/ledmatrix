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

weighting_divider = 64
weighting = numpy.ndarray(shape=(MATRIX_W))
weighting.fill(2)
for x in range(MATRIX_W):
    ex = int(x/2)
    if ex < 1:
        continue
    weighting[x] = 2*ex
weighting[0] = 0.5
#print weighting

bufferSize=2**10
sampleRate=44100 

p = pyaudio.PyAudio()


# From http://stackoverflow.com/questions/12344951/detect-beat-and-play-wav-file-in-a-syncronised-manner
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

        self.imagearray = numpy.ndarray(shape=(MATRIX_H,MATRIX_W,3), dtype=numpy.uint8)
        self.imagearray.fill(0)
        self.update_image()

        self.chunks = []
        self.beatdetector = SimpleBeatDetection()
        self.beat_is_on = False
        self.inStream = p.open(format=pyaudio.paInt16, channels=1, rate=sampleRate, input=True, frames_per_buffer=bufferSize)

        #self.audio_timer = QtCore.QTimer()
        #self.audio_timer.timeout.connect(self.read_audio)
        #self.audio_timer.start(0)

        self.analyze_timer = QtCore.QTimer()
        self.analyze_timer.timeout.connect(self.analyze_audio)
        self.analyze_timer.start(5)


    def read_audio(self):
        self.chunks.append(self.inStream.read(bufferSize))

    # Return power array index corresponding to a particular frequency
    def piff(self, val):
        #return int(2*bufferSize*val/sampleRate)
        return int(bufferSize*val/sampleRate)
    
    # Visualizing code from http://www.raspberrypi.org/phpBB3/viewtopic.php?p=314087
    def calculate_levels(self, signal):
        matrix =  numpy.ndarray(shape=(MATRIX_W))
        # Apply FFT - real data
        fourier=numpy.fft.rfft(signal)
        # Remove last element in array to make it the same size as chunk
        #fourier=numpy.delete(fourier,len(fourier)-1)
        # Find average 'amplitude' for specific frequency ranges in Hz
        power = numpy.abs(fourier)
        maxfreq = sampleRate/2.0
        bandwidth = maxfreq/MATRIX_W
        for x in range(MATRIX_W):
            bin_start = int(x*bandwidth)
            bin_end = int((x+1)*bandwidth)
            #print "bin %d from %d to %d" % (x, bin_start, bin_end)
            matrix[x] = int(numpy.mean(power[self.piff(bin_start):self.piff(bin_end):1]))
            #print "bin %d from %d to %d power %f" % (x, bin_start, bin_end, matrix[x])
        # Tidy up column values for the LED matrix
        #print matrix
        matrix=numpy.divide(numpy.multiply(matrix,weighting),weighting_divider)
        #print matrix
        # Set floor at 0 and ceiling at 8 for LED matrix
        matrix=matrix.clip(0,MATRIX_H) 
        return matrix

    def analyze_audio(self):
        self.read_audio()
        if len(self.chunks) > 0:
            data = self.chunks.pop(0)
            signal = numpy.frombuffer(data, numpy.int16)
            #print signal
            beat = self.beatdetector.detect_beat(signal)
            if (beat):
                self.beat_on()
                QtCore.QTimer.singleShot(BEAT_TIME, self.beat_off)
            self.levels = self.calculate_levels(signal)
            self.draw_levels()

        if len(self.chunks) > 20:
            print "falling behind, %d chunks in queue"  % len(self.chunks)

    def draw_levels(self):
        # Start by filling according to beat
        if self.beat_is_on:
            self.imagearray.fill(255)
        else:
            self.imagearray.fill(0)

        for y in range(MATRIX_H):
            for x in range(MATRIX_W):
                if self.levels[x] >= y:
                    self.imagearray[(MATRIX_H-1)-y][x] = (255,0,0)

        self.update_image()

    def beat_on(self):
        self.beat_is_on = True
        #self.imagearray.fill(255)
        #self.update_image()

    def beat_off(self):
        self.beat_is_on = False
        #self.imagearray.fill(0)
        #self.update_image()

    def update_image(self):
        self.PilImage = Image.fromarray(self.imagearray)
        self.PilImage = self.PilImage.resize((MATRIX_W*FFT_QT_SCALE, MATRIX_H*FFT_QT_SCALE), Image.BILINEAR)
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
