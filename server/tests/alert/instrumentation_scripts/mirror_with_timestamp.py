#!/usr/bin/env python3

"""
Test instrumentation script which simply outputs the received argument with an additional timestamp.
"""

import sys
import time
import json

data = json.loads(sys.argv[1])
data["hasOptionalData"] = True
data["optionalData"] = dict()
data["optionalData"]["timestamp"] = int(time.time())

print(json.dumps(data))
