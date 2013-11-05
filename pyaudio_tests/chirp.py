#!/usr/bin/env python
import sys
import pyaudio
import numpy, scipy
import scipy.signal

sampleRate=44100
#sampleRate=1000
bufferSize=2**10 # 1024

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=sampleRate, input=False, output=True, frames_per_buffer=bufferSize)

chirp_start_hz = 20.0
chirp_end_hz = 1500.0
chirp_time_s = 3

# TODO: Probably should do multiple consequtive sweeps instead of calculating all this into memory in one go...
sampletimes = numpy.linspace(0.0, chirp_time_s, chirp_time_s*sampleRate)
chirpdata = scipy.signal.chirp(sampletimes, chirp_start_hz, chirp_time_s, chirp_end_hz)
audio_chirp = numpy.interp(chirpdata, [-1.0, 1.0], [0, 2**16-1]).astype(numpy.uint16)

stream.write(audio_chirp)

