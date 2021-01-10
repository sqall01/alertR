#!/usr/bin/env python3

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

    def __init__(self, play_silence: bool):

        self._log_tag = os.path.basename(__file__)

        self._chunk_size = 1024

        self.sound_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "sounds")

        # lock that is being used so only one thread can play sounds
        self._sound_lock = threading.Lock()

        if play_silence:
            self._play_silence()

    # plays the given wave file with the help of aplay
    # (used pyaudio before, but could not suppress the console output)
    def _play_file(self, **kwargs):
        file_location = kwargs["file"]
        with self._sound_lock:
            logging.debug("[%s]: Playing wave file '%s'." % (self._log_tag, file_location))

            p = subprocess.Popen(["aplay", file_location],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

            exit_code = p.wait()
            out, err = p.communicate()

            if exit_code != 0:
                logging.error("[%s]: Could not play wave file '%s'." % (self._log_tag, file_location))

                logging.error("[%s]: Error message: %s" % (self._log_tag, err))

    def _play_silence(self):
        logging.debug("[%s]: Playing silence." % self._log_tag)
        dev_zero = open("/dev/zero", "rb")
        subprocess.Popen(["aplay", "-c", "2", "-r", "48000", "-f", "S16_LE"], stdin=dev_zero)

    def audio_profile_change(self):
        kwargs = {"file": os.path.join(self.sound_directory, "profile_change.wav")}
        threading.Thread(target=self._play_file, kwargs=kwargs, daemon=True).start()

    def audio_profile_change_delayed(self):
        kwargs = {"file": os.path.join(self.sound_directory, "profile_change_delayed.wav")}
        threading.Thread(target=self._play_file, kwargs=kwargs, daemon=True).start()

    def audio_warning(self):
        kwargs = {"file": os.path.join(self.sound_directory, "warning.wav")}
        threading.Thread(target=self._play_file, kwargs=kwargs, daemon=True).start()
