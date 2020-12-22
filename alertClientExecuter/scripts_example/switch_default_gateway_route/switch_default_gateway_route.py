#!/usr/bin/env python3

import sys
import os

# list of resolv.conf files
# for example because postfix under Debian systems is chroot'ed
# it has an own resolv.conf file
resolv_conf_files = ["/etc/resolv.conf",
    "/var/spool/postfix/etc/resolv.conf"]

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


# removes the old default gw
def remove_gw():

    # try removing default gw 10 times until it does not exist anymore
    for _ in range(10):
        already_deleted = True

        # parse current route table and get default gw
        p = subprocess.Popen(["route", "-n"], stdout=subprocess.PIPE)
        out = p.communicate()
        out = out[0].split("\n")
        for line in out:
            line_split = line.strip().split(" ")
            if line_split[0] == "0.0.0.0": # default gw
                for field in line_split[1:]:
                    if field == "":
                        continue
                    else:

                        # delete old default gateway
                        p = subprocess.Popen(
                            ["route", "del", "default", "gw", field])
                        exit_code = p.wait()

                        if (exit_code != 0
                            and exit_code != 7
                            and exit_code != 1792):

                            print("Deleting default route to '%s' failed."
                                % field)
                            return False

                        else:
                            already_deleted = False
                        break

        if already_deleted:
            return True

    print("Deleting default route failed 10 times.")
    return False


# adds the new default gw
def add_gw(gw):

    # add new default gateway
    p = subprocess.Popen(["route", "add", "default", "gw", gw])
    exit_code = p.wait()

    if exit_code != 0 and exit_code != 7 and exit_code != 1792:
        print("Adding default route failed.")
        return False

    return True


# update resolv.conf
def update_resolv_conf(resolv_conf_files, resolv_conf_content):

    # replace resolv.conf with the given content (if exists)
    for resolv_conf_file in resolv_conf_files:
        if os.path.isfile(resolv_conf_file):
            with open(resolv_conf_file, 'w') as fp:
                fp.write(resolv_conf_content)


if len(sys.argv) != 2:
    print("Usage: %s <normal|alternative>" % sys.argv[0])
    sys.exit(0)

# changing routes in the OS needs root permissions
if os.geteuid() != 0:
    print("Script needs root permissions.")
    sys.exit(1)

if sys.argv[1] == "normal":
    print("Switching to normal route.")

    if not remove_gw():
        sys.exit(1)

    if not add_gw(normal_gateway):
        sys.exit(1)

    # replace resolv.conf with the normally used content
    update_resolv_conf(resolv_conf_files, normal_resolv_conf)

    print("Done.")

elif sys.argv[1] == "alternative":
    print("Switching to alternative route.")

    if not remove_gw():
        sys.exit(1)

    if not add_gw(alternative_gateway):
        sys.exit(1)

    # replace resolv.conf with the alternatively used content
    update_resolv_conf(resolv_conf_files, alternative_resolv_conf)

    print("Done.")

else:
    print("Invalid argument.")
    sys.exit(1)