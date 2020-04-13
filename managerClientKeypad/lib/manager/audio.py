#!/usr/bin/python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import logging
import os
import subprocess
import threading


# class that outputs all audio
class AudioOutput:

    def __init__(self):

        # file nme of this file (used for logging)
        self.fileName = os.path.basename(__file__)

        self.chunkSize = 1024

        self.soundDirectory = os.path.dirname(os.path.abspath(__file__)) + "/../../sounds/"

        # lock that is being used so only one thread can play sounds
        self.soundLock = threading.BoundedSemaphore(1)

    # plays the given wave file with the help of aplay
    # (used pyaudio before, but could not suppress the console output)
    def _playFile(self, **kwargs):
        fileLocation = kwargs["file"]
        with self.soundLock:
            logging.debug("[%s]: Playing wave file '%s'." % (self.fileName, fileLocation))

            p = subprocess.Popen(["aplay", fileLocation],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

            exit_code = p.wait()
            out, err = p.communicate()

            if exit_code != 0:
                logging.error("[%s]: Could not play wave file '%s'." % (self.fileName, fileLocation))

                logging.error("[%s]: Error message: %s" % (self.fileName, err))

    def audioActivating(self):
        kwargs = {"file": self.soundDirectory + "activating.wav"}
        threading.Thread(target=self._playFile, kwargs=kwargs, daemon=True).start()

    def audioActivatingDelayed(self):
        kwargs = {"file": self.soundDirectory + "activating_delayed.wav"}
        threading.Thread(target=self._playFile, kwargs=kwargs, daemon=True).start()

    def audioDeactivating(self):
        kwargs = {"file": self.soundDirectory + "deactivating.wav"}
        threading.Thread(target=self._playFile, kwargs=kwargs, daemon=True).start()

    def audioWarning(self):
        kwargs = {"file": self.soundDirectory + "warning.wav"}
        threading.Thread(target=self._playFile, kwargs=kwargs, daemon=True).start()

    def playSilence(self):
        logging.debug("[%s]: Playing silence." % self.fileName)
        devZero = open("/dev/zero", "rb")
        subprocess.Popen(["aplay", "-c", "2", "-r", "48000", "-f", "S16_LE"], stdin=devZero)
