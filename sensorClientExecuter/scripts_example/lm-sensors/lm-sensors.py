#!/usr/bin/python

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

import subprocess
import optparse
import json
import os


def parse_sensors():
	process = subprocess.Popen(["sensors", "-u"], stdout=subprocess.PIPE)

	# Wait until command was executed.
	while process.poll() is None:
		pass

	# Do nothing if command was not executed successful.
	if process.poll() != 0:
		return None

	output, _ = process.communicate()

	sensors = dict()
	new_device = True
	current_device = ""
	current_sensor = ""
	for line in output.split("\n"):
		# Ignore empty lines.
		if line == "":
			new_device = True
			continue

		elif new_device:
			current_device = line
			new_device = False
			sensors[current_device] = dict()
			sensors[current_device]["sensors"] = dict()

		# Check if we have a new adapter.
		elif line.startswith("Adapter: "):
			sensors[current_device]["adapter"] = line[9:]

		# Ignore lines that do not belong to a device.
		elif current_device == "":
			continue

		elif line[-1] == ":":
			current_sensor = line[:-1]
			sensors[current_device]["sensors"][current_sensor] = dict()

		elif line.startswith("  ") and current_sensor != "":
			key = line[2:line.find(":")]
			value = float(line[line.find(":")+2:])
			sensors[current_device]["sensors"][current_sensor][key] = value

		else:
			print("Do not know how to parse line: %s" % line)

	return sensors


def pretty_print(sensors):
	for device in sensors.keys():
		print("Device: %s" % device)
		print("Adapter: %s" % sensors[device]["adapter"])
		print("Sensors:")
		for sensor in sensors[device]["sensors"].keys():
			print("\tSensor: %s" % sensor)
			for key, value in sensors[device]["sensors"][sensor].iteritems():
				print("\t\t%s - %s" % (key, value))
		print("\n-----------------------\n")


def extract_value(sensors, device, sensor, key):
	if device not in sensors.keys():
		print("Device '%s' does not exist." % device)
		return None
	if sensor not in sensors[device]["sensors"].keys():
		print("Sensor '%s' of device '%s' does not exist." % (sensor, device))
		return None
	if key not in sensors[device]["sensors"][sensor].keys():
		print("Key '%s' for sensor '%s' of device '%s' does not exist."
			% (key, sensor, device))
		return None
	return sensors[device]["sensors"][sensor][key]


def create_sensor_alert(value, msg, state):
	result = dict()
	result["message"] = "sensoralert"
	payload = dict()
	payload["state"] = state
	payload["hasOptionalData"] = True
	optionalData = dict()
	optionalData["message"] = msg
	payload["optionalData"] = optionalData
	payload["dataType"] = 2
	payload["data"] = value
	payload["hasLatestData"] = True
	payload["changeState"] = True
	result["payload"] = payload
	return result


def create_state_change(value, state):
	result = dict()
	result["message"] = "statechange"
	payload = dict()
	payload["state"] = state
	payload["dataType"] = 2
	payload["data"] = value
	result["payload"] = payload
	return result


def main():

	# parsing command line options
	parser = optparse.OptionParser()

	parser.formatter = optparse.TitledHelpFormatter()

	parser.description = "Parses lm-sensors data and brings them into an "\
		"alertR usable format."
	parser.epilog = "Use the pretty print option (-p) to see what kind "\
		"of data is provided by lm-sensors. For examples on how to use "\
		"them with alertR please refer to the README.md file or visit "\
		"https://github.com/sqall01/alertR/wiki"

	sensor_group = optparse.OptionGroup(parser,
		"alertR options.")
	sensor_group.add_option(
		"-d",
		"--device",
		dest="device",
		action="store",
		help="Device to extract (Required).",
		default=None)
	sensor_group.add_option(
		"-s",
		"--sensor",
		dest="sensor",
		action="store",
		help="Sensor of device to extract (Required).",
		default=None)
	sensor_group.add_option(
		"-k",
		"--key",
		dest="key",
		action="store",
		help="Key for sensor of device to extract (Required).",
		default=None)
	sensor_group.add_option(
		"--max_value",
		dest="max_value",
		action="store",
		type="float",
		help="The maximum value the sensor is allowed to have. "\
			"If this value is exceeded a sensor alert "\
			"is given back (Optional).",
		default=None)
	sensor_group.add_option(
		"--min_value",
		dest="min_value",
		action="store",
		type="float",
		help="The minimum value the sensor is allowed to have. "\
			"If the sensor's value is below a sensor alert is "\
			"given back (Optional).",
		default=None)

	misc_group = optparse.OptionGroup(parser,
		"Miscellaneous options.")
	misc_group.add_option(
		"-p",
		"--pretty",
		dest="pretty",
		action="store_true",
		help="Pretty print of sensors.",
		default=False)

	parser.add_option_group(sensor_group)
	parser.add_option_group(misc_group)

	(options, args) = parser.parse_args()

	if options.pretty:
		sensors = parse_sensors()
		if sensors is None:
			return
		pretty_print(sensors)

	elif options.device and options.sensor and options.key:
		sensors = parse_sensors()
		value = extract_value(sensors,
			options.device,
			options.sensor,
			options.key)
		if value is None:
			return

		# Get the old value if it exists.
		path = os.path.dirname(os.path.abspath(__file__)) + "/"
		file_name = "state_" \
			+ options.device + "_" \
			+ options.sensor + "_" \
			+ options.key
		old_value = None
		try:
			with open(path + file_name, 'r') as fp:
				old_value = float(fp.read())
		except:
			pass

		# Decide what kind of alertR message is given back.
		# If a limits are given, decide if we are outside of these.
		if (options.max_value is not None
			or options.min_value is not None):

			# Check if our value is above the limit.
			if options.max_value is not None and value > options.max_value:

				# Check if our old state was also already above the limit.
				# => just output the state.
				if old_value is not None and old_value > options.max_value:
					result = create_state_change(value, 1)

				# We are above the limit now => output a sensor alert.
				else:
					result = create_sensor_alert(value,
						"Value is above allowed limit.",
						1)

			# Check if our value is below the limit.
			elif options.min_value is not None and value < options.min_value:

				# Check if our old state was also already below the limit.
				# => just output the state.
				if old_value is not None and old_value < options.min_value:
					result = create_state_change(value, 1)

				# We are below the limit now => output a sensor alert.
				else:
					result = create_sensor_alert(value,
						"Value is below allowed limit.",
						1)

			# We are inside the given limits => just output the state.
			else:
				result = create_state_change(value, 0)

		# No limits givin => just output a state.
		else:
			result = create_state_change(value, 0)
		print(json.dumps(result))

		# Write back current value for next execution.
		try:
			with open(path + file_name, 'w') as fp:
				fp.write(str(value))
		except:
			pass

	else:
		print("Use --help to get all available options.")


if __name__ == '__main__':
	main()