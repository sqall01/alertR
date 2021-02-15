import logging
import threading
import time
from unittest import TestCase
from typing import Dict


class Timer:

    _running_timers = {}  # type: Dict[str, bool]
    _running_timers_lock = threading.Lock()

    @staticmethod
    def _set_timer(ctx: TestCase, desc: str, timeout: int):
        """
        Internal function used to have timeout if we are in a blocking function.
        :param ctx: context of the test case
        :param desc: description of the timeout
        :param timeout: timeout in seconds
        """

        for i in range(timeout):
            with Timer._running_timers_lock:
                if not Timer._running_timers[desc]:
                    return
            time.sleep(1)

        ctx.fail("Timeout: %s" % desc)

    @staticmethod
    def start_timer(ctx: TestCase, desc: str, timeout: int):

        with Timer._running_timers_lock:
            Timer._running_timers[desc] = True

        thread = threading.Thread(target=Timer._set_timer,
                                  args=(ctx, desc, timeout),
                                  daemon=False)
        thread.start()

    @staticmethod
    def stop_timer(desc: str):
        with Timer._running_timers_lock:
            Timer._running_timers[desc] = False


def config_logging(loglevel):
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=loglevel)
