#!/usr/bin/python3

"""
Test instrumentation script which simply outputs the received argument with an toggled state.
"""

import sys
import time
import json

data = json.loads(sys.argv[1])
data["state"] = 1 - data["state"]

print(json.dumps(data))
