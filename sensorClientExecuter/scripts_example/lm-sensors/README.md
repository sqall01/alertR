alertR - lm-sensors
======

This script allows you to read sensor data like CPU temperature on Linux with the help of "lm-sensors". The following gives you a short example on how to configure it. Use the "--help" argument to see the full list of options.

To see all available sensors use the following command:

```bash

sqall@towel:~$ python3 lm-sensors.py -p

Device: acpitz-virtual-0
Adapter: Virtual device
Sensors:
	Sensor: temp1
		temp1_crit - 128.0
		temp1_input - 43.0

-----------------------

Device: coretemp-isa-0000
Adapter: ISA adapter
Sensors:
	Sensor: Core 3
		temp5_crit - 100.0
		temp5_input - 50.0
		temp5_crit_alarm - 0.0
		temp5_max - 100.0
	Sensor: Core 2
		temp4_input - 42.0
		temp4_max - 100.0
		temp4_crit - 100.0
		temp4_crit_alarm - 0.0
	Sensor: Core 0
		temp2_crit - 100.0
		temp2_max - 100.0
		temp2_input - 43.0
		temp2_crit_alarm - 0.0
	Sensor: Physical id 0
		temp1_crit_alarm - 0.0
		temp1_max - 100.0
		temp1_crit - 100.0
		temp1_input - 49.0
	Sensor: Core 1
		temp3_crit_alarm - 0.0
		temp3_max - 100.0
		temp3_crit - 100.0
		temp3_input - 45.0

-----------------------

Device: thinkpad-isa-0000
Adapter: ISA adapter
Sensors:
	Sensor: fan1
		fan1_input - 2262.0

-----------------------

```

In this example we want the temperature of the whole CPU. In order to get it, we need the device (-d option) "coretemp-isa-0000", the actual sensor (-s option) "Physical id 0" and the key (-k option) "temp1_input". 

To see if everything works correctly, we can manually execute the command with the given options:

```bash

sqall@towel:~$ python3 lm-sensors.py -d coretemp-isa-0000 -s "Physical id 0" -k temp1_input

{"message": "statechange", "payload": {"dataType": 2, "state": 0, "data": 48.0}}

```

Note the whitespaces in the sensor name "Physical id 0". Because of them, we have to put quotes around the argument in the command line.

The corresponding sensor configuration for the alertR Sensor Client Executer looks like the following:

```xml

<!-- [...] -->
<sensor>

	<general
		id="0"
		description="lm-sensors CPU"
		alertDelay="0"
		triggerAlert="True"
		triggerAlertNormal="True"
		triggerState="1" />

	<alertLevel>0</alertLevel>

	<executer
		execute="/usr/bin/python3"
		timeout="5"
		intervalToCheck="10"
		parseOutput="True"
		dataType="2">

		<argument>/path/to/lm-sensors.py</argument>
		<argument>-d</argument>
		<argument>coretemp-isa-0000</argument>
		<argument>-s</argument>
		<argument>Physical id 0</argument>
		<argument>-k</argument>
		<argument>temp1_input</argument>

	</executer>

</sensor>
<!-- [...] -->

```

Note the missing quotes for the sensor name "Physical id 0". Arguments given in the configuration file do not need quotes if they have whitespaces or other special characters.
