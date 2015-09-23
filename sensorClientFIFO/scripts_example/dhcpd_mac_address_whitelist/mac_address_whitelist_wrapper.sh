#!/bin/bash

# isc-dhcp-server can not start scripts in the background
# therefore this script does it
# this way isc-dhcp-server does not block until the script finishes its job
/absolute/path/to/mac_address_whitelist.py $1 $2 &