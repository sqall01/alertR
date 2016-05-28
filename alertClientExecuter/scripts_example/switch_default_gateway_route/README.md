Switch Default Gateway Route
======

This script switches the default gateway route used by your host to an alternative one. The idea behind it is, when your Internet connection on your normal default gateway is down, you can switch to an alternative one. For example, you can check the Internet connection on your router or any other host and notify the alertR system if the Internet connection is down. Then the alertR Alert Client Executer can execute this script to switch the Internet connection from the normal route to an alternative route. As an alternative route an UMTS connection can be used. This is particularly useful if you have services that need a constant access to the Internet or if you want your alertR system to send emergency notifications even when your Internet connection is down.


How to use it?
======

In order to use this script you first have to configure it. In the script you have to set up the IP address of your normal gateway and the IP address of the alternative you want to switch to. 

Here is an example configuration for this script:


Network Configuration:
------

* Normal gateway address: 10.42.42.1
* Nameserver used for the normal gateway: 10.42.42.1
* Gateway address when using UMTS modem: 192.168.1.1
* Nameserver used for the UMTS modem: 8.8.8.8


The UMTS modem in this example registers itself as a network device
(used UMTS modem was the Huawei E303 surfstick). The UMTS modem has always
the address 192.168.1.1. In our configuration this network device is named
"eth1" and the network device for the normal connection is named "eth0".

In order to have a valid IP address in both network ranges, we configure
a static IP address for the host.

```bash

root@raspberrypi:/etc/network# vim interfaces

# normal interface
allow-hotplug eth0
auto eth0
iface eth0 inet static
        address 10.42.42.44
        netmask 255.255.255.0
        network 10.42.42.0
        broadcast 10.42.42.255
        gateway 10.42.42.1

# alternative interface
allow-hotplug eth1
auto eth1
iface eth1 inet static
        address 192.168.1.99
        netmask 255.255.255.0
        network 192.168.1.0
        broadcast 192.168.1.255

```

NOTE: If you want to receive an IP address dynamically for both interfaces,
please remember to disable the propagation of nameserver and gateway in the
/etc/dhcp/dhclient.conf. Or otherwise the gateway/nameserver of your host
will change constantly due to the made DHCP requests.


Permission Configuration:
------

Because only the "root" user has the permissions to change the routing entries,
this script has to be executed as "root" user. To do this, we need sudo. On
Debian-like systems sudo can be installed via:

```bash

root@raspberrypi:/etc# apt-get install sudo

```

And we need to configure it:

```bash

root@raspberrypi:/etc# vim sudoers

[...]
pi        ALL=NOPASSWD:/home/pi/alertR/alertClientExecuter/scripts/switch_route.py

```

Change the permissions of the script:

```bash

root@raspberrypi:/home/pi/alertR/alertClientExecuter/scripts# chown root:root switch_route.py 
root@raspberrypi:/home/pi/alertR/alertClientExecuter/scripts# chmod 755 switch_route.py

```


alertR Configuration:
------

We consider the following configuration of your alertR system:

* You have installed a script that checks if the Internet connection is down using your normal gateway (for example on your router). This script triggers a sensor alert when the Internet connection is down (state: "triggered"), and this script triggers a sensor alert when the Internet connection is up again (state: "normal").
* The sensor alert that is triggered by the Internet checking script is for the alert level 10 and 11. On the alertR server, alert level 10 is configured to always trigger a sensor alert and only on the "triggered" state. Alert level 11 is also configured to always trigger a sensor alert but only on the "normal" state.

The following alert-specific settings have to be made for the alertR Alert Client Executer to work with the given alertR system configuration:

```bash

[...]
<alerts>

    <alert>

        <general
            id="0"
            description="emergency Internet connection switch (emergency route)" />

        <alertLevel>10</alertLevel>

        <executer
            execute="/usr/bin/sudo">

            <triggerArgument>/home/pi/alertR/alertClientExecuter/scripts/switch_route.py</triggerArgument>
            <triggerArgument>alternative</triggerArgument>

            <stopArgument>/home/pi/alertR/alertClientExecuter/scripts/switch_route.py</stopArgument>
        </executer>

    </alert>

    <alert>

        <general
            id="1"
            description="emergency Internet connection switch (normal route)" />

        <alertLevel>11</alertLevel>

        <executer
            execute="/usr/bin/sudo">

            <triggerArgument>/home/pi/alertR/alertClientExecuter/scripts/switch_route.py</triggerArgument>
            <triggerArgument>normal</triggerArgument>

            <stopArgument>/home/pi/alertR/alertClientExecuter/scripts/switch_route.py</stopArgument>
        </executer>

    </alert>

</alerts>
[...]

```

If you need a more detailed description of how to set up an alertR system, please refer to the [wiki](https://github.com/sqall01/alertR/wiki).