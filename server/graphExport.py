#!/usr/bin/python3

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
from lib.localObjects import Alert, Sensor, AlertLevel, SensorDataType
from lib.config.parser import configure_alert_levels

try:
    import networkx as nx
    from networkx.drawing.nx_pydot import to_pydot
except Exception:
    print("Requires pip packages 'networkx' and 'pydot'. "
          + "Please install them by executing 'pip3 install networkx pydot'.")
    sys.exit(1)


class GraphAlert:

    def __init__(self, alert: Alert):
        self.alert = alert

    def __str__(self):
        temp = "\"Alert: " + self.alert.description + "\l" \
               + "Alert Id: " + str(self.alert.alertId) + "\l" \
               + "Remote Alert Id: " + str(self.alert.remoteAlertId) + "\l\""
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
        temp = "\"AlertLevel: " + self.alert_level.name + "\l" \
               + "Level: " + str(self.alert_level.level) + "\l" \
               + "Trigger Always: " + str(self.alert_level.triggerAlways) + "\l" \
               + "Alert for Triggered: " + str(self.alert_level.triggerAlertTriggered) + "\l" \
               + "Alert for Normal: " + str(self.alert_level.triggerAlertNormal) + "\l" \
               + "Has Rules: " + str(self.alert_level.rulesActivated) + "\l\""
        return temp

    def __eq__(self, other):
        if type(other) != GraphAlertLevel:
            return False
        return self.alert_level.level == other.alert_level.level

    def __hash__(self):
        return self.alert_level.level


class GraphSensor:

    def __init__(self, sensor: Sensor):
        self.sensor = sensor

    def __str__(self):
        data_type = "Unknown"
        if self.sensor.dataType == SensorDataType.NONE:
            data_type = "None"
        elif self.sensor.dataType == SensorDataType.INT:
            data_type = "Integer"
        elif self.sensor.dataType == SensorDataType.FLOAT:
            data_type = "Float"
        temp = "\"Sensor: " + self.sensor.description + "\l" \
               + "Sensor Id: " + str(self.sensor.sensorId) + "\l" \
               + "Remote Sensor Id: " + str(self.sensor.remoteSensorId) + "\l" \
               + "Alert Delay: " + str(self.sensor.alertDelay) + " sec\l" \
               + "Data Type: " + data_type + "\l\""
        return temp

    def __eq__(self, other):
        if type(other) != GraphSensor:
            return False
        return self.sensor.sensorId == other.sensor.sensorId

    def __hash__(self):
        return self.sensor.sensorId


def create_graph(alert_levels: Dict[int, AlertLevel], alerts: List[Alert], sensors: List[Sensor]) -> nx.DiGraph:
    graph = nx.DiGraph()

    # Add alerts, alert levels, and sensors as node to the graph.
    for sensor_obj in sensors:
        graph.add_node(GraphSensor(sensor_obj))

    for alert_obj in alerts:
        graph.add_node(GraphAlert(alert_obj))

    for _, alert_level_obj in alert_levels.items():
        graph.add_node(GraphAlertLevel(alert_level_obj))

    # Connect alerts and sensors with alert levels.
    for alert_obj in alerts:
        for alert_level_int in alert_obj.alertLevels:
            graph.add_edge(GraphAlertLevel(alert_levels[alert_level_int]),
                           GraphAlert(alert_obj))

    for sensor_obj in sensors:
        for alert_level_int in sensor_obj.alertLevels:
            graph.add_edge(GraphSensor(sensor_obj),
                           GraphAlertLevel(alert_levels[alert_level_int]))

    return graph


def get_alerts_and_sensors(global_data: GlobalData,
                           target_alert_level: Optional[int]) -> Tuple[List[Alert], List[Sensor]]:
    """
    Gets Alerts and Sensors from the database

    :return: List of Alert and List of Sensor objects
    """
    sys_info_list = global_data.storage.getAlertSystemInformation()

    # Filter Sensor objects if necessary.
    sensor_objs = []
    temp_sensor_objs = sys_info_list[2]
    if target_alert_level is not None:
        for sensor_obj in temp_sensor_objs:
            if target_alert_level in sensor_obj.alertLevels:
                sensor_obj.alertLevels = [target_alert_level]
                sensor_objs.append(sensor_obj)
    else:
        sensor_objs = temp_sensor_objs

    # Filter Alert objects if necessary.
    alert_objs = []
    temp_alert_objs = sys_info_list[4]
    if target_alert_level is not None:
        for alert_obj in temp_alert_objs:
            if target_alert_level in alert_obj.alertLevels:
                alert_obj.alertLevels = [target_alert_level]
                alert_objs.append(alert_obj)
    else:
        alert_objs = temp_alert_objs

    return alert_objs, sensor_objs


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
                    + "'python3 %s -g /home/alertr/graph.dot' -a 3" % sys.argv[0]
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
    parser.add_option("-a",
                      "--alertlevel",
                      dest="alert_level",
                      action="store",
                      type="int",
                      help="A specific Alert Level to export. If not set, all Alert Levels are exported. (Optional)",
                      default=None)

    (options, args) = parser.parse_args()

    if options.graph_path == "":
        print("Use --help to get all available options.")
        sys.exit(0)

    target_alert_level = options.alert_level

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
        if target_alert_level is None or alert_level.level == target_alert_level:
            alert_level_objs_dict[alert_level.level] = alert_level

    alert_objs, sensor_objs = get_alerts_and_sensors(global_data, target_alert_level)

    # Create graph and export.
    graph = create_graph(alert_level_objs_dict, alert_objs, sensor_objs)
    write_graph(graph, target_location, target_format)
    print("Graph written to '%s'." % target_location)
