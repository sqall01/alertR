#!/usr/bin/python3

"""
Test instrumentation script which simply outputs the received argument and exits with exit code 1.
"""

import sys

print(sys.argv[1])
sys.exit(1)
