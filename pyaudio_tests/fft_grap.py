#!/usr/bin/env python
import sys,os
import time

import pyaudio
import scipy
import struct
import scipy.fftpack
import threading


#ADJUST THIS TO CHANGE SPEED/SIZE OF FFT
bufferSize=2**11
#bufferSize=2**8

# ADJUST THIS TO CHANGE SPEED/SIZE OF FFT
sampleRate=48100 
#sampleRate=64000

p = pyaudio.PyAudio()


class SimpleBeatDetection:
    """
    Simple beat detection algorithm from
    http://archive.gamedev.net/archive/reference/programming/features/beatdetection/index.html
    """
    def __init__(self, history = 43):
        self.local_energy = numpy.zeros(history) # a simple ring buffer
        self.local_energy_index = 0 # the index of the oldest element

    def detect_beat(self, signal):

        samples = signal.astype(numpy.int) # make room for squares
        # optimized sum of squares, i.e faster version of (samples**2).sum()
        instant_energy = numpy.dot(samples, samples) / float(0xffffffff) # normalize

        local_energy_average = self.local_energy.mean()
        local_energy_variance = self.local_energy.var()

        beat_sensibility = (-0.0025714 * local_energy_variance) + 1.15142857
        beat = instant_energy > beat_sensibility * local_energy_average

        self.local_energy[self.local_energy_index] = instant_energy
        self.local_energy_index -= 1
        if self.local_energy_index < 0:
            self.local_energy_index = len(self.local_energy) - 1

        return beat

class runner:
    def __init__(self):
        self.chunks = []
        self.beats = SimpleBeatDetection()
        self.inStream = p.open(format=pyaudio.paInt16, channels=1, rate=sampleRate, input=True, frames_per_buffer=bufferSize)

    def streamreader(self):
        while True:
            self.chunks.append(self.inStream.read(bufferSize))
            # yield
            time.sleep(0)

    
    def go(self):
        threading.Thread(target=self.streamreader).start()
        while True:
            if len(chunks) > 0:
                data = chunks.pop(0)
                signal = numpy.frombuffer(data, numpy.int16)
                beat = self.beats(signal)
                if (beat):
                    print "BEAT"
                # TODO: the FFT
                print signal

            if len(chunks) > 20:
                print "falling behind...",len(chunks)
            # yield
            time.sleep(0)





# Another small bit of boilerplate
if __name__ == '__main__':
    r = runner()
    r.go()
    pass
