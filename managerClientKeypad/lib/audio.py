#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import threading
import logging
import os
import subprocess


# enum class for audio options
class AudioOptions:
	activating = 0
	activatingDelayed = 1
	deactivating = 2
	warning = 3


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


	# plays the given wave file with the help of aplay
	# (used pyaudio before, but could not suppress the console output)
	def _playFile(self, fileLocation):

		logging.debug("[%s]: Playing wave file '%s'."
				% (self.fileName, fileLocation))

		p = subprocess.Popen(["aplay", fileLocation], stdout=subprocess.PIPE,
			stderr=subprocess.PIPE)

		exit_code = p.wait()
		out, err = p.communicate()

		if exit_code != 0:
			logging.error("[%s]: Could not play wave file '%s'."
				% (self.fileName, fileLocation))

			logging.error("[%s]: Error message: %s"
				% (self.fileName, err))


	def audioActivating(self):
		self._acquireLock()
		self._playFile(self.soundDirectory + "activating.wav")
		self._releaseLock()


	def audioActivatingDelayed(self):
		self._acquireLock()
		self._playFile(self.soundDirectory + "activating_delayed.wav")
		self._releaseLock()


	def audioDeactivating(self):
		self._acquireLock()
		self._playFile(self.soundDirectory + "deactivating.wav")
		self._releaseLock()


	def audioWarning(self):
		self._acquireLock()
		self._playFile(self.soundDirectory + "warning.wav")
		self._releaseLock()


	def playSilence(self):
		logging.debug("[%s]: Playing silence." % self.fileName)

		devZero = open("/dev/zero", "rb")
		subprocess.Popen(["aplay", "-c", "2", "-r", "48000", "-f", "S16_LE"], stdin=devZero)