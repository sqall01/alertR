#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import sys
import logging
import optparse
import xml.etree.ElementTree
from typing import Tuple, List, Dict, Optional
from lib import Sqlite
from lib import GlobalData
from lib.localObjects import Alert, Sensor, AlertLevel, SensorDataType, Node
from lib.config.parser import configure_alert_levels

try:
    import networkx as nx
    from networkx.drawing.nx_pydot import to_pydot
except Exception:
    print("Requires pip packages 'networkx' and 'pydot'. "
          + "Please install them by executing 'pip3 install networkx pydot'.")
    sys.exit(1)


class GraphAlert:

    def __init__(self, node: Node, alert: Alert):
        self.alert = alert
        self.node = node

    def __str__(self):
        # noinspection PyPep8
        temp = "\"Alert: " + self.alert.description + "\l" \
               + "Alert Id: " + str(self.alert.alertId) + "\l" \
               + "Remote Alert Id: " + str(self.alert.remoteAlertId) + "\l" \
               + "Node Username: " + str(self.node.username) + "\l\""
        return temp

    def __eq__(self, other):
        if type(other) != GraphAlert:
            return False
        return self.alert.alertId == other.alert.alertId

    def __hash__(self):
        return self.alert.alertId


class GraphAlertLevel:

    def __init__(self, alert_level: AlertLevel):
        self.alert_level = alert_level

    def __str__(self):
        # noinspection PyPep8
        temp = "\"AlertLevel: " + self.alert_level.name + "\l" \
               + "Level: " + str(self.alert_level.level) + "\l" \
               + "Alert for Triggered: " + str(self.alert_level.triggerAlertTriggered) + "\l" \
               + "Alert for Normal: " + str(self.alert_level.triggerAlertNormal) + "\l" \
               + "Instrumented: " + str(self.alert_level.instrumentation_active) + "\l\""
        return temp

    def __eq__(self, other):
        if type(other) != GraphAlertLevel:
            return False
        return self.alert_level.level == other.alert_level.level

    def __hash__(self):
        return self.alert_level.level


class GraphSensor:

    def __init__(self, node: Node, sensor: Sensor):
        self.sensor = sensor
        self.node = node

    def __str__(self):
        data_type = "Unknown"
        if self.sensor.dataType == SensorDataType.NONE:
            data_type = "None"
        elif self.sensor.dataType == SensorDataType.INT:
            data_type = "Integer"
        elif self.sensor.dataType == SensorDataType.FLOAT:
            data_type = "Float"
        # noinspection PyPep8
        temp = "\"Sensor: " + self.sensor.description + "\l" \
               + "Sensor Id: " + str(self.sensor.sensorId) + "\l" \
               + "Remote Sensor Id: " + str(self.sensor.remoteSensorId) + "\l" \
               + "Node Username: " + str(self.node.username) + "\l" \
               + "Alert Delay: " + str(self.sensor.alertDelay) + " sec\l" \
               + "Data Type: " + data_type + "\l\""
        return temp

    def __eq__(self, other):
        if type(other) != GraphSensor:
            return False
        return self.sensor.sensorId == other.sensor.sensorId

    def __hash__(self):
        return self.sensor.sensorId


class Filter:
    def __init__(self,
                 alert_level: Optional[int],
                 alert_username: Optional[str],
                 remote_alert_id: Optional[int],
                 sensor_username: Optional[str],
                 remote_sensor_id: Optional[int]):

        self.alert_level = alert_level
        self.alert_username = alert_username
        self.remote_alert_id = remote_alert_id
        self.sensor_username = sensor_username
        self.remote_sensor_id = remote_sensor_id

        self.cached_node = None

        if ((self.alert_username is None and self.remote_alert_id is not None)
           or (self.alert_username is not None and self.remote_alert_id is None)):
            raise ValueError("Bot '--alertusername' and '--remotealertid' have to be set or none.")

        if ((self.sensor_username is None and self.remote_sensor_id is not None)
           or (self.sensor_username is not None and self.remote_sensor_id is None)):
            raise ValueError("Bot '--sensorusername' and '--remotesensorid' have to be set or none.")

        filter_set = False
        if self.alert_level is not None:
            filter_set = True

        if self.alert_username is not None and self.remote_alert_id is not None:
            if filter_set:
                raise ValueError("Only one filter option can be set (Alert Level, Alert, or Sensor)")
            filter_set = True

        if self.sensor_username is not None and self.remote_sensor_id is not None:
            if filter_set:
                raise ValueError("Only one filter option can be set (Alert Level, Alert, or Sensor)")

    def _get_node(self,
                  username: str,
                  nodes: Dict[int, Node]) -> Node:

        if self.cached_node is not None:
            return self.cached_node

        for _, node in nodes.items():
            if node.username.lower() == username.lower():
                self.cached_node = node
                break

        if self.cached_node is None:
            raise ValueError("Node with username '%s' does not exist." % username)

        return self.cached_node

    def filter_alert_levels(self,
                            alert_levels: Dict[int, AlertLevel],
                            nodes: Dict[int, Node],
                            alerts: List[Alert],
                            sensors: List[Sensor]) -> Dict[int, AlertLevel]:
        """
        Filters the alert levels to the requested ones.

        :param alert_levels: Dict of all Alert Levels mapping level to Alert Level object.
        :param nodes: Dict of all Nodes mapping node id to Node object.
        :param alerts: List of all Alerts.
        :param sensors: List of all Sensors.
        :return: Dict of alert level to Alert Level object.
        """
        filtered_alert_levels = {}

        # Process Alert Level filter if set.
        if self.alert_level is not None:
            for _, alert_level in alert_levels.items():
                if alert_level.level == self.alert_level:
                    filtered_alert_levels[alert_level.level] = alert_level
                    break

        # Process Alert filter if set.
        elif self.alert_username is not None:
            target_node = self._get_node(self.alert_username, nodes)
            target_alert = None
            for alert in alerts:
                if alert.nodeId == target_node.id and alert.remoteAlertId == self.remote_alert_id:
                    target_alert = alert
                    break

            if target_alert is None:
                raise ValueError("Alert with username '%s' and remote Alert id '%d' does not exist."
                                 % (self.alert_username, self.remote_alert_id))

            for _, alert_level in alert_levels.items():
                if alert_level.level in target_alert.alertLevels:
                    filtered_alert_levels[alert_level.level] = alert_level

        # Process Sensor filter if set.
        elif self.sensor_username is not None:
            target_node = self._get_node(self.sensor_username, nodes)
            target_sensor = None
            for sensor in sensors:
                if sensor.nodeId == target_node.id and sensor.remoteSensorId == self.remote_sensor_id:
                    target_sensor = sensor
                    break

            if target_sensor is None:
                raise ValueError("Sensor with username '%s' and remote Sensor id '%d' does not exist."
                                 % (self.sensor_username, self.remote_sensor_id))

            for _, alert_level in alert_levels.items():
                if alert_level.level in target_sensor.alertLevels:
                    filtered_alert_levels[alert_level.level] = alert_level

        # No filter is set.
        else:
            filtered_alert_levels = alert_levels

        return filtered_alert_levels

    def filter_alerts(self,
                      nodes: Dict[int, Node],
                      alerts: List[Alert],
                      sensors: List[Sensor]) -> List[Alert]:
        """
        Filters the alerts to the requested ones.

        :param nodes: Dict of all Nodes mapping node id to Node object.
        :param alerts: List of all Alerts.
        :param sensors: List of all Sensors.
        :return: List of Alert objects.
        """
        filtered_alerts = []

        # Process Alert Level filter if set.
        if self.alert_level is not None:
            for alert in alerts:
                if self.alert_level in alert.alertLevels:
                    alert.alertLevels = [self.alert_level]
                    filtered_alerts.append(alert)

        # Process Alert filter if set.
        elif self.alert_username is not None:
            target_node = self._get_node(self.alert_username, nodes)
            for alert in alerts:
                if alert.nodeId == target_node.id and alert.remoteAlertId == self.remote_alert_id:
                    filtered_alerts.append(alert)
                    break

        # Process Sensor filter if set.
        elif self.sensor_username is not None:
            target_node = self._get_node(self.sensor_username, nodes)
            target_sensor = None
            for sensor in sensors:
                if sensor.nodeId == target_node.id and sensor.remoteSensorId == self.remote_sensor_id:
                    target_sensor = sensor
                    break

            if target_sensor is None:
                raise ValueError("Sensor with username '%s' and remote Sensor id '%d' does not exist."
                                 % (self.sensor_username, self.remote_alert_id))

            for alert in alerts:
                for alert_level in alert.alertLevels:
                    if alert_level in target_sensor.alertLevels:
                        # Since an Alert can have different Alert Levels as the target Sensor, only store the ones
                        # that the Sensor also has.
                        orig_alert_levels = alert.alertLevels
                        new_alert_levels = []
                        for sensor_alert_level in target_sensor.alertLevels:
                            if sensor_alert_level in orig_alert_levels:
                                new_alert_levels.append(sensor_alert_level)
                        alert.alertLevels = new_alert_levels
                        filtered_alerts.append(alert)

        else:
            filtered_alerts = alerts

        return filtered_alerts

    def filter_sensors(self,
                       nodes: Dict[int, Node],
                       alerts: List[Alert],
                       sensors: List[Sensor]) -> List[Sensor]:
        """
        Filters the sensors to the requested ones.

        :param nodes: Dict of all Nodes mapping node id to Node object.
        :param alerts: List of all Alerts.
        :param sensors: List of all Sensors.
        :return: List of Sensor objects.
        """
        filtered_sensors = []

        # Process Alert Level filter if set.
        if self.alert_level is not None:
            for sensor in sensors:
                if self.alert_level in sensor.alertLevels:
                    sensor.alertLevels = [self.alert_level]
                    filtered_sensors.append(sensor)

        # Process Alert filter if set.
        elif self.alert_username is not None:
            target_node = self._get_node(self.alert_username, nodes)
            target_alert = None
            for alert in alerts:
                if alert.nodeId == target_node.id and alert.remoteAlertId == self.remote_alert_id:
                    target_alert = alert
                    break

            if target_alert is None:
                raise ValueError("Alert with username '%s' and remote Alert id '%d' does not exist."
                                 % (self.alert_username, self.remote_sensor_id))

            for sensor in sensors:
                for alert_level in sensor.alertLevels:
                    if alert_level in target_alert.alertLevels:
                        # Since a Sensor can have different Alert Levels as the target Alert, only store the ones
                        # that the Alert also has.
                        orig_alert_levels = sensor.alertLevels
                        new_alert_levels = []
                        for alert_alert_level in target_alert.alertLevels:
                            if alert_alert_level in orig_alert_levels:
                                new_alert_levels.append(alert_alert_level)
                        sensor.alertLevels = new_alert_levels
                        filtered_sensors.append(sensor)

        # Process Sensor filter if set.
        elif self.sensor_username is not None:
            target_node = self._get_node(self.sensor_username, nodes)
            for sensor in sensors:
                if sensor.nodeId == target_node.id and sensor.remoteSensorId == self.remote_sensor_id:
                    filtered_sensors.append(sensor)
                    break

        else:
            filtered_sensors = sensors

        return filtered_sensors


def create_graph(alert_levels: Dict[int, AlertLevel],
                 nodes: Dict[int, Node],
                 alerts: List[Alert],
                 sensors: List[Sensor]) -> nx.DiGraph:
    graph = nx.DiGraph()

    # Add alerts, alert levels, and sensors as node to the graph.
    for alert_obj in alerts:
        graph.add_node(GraphAlert(nodes[alert_obj.nodeId], alert_obj))

    for sensor_obj in sensors:
        graph.add_node(GraphSensor(nodes[sensor_obj.nodeId], sensor_obj))

    for _, alert_level_obj in alert_levels.items():
        graph.add_node(GraphAlertLevel(alert_level_obj))

    # Connect alerts and sensors with alert levels.
    for alert_obj in alerts:
        for alert_level_int in alert_obj.alertLevels:
            graph.add_edge(GraphAlertLevel(alert_levels[alert_level_int]),
                           GraphAlert(nodes[alert_obj.nodeId], alert_obj))

    for sensor_obj in sensors:
        for alert_level_int in sensor_obj.alertLevels:
            graph.add_edge(GraphSensor(nodes[sensor_obj.nodeId], sensor_obj),
                           GraphAlertLevel(alert_levels[alert_level_int]))

    return graph


def get_objects_from_db(global_data: GlobalData) -> Tuple[Dict[int, Node], List[Alert], List[Sensor]]:
    """
    Gets Nodes, Alerts and Sensors from the database

    :return: Dict of all Node objects, List of Alert and List of Sensor objects
    """
    sys_info_list = global_data.storage.getAlertSystemInformation()

    node_objs = {}
    temp_node_objs = sys_info_list[1]  # type: List[Node]
    for node_obj in temp_node_objs:
        node_objs[node_obj.id] = node_obj

    alert_objs = sys_info_list[4]  # type: List[Alert]
    sensor_objs = sys_info_list[2]  # type: List[Sensor]

    return node_objs, alert_objs, sensor_objs


def write_graph(graph: nx.DiGraph, target_file, target_format="raw"):
    font = "Ubuntu Mono"
    dot = to_pydot(graph)
    for n in dot.get_node_list():
        n.set_fontname(font)
        n.set_shape("rect")
        if n.obj_dict["name"].startswith('"AlertLevel: '):
            n.set_fillcolor("#cecece")
            n.set_style("filled")
        elif n.obj_dict["name"].startswith('"Alert: '):
            n.set_fillcolor("#4e96d5")
            n.set_style("filled")
        elif n.obj_dict["name"].startswith('"Sensor: '):
            n.set_fillcolor("#25d426")
            n.set_style("filled")

    dot.write(target_file, format=target_format)


if __name__ == '__main__':

    # Parsing command line options.
    parser = optparse.OptionParser()
    parser.formatter = optparse.TitledHelpFormatter()
    parser.description = "Exports a graph containing Alerts, Alert Levels, and Sensors of your AlertR system."
    parser.epilog = "Example command create graph: " \
                    + "\t\t\t\t\t\t\t\t\t\t" \
                    + "'python3 %s -g /home/alertr/graph.dot'" % sys.argv[0] \
                    + "\t\t\t\t\t\t\t\t\t\t" \
                    + "Example command to create graph for a specific Alert Level:" \
                    + "\t\t\t\t\t\t\t\t\t\t" \
                    + "'python3 %s -g /home/alertr/graph.dot' --alertlevel 3" % sys.argv[0] \
                    + "\t\t\t\t\t\t\t\t\t\t" \
                    + "Example command to create graph for a specific Alert:" \
                    + "\t\t\t\t\t\t\t\t\t\t" \
                    + "'python3 %s -g /home/alertr/graph.dot' --remotealertid 1 --alertusername user1" % sys.argv[0] \
                    + "\t\t\t\t\t\t\t\t\t\t" \
                    + "Example command to create graph for a specific Sensor:" \
                    + "\t\t\t\t\t\t\t\t\t\t" \
                    + "'python3 %s -g /home/alertr/graph.dot' --remotesensorid 2 --sensorusername user33" % sys.argv[0]
    parser.add_option("-g",
                      "--graph",
                      dest="graph_path",
                      action="store",
                      help="Target graph location. (Required)",
                      default="")
    parser.add_option("",
                      "--png",
                      dest="png",
                      action="store_true",
                      help="Output PNG file. (Optional)",
                      default=False)
    parser.add_option("",
                      "--alertlevel",
                      dest="alert_level",
                      action="store",
                      type="int",
                      help="Specific Alert Level to export. If not set, all Alert Levels are exported. (Optional)",
                      default=None)
    parser.add_option("",
                      "--remotealertid",
                      dest="remote_alert_id",
                      action="store",
                      type="int",
                      help="Specific Remote Alert Id to export. If not set, all Alerts are exported. "
                           + "If set, requires also to set --alertusername (Optional)",
                      default=None)
    parser.add_option("",
                      "--alertusername",
                      dest="alert_username",
                      action="store",
                      help="Specific username of the AlertR instance running the Alert to export. "
                           + "If not set, all Alerts are exported. "
                           + "If set, requires also to set --remotealertid (Optional)",
                      default=None)
    parser.add_option("",
                      "--remotesensorid",
                      dest="remote_sensor_id",
                      action="store",
                      type="int",
                      help="Specific Remote Sensor Id to export. If not set, all Sensors are exported. "
                           + "If set, requires also to set --sensorusername (Optional)",
                      default=None)
    parser.add_option("",
                      "--sensorusername",
                      dest="sensor_username",
                      action="store",
                      help="Specific username of the AlertR instance running the Sensor to export. "
                           + "If not set, all Sensors are exported. "
                           + "If set, requires also to set --remotesensorid (Optional)",
                      default=None)

    (options, args) = parser.parse_args()

    if options.graph_path == "":
        print("Use --help to get all available options.")
        sys.exit(0)

    # Extract target Alert Level, Alert, and Sensor (if set at all).
    try:
        filter_obj = Filter(options.alert_level,
                            options.alert_username,
                            options.remote_alert_id,
                            options.sensor_username,
                            options.remote_sensor_id)
    except ValueError as e:
        print(e)
        sys.exit(1)

    # Create correct file ending and check target file writable.
    target_location = options.graph_path
    do_png = options.png
    target_format = "raw"
    if do_png:
        target_format = "png"
        if target_location[-4:] != ".png":
            target_location += ".png"
    else:
        if target_location[-4:] != ".dot":
            target_location += ".dot"
    try:
        with open(target_location, 'w') as fp:
            pass
    except Exception:
        print("Not able to write '%s'." % target_location)
        sys.exit(1)

    global_data = GlobalData()

    # Initialize logging.
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.WARNING)
    global_data.logger = logging.getLogger("graph")

    global_data.storage = Sqlite(global_data.storageBackendSqliteFile,
                                 global_data,
                                 read_only=True)

    # Read necessary configurations.
    configRoot = xml.etree.ElementTree.parse(global_data.configFile).getroot()
    configure_alert_levels(configRoot, global_data)

    # Get Alert, Alert Level, ans Sensor objects.
    alert_level_objs_dict = dict()
    for alert_level in global_data.alertLevels:
            alert_level_objs_dict[alert_level.level] = alert_level
    node_objs, alert_objs, sensor_objs = get_objects_from_db(global_data)

    # Filter Alert Level, Alert, and Sensor.
    try:
        alert_level_objs_dict = filter_obj.filter_alert_levels(alert_level_objs_dict,
                                                               node_objs,
                                                               alert_objs,
                                                               sensor_objs)
        alert_objs = filter_obj.filter_alerts(node_objs,
                                              alert_objs,
                                              sensor_objs)
        sensor_objs = filter_obj.filter_sensors(node_objs,
                                                alert_objs,
                                                sensor_objs)
    except ValueError as e:
        print(e)
        sys.exit(1)

    # Create graph and export.
    graph = create_graph(alert_level_objs_dict, node_objs, alert_objs, sensor_objs)
    write_graph(graph, target_location, target_format)
    print("Graph written to '%s'." % target_location)
