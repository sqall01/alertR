#!/bin/bash

INTERNET_SERVER=("8.8.8.8" "github.com")

for i in "${INTERNET_SERVER[@]}"; do

    ping -c2 $i
    if [ "$?" = "0" ]; then
        exit 0
    fi

done

exit 1