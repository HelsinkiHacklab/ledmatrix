#!/usr/bin/env python
from __future__ import with_statement
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

# This stuff is used by the older FFT to led bars code I lifted from RPI forums, will be removed
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

# Audio setup
bufferSize=2**10
sampleRate=44100 
# low and high end of that we are interedted in visualizing.
spectrogram_lowpass=50 # hz
spectrogram_highpass=12000 # hz



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

class ZMQThread(QtCore.QThread):
    def __init__(self, view):
        QtCore.QThread.__init__(self)
        self.view = view
        self.connect(self.view, QtCore.SIGNAL('update_matrix()'), self.update_matrix)

    def run(self):
        while(True):
            time.sleep(0) # Yield
        return

    def update_matrix(self):
        # Switch the lines that need switching
        for i in range(len(self.view.imagearray)):
            if ((i % 2) == 0):
                self.view.imagearray_switched[i] = self.view.imagearray[i][::-1]
            else:
                self.view.imagearray_switched[i] = self.view.imagearray[i]
        # and output
        self.view.zmq_socket.send(self.view.imagearray_switched.flatten())
        # We have to get the reply even if we do not care about it
        self.view.zmq_socket.recv()
        

class PreviewWindow(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        
        self.zmq_socket = None
        self.canvasx = MATRIX_W*FFT_QT_SCALE
        self.canvasy = MATRIX_H*FFT_QT_SCALE

        self.setGeometry(self.canvasx, self.canvasy, self.canvasx, self.canvasy)
        self.setWindowTitle('%dx%d scaled by %d' % (MATRIX_W, MATRIX_H, FFT_QT_SCALE))
        self.label = QtGui.QLabel('', self)

        self.imagearray = numpy.ndarray(shape=(MATRIX_H,MATRIX_W,3), dtype=numpy.uint8)
        self.imagearray_switched = numpy.ndarray(shape=(MATRIX_H,MATRIX_W,3), dtype=numpy.uint8)
        self.imagearray.fill(0)
        self.update_image()

        self.chunks = []
        self.beatdetector = SimpleBeatDetection()
        self.beat_is_on = False

        # Read audio as fast as feasible (though the read method probably blocks so maybe this should be a separate thread, or better probably to switch to the callback version)
        self.audio_timer = QtCore.QTimer()
        self.audio_timer.timeout.connect(self.read_audio)
        self.audio_timer.start(0)

        # Analyze the audio data we got every X ms
        self.analyze_timer = QtCore.QTimer()
        self.analyze_timer.timeout.connect(self.analyze_audio)
        self.analyze_timer.start(0)

        # Kick up a thread to handle the ZQM coms
        self.zmqthread = ZMQThread(self)
        self.zmqthread.start()

        # Update the matrix every X ms
        self.update_matrix_timer = QtCore.QTimer()
        self.update_matrix_timer.timeout.connect(self.update_matrix)
        self.update_matrix_timer.start(20)


    def read_audio(self):
        self.chunks.append(self.inStream.read(bufferSize))

    # Return power array index corresponding to a particular frequency
    def piff(self, val):
        #return int(2*bufferSize*val/sampleRate)
        return int(bufferSize*val/sampleRate)
    
    # Visualizing code from http://www.raspberrypi.org/phpBB3/viewtopic.php?p=314087
    def calculate_levels_old(self, signal):
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

    def calculate_levels(self, pcm):
        binpower =  numpy.ndarray(shape=(MATRIX_W))

        fft = numpy.fft.fft(pcm)
        fftr = 10*numpy.log10(abs(fft.real))[:len(pcm)/2]
        ffti = 10*numpy.log10(abs(fft.imag))[:len(pcm)/2]
        fftb = 10*numpy.log10(numpy.sqrt(fft.imag**2+fft.real**2))[:len(pcm)/2]
        freq = numpy.fft.fftfreq(numpy.arange(len(pcm)).shape[-1])[:len(pcm)/2]
        freq = freq*sampleRate #make the frequency scale

        # There is probably a much better way but can't be bothered right now.        
        while (freq[0] < spectrogram_lowpass):
            # Drop frequency bins until we are above our cutoff
            fftb = numpy.delete(fftb,0)
            freq = numpy.delete(freq,0)
        while (freq[-1] > spectrogram_highpass):
            # Drop frequency bins until we are above our cutoff
            fftb = numpy.delete(fftb,-1)
            freq = numpy.delete(freq,-1)

        #print fftb
        #print freq
        # TODO: Bin levels by octaves not linearly http://stackoverflow.com/questions/604453/analyze-audio-using-fast-fourier-transform
        fft_size = len(fftb)
        bin_size = float(fft_size/MATRIX_W)
        if (bin_size != int(bin_size)):
            # This case is probably not handled properly
            #print "bin_size %f may be problematic" % bin_size
            pass
        for x in range(MATRIX_W):
            startidx = int(x*bin_size)
            endidx = int((x+1)*bin_size)
            #print "slot %d data %s" % (x, fftb[startidx:endidx])
            binpower[x] = numpy.mean(fftb[startidx:endidx])

        #print binpower
        for x in range(MATRIX_W):
            # map to 0-7
            binpower[x] = int(round(numpy.interp(binpower[x], [6,30],[-1,7])))
        #print binpower
        return binpower



    def analyze_audio(self):
        if len(self.chunks) > 5:
            print "falling behind, %d chunks in queue"  % len(self.chunks)

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


    def update_matrix(self):
        self.emit(QtCore.SIGNAL('update_matrix()'))

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
    myWidget = PreviewWindow()
    p = pyaudio.PyAudio()
    myWidget.inStream = p.open(format=pyaudio.paInt16, channels=1, rate=sampleRate, input=True, frames_per_buffer=bufferSize)
    if len(sys.argv) > 1:
        import zmq
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.connect(sys.argv[1])
        myWidget.zmq_socket = socket

    myWidget.show()
    sys.exit(app.exec_())

    
