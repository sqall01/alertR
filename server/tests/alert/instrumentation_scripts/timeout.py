#!/usr/bin/env python3

"""
Test instrumentation script which waits for 60 seconds before it outputs the received argument.
"""

import sys
import time

time.sleep(60)
print(sys.argv[1])
