#!/usr/bin/python

import sys
import csv
import os
import subprocess
import time
import fcntl
import smtplib


# FIFO file of the alertR sensor client
FIFO_FILE = "/home/alertR/sensorClientFIFO/config/dhcpd.fifo"

# file that is used to synchronize the write access to the FIFO file
LOCK_FILE = "/tmp/alertR_mac_address.lockfile"

# should the unknown client be scanned via nmap?
# needs pip packet "python-nmap"
# => install via "pip install python-nmap"
SCAN_VIA_NMAP = True

# should an email be sent?
# It uses the local email service on the host system
SEND_EMAIL = True
FROM_ADDR = "alertR@h4des.org"
TO_ADDR = "targetAddr@somedomain.org"


if len(sys.argv) != 3:
	print "Usage: %s <client IP> <client MAC address>"
	sys.exit(0)

client_ip = sys.argv[1]
client_mac_address = sys.argv[2]

# check if mac address is whitelisted
found = False
with open(os.path.dirname(os.path.abspath(__file__)) + "/mac_address_whitelist.csv", 'rb') as csv_file:
	csv_reader = csv.reader(csv_file, quoting=csv.QUOTE_ALL)

	for row in csv_reader:
		if len(row) != 2:
			continue
		if row[0].find('#') != -1:
			continue

		mac_address = row[0]
		description = row[1]

		if client_mac_address == mac_address.lower():
			found = True
			break

if not found:

	# only scan unknown host via nmap if activated
	nm = None
	if SCAN_VIA_NMAP:

		# needs pip packet "python-nmap"
		# => install via "pip install python-nmap"
		import nmap

		nm = nmap.PortScanner()
		nm.scan(client_ip, arguments="")

		# create a string from the nmap scan
		nmap_result_string = ""
		for host in nm.all_hosts():
			for protocol in nm[host].all_protocols():
				port_list = nm[host][protocol].keys()
				port_list.sort()
				for port in port_list:
					nmap_result_string += "%d/%s/%s; " % (port, protocol,
						nm[host][protocol][port]['state'])
		if nmap_result_string == "":
			nmap_result_string = "None"

	# only send an email if it is activated
	if SEND_EMAIL:

		subject = "[alertR] DHCP lease for unknown client"

		message = "DHCP lease for an unknown client was detected.\n\n"
		message += "IP: %s\n" % client_ip
		message += "MAC: %s\n" % client_mac_address
		if not nm is None:
			message += "\nNmap scan results:\n"
			for host in nm.all_hosts():
				for protocol in nm[host].all_protocols():
					port_list = nm[host][protocol].keys()
					port_list.sort()
					for port in port_list:
						message += "%d/%s - %s - %s\n" % (port, protocol,
							nm[host][protocol][port]["state"],
							nm[host][protocol][port]['name'])

		email_header = "From: %s\r\nTo: %s\r\nSubject: %s\r\n" \
			% (FROM_ADDR, TO_ADDR, subject)

		try:
			smtp_server = smtplib.SMTP("127.0.0.1", 25)
			smtp_server.sendmail(FROM_ADDR, TO_ADDR, 
				email_header + message)
			smtp_server.quit()
		except Exception as e:
			pass

	# get file lock
	lock_fd = open(LOCK_FILE, 'w')
	fcntl.lockf(lock_fd, fcntl.LOCK_EX)

	# send message to alertR
	with open(FIFO_FILE, 'w') as fifo_file:

		if SCAN_VIA_NMAP:

			fifo_message = '{"message": "sensoralert", ' \
				+ '"payload": {' \
				+ '"state": 1, ' \
				+ '"hasOptionalData": true, ' \
				+ '"optionalData": {' \
				+ '"message": ' \
				+ '"Unknown client with IP: %s and MAC: %s and Ports: %s' \
				% (client_ip, client_mac_address, nmap_result_string) \
				+ '."}, '
				+ '"dataType": 0,'
				+ '"hasLatestData": false, '
				+ '"changeState": false, '
				+ '}}'

		else:
			fifo_message = '{"message": "sensoralert", ' \
				+ '"payload": {' \
				+ '"state": 1, ' \
				+ '"hasOptionalData": true, ' \
				+ '"optionalData": {' \
				+ '"message": ' \
				+ '"Unknown client with IP: %s and MAC: %s."' \
				% (client_ip, client_mac_address)
				+ '}, '
				+ '"dataType": 0,'
				+ '"hasLatestData": false, '
				+ '"changeState": false, '
				+ '}}'

		fifo_file.write(fifo_message)

	time.sleep(1)

	# release file lock
	fcntl.lockf(lock_fd, fcntl.LOCK_UN)
	lock_fd.close()
