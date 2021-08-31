#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

import sys
import logging
import xml.etree.ElementTree
from lib import GlobalData

try:
    import gpxpy
except ImportError as e:
    print("Requires pip packages 'gpxpy'. Please install it by executing 'pip3 install gpxpy'.")
    sys.exit(1)

if __name__ == '__main__':
    global_data = GlobalData()

    # Initialize logging.
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.INFO)
    global_data.logger = logging.getLogger("graph")

    # Read necessary configurations.
    configRoot = xml.etree.ElementTree.parse(global_data.configFile).getroot()

    geofences = {}

    # Parse all sensors.
    for item in configRoot.find("sensors").iterfind("sensor"):

        desc = str(item.find("general").attrib["description"])

        polygons = []
        for polygon_xml in item.iterfind("polygon"):
            polygon = []
            first = True
            first_tuple = None
            for position_xml in polygon_xml.iterfind("position"):
                lat = float(position_xml.attrib["lat"])
                lon = float(position_xml.attrib["lon"])
                if first:
                    first_tuple = (lat, lon)
                first = False
                polygon.append((lat, lon))
            polygon.append(first_tuple)
            polygons.append(polygon)

        geofences[desc] = polygons

    # Create GPX files.
    for desc, polygons in geofences.items():
        gpx = gpxpy.gpx.GPX()

        gpx_track = gpxpy.gpx.GPXTrack(name=desc)
        gpx.tracks.append(gpx_track)

        for polygon in polygons:
            gpx_segment = gpxpy.gpx.GPXTrackSegment()
            gpx_track.segments.append(gpx_segment)

            for lat, lon in polygon:
                gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))

        file_name = "export_" + desc + ".gpx"
        logging.info("Writing to file: %s" % file_name)
        with open(file_name, 'wt') as fp:
            fp.write(gpx.to_xml())
