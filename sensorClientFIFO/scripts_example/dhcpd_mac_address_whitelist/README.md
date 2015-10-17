DHCP Lease MAC Address Whitelist
======

This scripts checks if the MAC address that requested an IP address from your DHCPD is known. If it is not known it will trigger a sensor alert using the FIFO sensor of the alertR Sensor Client FIFO. Also it is able to scan the ports of the unknown clients via Nmap and to send an eMail using the local eMail service.


How to use it?
======

In order to use this script you first have to configure it. You can decide if it should scan the unknown host via Nmap or if it should send and eMail notification. The script takes as first argument the IP address of the unknown client and as second argument the MAC address of the unknown client. If you use the "isc-dhcp-server", you should use the wrapper to start the script in the background. An example configuration part for the "isc-dhcp-server" looks like the following:

```bash

root@router:/etc/dhcp# vim dhcpd.conf
[...]

on commit {
	set ClientIP = binary-to-ascii(10, 8, ".", leased-address);
	set ClientMac = binary-to-ascii(16, 8, ":", substring(hardware, 1, 8));
	execute ("/home/alertr/mac_address_whitelist_wrapper.sh", ClientIP, ClientMac);
}

```

If you need a more detailed description of how to set up an alertR system, a basic example configuration is given in the [wiki](https://github.com/sqall01/alertR/wiki/Example-Configuration).