#!/usr/bin/env python3

"""
Test script which writes into FIFO file.
"""

import os
import sys
import time

fifo_file = sys.argv[1]
start = int(sys.argv[2])
end = int(sys.argv[3])

for i in range(start, end):
    while True:
        with open(fifo_file, "w") as fp:
            fp.write(str(i) + "\n")
        break
