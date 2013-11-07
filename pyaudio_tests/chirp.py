#!/usr/bin/env python
import sys
import pyaudio
import numpy, scipy
import scipy.signal
from scipy.io.wavfile import write

sampleRate=44100

chirp_start_hz = 50.0
chirp_end_hz = 15000.0
chirp_time_s = 15.0

sampletimes = numpy.linspace(0.0, chirp_time_s, chirp_time_s*sampleRate)
chirpdata = scipy.signal.chirp(sampletimes, chirp_start_hz, chirp_time_s, chirp_end_hz)
audio_chirp = numpy.interp(chirpdata, [-1.0, 1.0], [-1*2**15, 2**15-1]).astype(numpy.int16)

write('test.wav', sampleRate, audio_chirp)

