<?php

// written by sqall
// twitter: https://twitter.com/sqall01
// blog: http://blog.h4des.org
// github: https://github.com/sqall01
// 
// Licensed under the GNU Public License, version 2.

// include config data
require_once("./config/config.php");

// connect to the mysql database and
$mysqlConnection = mysql_connect($configMysqlServer . ":" . $configMysqlPort,
	$configMysqlUsername, $configMysqlPassword);
if(!$mysqlConnection) {
	echo "Error: mysql_connection.";
	exit(1);				
}
if(!mysql_select_db($configMysqlDb, $mysqlConnection)) {
	echo "Error: mysql_select_db.";
	exit(1);
}


// check if it is set which data should be returned
if(isset($_GET["data"])
	&& gettype($_GET["data"]) === "array") {

	// fill alert system info array with requested data
	$alertSystemInformation = array();
	foreach($_GET["data"] as $data) {

		$data = strtoupper($data);
		switch($data) {

			// generate internals array
			case "INTERNALS":
				$resultInternals = mysql_query("SELECT * FROM internals");
				$internalsArray = array();
				while($row = mysql_fetch_array($resultInternals)) {
					$internalEntry = array("id" => $row["id"],
						"type" => $row["type"],
						"value" => $row["value"]);
					array_push($internalsArray, $internalEntry);
				}
				$alertSystemInformation["internals"] = $internalsArray;
				break;

			// generate options array
			case "OPTIONS":
				$resultOptions = mysql_query("SELECT * FROM options");
				$optionsArray = array();
				while($row = mysql_fetch_array($resultOptions)) {
					$optionEntry = array("id" => $row["id"],
						"type" => $row["type"],
						"value" => $row["value"]);
					array_push($optionsArray, $optionEntry);
				}
				$alertSystemInformation["options"] = $optionsArray;
				break;

			// generate nodes array
			case "NODES":
				$resultNodes = mysql_query("SELECT * FROM nodes");
				$nodesArray = array();
				while($row = mysql_fetch_array($resultNodes)) {
					$nodeEntry = array("id" => $row["id"],
						"hostname" => $row["hostname"],
						"nodeType" => $row["nodeType"],
						"instance" => $row["instance"],
						"connected" => $row["connected"],
						"version" => $row["version"],
						"rev" => $row["rev"],
						"newestVersion" => $row["newestVersion"],
						"newestRev" => $row["newestRev"]);
					array_push($nodesArray, $nodeEntry);
				}
				$alertSystemInformation["nodes"] = $nodesArray;
				break;

			// generate sensors array
			case "SENSORS":
				$resultSensors = mysql_query("SELECT * FROM sensors");
				$resultSensorsAlertLevels = mysql_query(
					"SELECT * FROM sensorsAlertLevels");
				$sensorsAlertLevelsArray = array();
				while($row = mysql_fetch_array($resultSensorsAlertLevels)) {
					$sensorsAlertLevelEntry = array(
						"sensorId" => $row["sensorId"],
						"alertLevel" => $row["alertLevel"]);
					array_push($sensorsAlertLevelsArray,
						$sensorsAlertLevelEntry);
				}
				$sensorsArray = array();
				while($row = mysql_fetch_array($resultSensors)) {

					// get alert levels of sensor
					$alertLevelArray = array();
					for($i = 0; $i < count($sensorsAlertLevelsArray); $i++) {
						if($row["id"] === $sensorsAlertLevelsArray[$i][
							"sensorId"]) {
							array_push($alertLevelArray,
								$sensorsAlertLevelsArray[$i]["alertLevel"]);
						}
					}

					$sensorEntry = array("id" => $row["id"],
						"nodeId" => $row["nodeId"],
						"description" => $row["description"],
						"lastStateUpdated" => $row["lastStateUpdated"],
						"state" => $row["state"],
						"alertLevels" => $alertLevelArray);
					array_push($sensorsArray, $sensorEntry);
				}
				$alertSystemInformation["sensors"] = $sensorsArray;
				break;

			// generate alerts array
			case "ALERTS":
				$resultAlerts = mysql_query("SELECT * FROM alerts");
				$resultAlertsAlertLevels = mysql_query(
					"SELECT * FROM alertsAlertLevels");
				$alertsAlertLevelsArray = array();
				while($row = mysql_fetch_array($resultAlertsAlertLevels)) {
					$alertsAlertLevelEntry = array(
						"alertId" => $row["alertId"],
						"alertLevel" => $row["alertLevel"]);
					array_push($alertsAlertLevelsArray,
						$alertsAlertLevelEntry);
				}
				$alertsArray = array();
				while($row = mysql_fetch_array($resultAlerts)) {

					// get alert levels of sensor
					$alertLevelArray = array();
					for($i = 0; $i < count($alertsAlertLevelsArray); $i++) {
						if($row["id"] === $alertsAlertLevelsArray[$i][
							"alertId"]) {
							array_push($alertLevelArray,
								$alertsAlertLevelsArray[$i]["alertLevel"]);
						}
					}

					$alertEntry = array("id" => $row["id"],
						"nodeId" => $row["nodeId"],
						"description" => $row["description"],
						"alertLevels" => $alertLevelArray);
					array_push($alertsArray, $alertEntry);
				}
				$alertSystemInformation["alerts"] = $alertsArray;
				break;

			// generate managers array
			case "MANAGERS":
				$resultManagers = mysql_query("SELECT * FROM managers");
				$managersArray = array();
				while($row = mysql_fetch_array($resultManagers)) {
					$managerEntry = array("id" => $row["id"],
						"nodeId" => $row["nodeId"],
						"description" => $row["description"]);
					array_push($managersArray, $managerEntry);
				}
				$alertSystemInformation["managers"] = $managersArray;
				break;

			// generate sensor alerts array
			case "SENSORALERTS":
				$resultSensorAlerts = null;
				// check if a range is given => get range of sensor alerts
				if(isset($_GET["sensorAlertsRangeStart"])
					&& isset($_GET["sensorAlertsNumber"])
					&& intval($_GET["sensorAlertsRangeStart"]) >= 0
					&& intval($_GET["sensorAlertsNumber"]) > 0) {
					$rangeStart = intval($_GET["sensorAlertsRangeStart"]);
					$number = intval($_GET["sensorAlertsNumber"]);
					$resultSensorAlerts = mysql_query(
						"SELECT * FROM sensorAlerts ORDER BY id DESC "
						. "LIMIT " . $rangeStart . "," . $number);
				}
				// no range is given => get all sensor alerts
				else {
					$resultSensorAlerts = mysql_query(
						"SELECT * FROM sensorAlerts ORDER BY id DESC");
				}
				$sensorAlertsArray = array();
				while($row = mysql_fetch_array($resultSensorAlerts)) {
					$sensorAlertEntry = array("id" => $row["id"],
						"sensorId" => $row["sensorId"],
						"state" => $row["state"],
						"description" => $row["description"],
						"timeReceived" => $row["timeReceived"],
						"data" => $row["dataJson"]);
					array_push($sensorAlertsArray, $sensorAlertEntry);
				}
				$alertSystemInformation["sensorAlerts"] = $sensorAlertsArray;
				break;

			// generate alert levels array
			case "ALERTLEVELS":
				$resultAlertLevels = mysql_query("SELECT * FROM alertLevels");
				$alertLevelsArray = array();
				while($row = mysql_fetch_array($resultAlertLevels)) {
					$alertLevelEntry = array(
						"alertLevel" => $row["alertLevel"],
						"name" => $row["name"],
						"triggerAlways" => $row["triggerAlways"],
						"smtpActivated" => $row["smtpActivated"],
						"toAddr" => $row["toAddr"]);
					array_push($alertLevelsArray, $alertLevelEntry);
				}
				$alertSystemInformation["alertLevels"] = $alertLevelsArray;
				break;

			default:
				break;
		}


	}

	// output array as a json object
	header('Content-type: application/json');
	echo json_encode($alertSystemInformation);

}
else {
	echo "Error: $data not set correctly.";
}


?>