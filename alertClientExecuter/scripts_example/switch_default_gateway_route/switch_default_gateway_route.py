#!/usr/bin/python3

import sys
import os

# the ip address of the gateway you normally use
normal_gateway = "10.42.42.1"

# the content of the /etc/resolv.conf when used normally
normal_resolv_conf = "domain h4des.org\n" \
	+ "search h4des.org\n" \
	+ "nameserver 10.42.42.1"

# the ip address of the gateway you want to switch to when
# the normal gateway does not provide an internet connection
alternative_gateway = "192.168.1.1"

# the content of the /etc/resolv.conf when the alternative route is used
alternative_resolv_conf = "nameserver 8.8.8.8"


if len(sys.argv) != 2:
	print("Usage: %s <normal|alternative>" % sys.argv[0])
	sys.exit(0)

# changing routes in the OS needs root permissions
if os.geteuid() != 0:
	print("Script needs root permissions.")
	sys.exit(1)

if sys.argv[1] == "normal":
	print("Switching to normal route.")

	# delete old default gateway
	exit_code = os.system("route del default gw " + alternative_gateway)

	if exit_code != 0 and exit_code != 7 and exit_code != 1792:
		print("Deleting default route failed.")
		sys.exit(1)

	# add new default gateway
	exit_code = os.system("route add default gw " + normal_gateway)

	if exit_code != 0 and exit_code != 7 and exit_code != 1792:
		print("Adding default route failed.")
		sys.exit(1)

	# replace resolv.conf with the normally used content
	with open("/etc/resolv.conf", 'w') as fp:
		fp.write(normal_resolv_conf)

	print("Done.")

elif sys.argv[1] == "alternative":
	print("Switching to alternative route.")

	# delete old default gateway
	exit_code = os.system("route del default gw " + normal_gateway)

	if exit_code != 0 and exit_code != 7 and exit_code != 1792:
		print("Deleting default route failed.")
		sys.exit(1)

	# add new default gateway
	exit_code = os.system("route add default gw " + alternative_gateway)

	if exit_code != 0 and exit_code != 7 and exit_code != 1792:
		print("Adding default route failed.")
		sys.exit(1)

	# replace resolv.conf with the alternatively used content
	with open("/etc/resolv.conf", 'w') as fp:
		fp.write(alternative_resolv_conf)

	print("Done.")

else:
	print("Invalid argument.")
	sys.exit(1)