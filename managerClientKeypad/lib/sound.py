#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

import threading
import logging
import os
import pyaudio
import wave


# enum class for audio options
class AudioOptions:
	activating = 0
	activatingDelayed = 1
	deactivating = 2


# class that outputs all audio
class AudioOutput:

	def __init__(self):

		# file nme of this file (used for logging)
		self.fileName = os.path.basename(__file__)

		self.chunkSize = 1024

		self.soundDirectory = os.path.dirname(os.path.abspath(__file__)) \
			+ "/../sounds/"

		# lock that is being used so only one thread can play sounds
		self.soundLock = threading.BoundedSemaphore(1)


	# internal function that acquires the lock
	def _acquireLock(self):
		logging.debug("[%s]: Acquire lock." % self.fileName)
		self.soundLock.acquire()


	# internal function that releases the lock
	def _releaseLock(self):
		logging.debug("[%s]: Release lock." % self.fileName)
		self.soundLock.release()


	# plays the given wave file
	def _playFile(self, fileLocation):

		logging.debug("[%s]: Playing wave file '%s'."
				% (self.fileName, fileLocation))

		# open wave file
		waveFile = None
		try:
			waveFile = wave.open(fileLocation, 'rb')
		except Exception as e:
			logging.exception("[%s]: Could not open wave file '%s'."
				% (self.fileName, fileLocation))
			return

		# open player stream
		player = None
		stream = None
		try:
			player = pyaudio.PyAudio()
			stream = player.open(
				format=player.get_format_from_width(waveFile.getsampwidth()),
				channels=waveFile.getnchannels(),
				rate=waveFile.getframerate(),
				output=True)
		except Exception as e:
			logging.exception("[%s]: Could not open player stream."
				% self.fileName)
			return

		# write stream data
		try:
			data = waveFile.readframes(self.chunkSize)
			while len(data) > 0:
				stream.write(data)
				data = waveFile.readframes(self.chunkSize)
		except Exception as e:
			logging.exception("[%s]: Not able to write stream data."
				% self.fileName)
			return

		# stop and close player stream
		try:
			stream.stop_stream()
			stream.close()
			player.terminate()
		except Exception as e:
			logging.exception("[%s]: Not able to close player stream."
				% self.fileName)
			return


	def audioActivating(self):
		self._acquireLock()
		self._playFile(self.soundDirectory + "activating.wav")
		self._releaseLock()


	def audioDeactivating(self):
		self._acquireLock()
		self._playFile(self.soundDirectory + "deactivating.wav")
		self._releaseLock()


	def audioActivatingDelayed(self):
		self._acquireLock()
		self._playFile(self.soundDirectory + "activating_delayed.wav")
		self._releaseLock()