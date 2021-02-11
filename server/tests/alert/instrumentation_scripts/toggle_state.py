#!/usr/bin/env python3

"""
Test instrumentation script which simply outputs the received argument with an toggled state.
"""

import sys
import json

data = json.loads(sys.argv[1])
data["state"] = 1 - data["state"]

print(json.dumps(data))
