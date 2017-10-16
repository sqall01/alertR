<?php

// written by sqall
// twitter: https://twitter.com/sqall01
// blog: http://blog.h4des.org
// github: https://github.com/sqall01
// 
// Licensed under the GNU Affero General Public License, version 3.

// include config data
require_once("./config/config.php");


// This enum class gives the different data types of a sensor.
abstract class SensorDataType {
    const NONE_TYPE = 0;
    const INT_TYPE = 1;
    const FLOAT_TYPE = 2;
}


// check if ssl is used (or disabled via config)
if($configWebSSL) {
	if (!isset($_SERVER['HTTPS']) || $_SERVER['HTTPS'] != 'on') {
		echo "Error: SSL not used.";
		exit(1);
	}
}

// check if the user has authenticated himself
if($configWebAuth) {
	if(!isset($_SERVER["REMOTE_USER"])) {
		echo "Error: User authentication required.";
		exit(1);
	}
}

// connect to the mysql database and

try {
	$db = new PDO('mysql:host=' . $configMysqlServer
			. ';dbname=' . $configMysqlDb
			. ';charset=utf8mb4',
			$configMysqlUsername, $configMysqlPassword);
} catch (PDOException $e) {
	echo "Error: mysql_connection failed! (Error=" . $e->getMessage() . ")\n";
	die();
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
				$stmt = $db->query('SELECT * FROM internals');
				$internalsArray = array();
				while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
					$internalEntry = array("id" => $row["id"],
						"type" => $row["type"],
						"value" => $row["value"]);
					array_push($internalsArray, $internalEntry);
				}
				$alertSystemInformation["internals"] = $internalsArray;
				break;

			// generate options array
			case "OPTIONS":
				$stmt = $db->query('SELECT * FROM options');
				$optionsArray = array();
				while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
					$optionEntry = array("id" => $row["id"],
						"type" => $row["type"],
						"value" => $row["value"]);
					array_push($optionsArray, $optionEntry);
				}
				$alertSystemInformation["options"] = $optionsArray;
				break;

			// generate nodes array
			case "NODES":
				$stmt = $db->query('SELECT * FROM nodes');
				$nodesArray = array();
				while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
					$nodeEntry = array("id" => $row["id"],
						"hostname" => $row["hostname"],
						"nodeType" => $row["nodeType"],
						"instance" => $row["instance"],
						"connected" => $row["connected"],
						"version" => $row["version"],
						"rev" => $row["rev"],
						"newestVersion" => $row["newestVersion"],
						"newestRev" => $row["newestRev"],
						"username" => $row["username"],
						"persistent" => $row["persistent"]);
					array_push($nodesArray, $nodeEntry);
				}
				$alertSystemInformation["nodes"] = $nodesArray;
				break;

			// generate sensors array
			case "SENSORS":
				$stmt = $db->query('SELECT * FROM sensors');
				$resultSensors = $stmt->fetchAll(PDO::FETCH_ASSOC);

				$stmt = $db->query('SELECT * FROM sensorsAlertLevels');
				$resultSensorsAlertLevels = $stmt->fetchAll(PDO::FETCH_ASSOC);

				$sensorsAlertLevelsArray = array();
				while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
					$sensorsAlertLevelEntry = array(
						"sensorId" => $row["sensorId"],
						"alertLevel" => $row["alertLevel"]);
					array_push($sensorsAlertLevelsArray,
						$sensorsAlertLevelEntry);
				}
				$sensorsArray = array();
				foreach($resultSensors as $row) {

					// get alert levels of sensor
					$alertLevelArray = array();
					for($i = 0; $i < count($sensorsAlertLevelsArray); $i++) {
						if($row["id"] === $sensorsAlertLevelsArray[$i][
							"sensorId"]) {
							array_push($alertLevelArray,
								$sensorsAlertLevelsArray[$i]["alertLevel"]);
						}
					}

					// Get the data of the sensor.
					$data = "";
					switch($row["dataType"]) {

						case SensorDataType::INT_TYPE:
							$stmt = $db->query("SELECT data FROM "
								. "sensorsDataInt WHERE sensorId = "
								. intval($row["id"]));
							$dataRow = $stmt->fetch(PDO::FETCH_ASSOC);
							$data = $dataRow["data"];
							break;

						case SensorDataType::FLOAT_TYPE:
							$stmt = $db->query("SELECT data FROM "
								. "sensorsDataFloat WHERE sensorId = "
								. intval($row["id"]));
							$dataRow = $stmt->fetch(PDO::FETCH_ASSOC);
							$data = $dataRow["data"];
							break;

						case SensorDataType::NONE_TYPE:
						default:
							break;
					}

					$sensorEntry = array("id" => $row["id"],
						"nodeId" => $row["nodeId"],
						"description" => $row["description"],
						"lastStateUpdated" => $row["lastStateUpdated"],
						"state" => $row["state"],
						"alertLevels" => $alertLevelArray,
						"dataType" => $row["dataType"],
						"data" => $data);
					array_push($sensorsArray, $sensorEntry);
				}
				$alertSystemInformation["sensors"] = $sensorsArray;
				break;

			// generate alerts array
			case "ALERTS":
				$stmt = $db->query("SELECT * FROM alerts");
				$resultAlerts = $stmt->fetchAll(PDO::FETCH_ASSOC);

				$stmt = $db->query("SELECT * FROM alertsAlertLevels");
				$alertsAlertLevelsArray = array();
				while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
					$alertsAlertLevelEntry = array(
						"alertId" => $row["alertId"],
						"alertLevel" => $row["alertLevel"]);
					array_push($alertsAlertLevelsArray,
						$alertsAlertLevelEntry);
				}
				$alertsArray = array();
				foreach($resultAlerts as $row) {

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
				$stmt = $db->query("SELECT * FROM managers");
				$managersArray = array();
				while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
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
				$sensorAlertsAlertLevelsArray = null;
				// check if a range is given => get range of sensor alerts
				if(isset($_GET["sensorAlertsRangeStart"])
					&& isset($_GET["sensorAlertsNumber"])
					&& intval($_GET["sensorAlertsRangeStart"]) >= 0
					&& intval($_GET["sensorAlertsNumber"]) > 0) {
					$rangeStart = intval($_GET["sensorAlertsRangeStart"]);
					$number = intval($_GET["sensorAlertsNumber"]);
					$stmt =	$db->query("SELECT * FROM sensorAlerts ORDER BY id DESC "
						. "LIMIT " . $rangeStart . "," . $number);
					$resultSensorAlerts = $stmt->fetchAll(PDO::FETCH_ASSOC);
				}
				// no range is given => get all sensor alerts
				else {
					$stmt = $db->query("SELECT * FROM sensorAlerts ORDER BY id DESC");
					$resultSensorAlerts = $stmt->fetchAll(PDO::FETCH_ASSOC);
				}

				// Get alert levels of the sensor alerts.
				$stmt = $db->query("SELECT * FROM sensorAlertsAlertLevels");
				$sensorAlertsAlertLevelsArray = array();
				while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
					$sensorAlertsAlertLevelEntry = array(
						"sensorAlertId" => $row["sensorAlertId"],
						"alertLevel" => $row["alertLevel"]);
					array_push($sensorAlertsAlertLevelsArray,
						$sensorAlertsAlertLevelEntry);
				}

				$sensorAlertsArray = array();
				foreach( $resultSensorAlerts as $row) {

					// Get alert levels of sensor alert.
					$alertLevelArray = array();
					for($i = 0;
						$i < count($sensorAlertsAlertLevelsArray);
						$i++) {

						if($row["id"] === $sensorAlertsAlertLevelsArray[$i][
							"sensorAlertId"]) {
							array_push($alertLevelArray,
								$sensorAlertsAlertLevelsArray[$i][
								"alertLevel"]);
						}
					}

					// Get the data of the sensor alert.
					$data = "";
					switch($row["dataType"]) {

						case SensorDataType::INT_TYPE:
							$stmt = $db->query("SELECT data FROM "
								. "sensorAlertsDataInt WHERE sensorAlertId = "
								. intval($row["id"]));
							$dataRow = $stmt->fetch(PDO::FETCH_ASSOC);
							$data = $dataRow["data"];
							break;

						case SensorDataType::FLOAT_TYPE:
							$stmt = $db->query("SELECT data FROM "
								. "sensorAlertsDataFloat WHERE "
								. "sensorAlertId = "
								. intval($row["id"]));
							$dataRow = $stmt->fetch(PDO::FETCH_ASSOC);
							$data = $dataRow["data"];
							break;

						case SensorDataType::NONE_TYPE:
						default:
							break;
					}

					$sensorAlertEntry = array("id" => $row["id"],
						"sensorId" => $row["sensorId"],
						"state" => $row["state"],
						"description" => $row["description"],
						"timeReceived" => $row["timeReceived"],
						"alertLevels" => $alertLevelArray,
						"optionalData" => $row["dataJson"],
						"dataType" => $row["dataType"],
						"data" => $data);
					array_push($sensorAlertsArray, $sensorAlertEntry);
				}
				$alertSystemInformation["sensorAlerts"] = $sensorAlertsArray;
				break;

			// generate alert levels array
			case "ALERTLEVELS":
				$stmt = $db->query("SELECT * FROM alertLevels");
				$alertLevelsArray = array();
				while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
					$alertLevelEntry = array(
						"alertLevel" => $row["alertLevel"],
						"name" => $row["name"],
						"triggerAlways" => $row["triggerAlways"]);
					array_push($alertLevelsArray, $alertLevelEntry);
				}
				$alertSystemInformation["alertLevels"] = $alertLevelsArray;
				break;

			// generate events array
			case "EVENTS":
				$resultEvents = null;
				// check if a range is given => get range of events
				if(isset($_GET["eventsRangeStart"])
					&& isset($_GET["eventsNumber"])
					&& intval($_GET["eventsRangeStart"]) >= 0
					&& intval($_GET["eventsNumber"]) > 0) {
					$rangeStart = intval($_GET["eventsRangeStart"]);
					$number = intval($_GET["eventsNumber"]);
					$stmt = $db->query(
						"SELECT * FROM events ORDER BY id DESC "
						. "LIMIT " . $rangeStart . "," . $number);
					$resultEvents = $stmt->fetchAll(PDO::FETCH_ASSOC);

					$stmt = $db->query("SELECT * FROM eventsChangeAlert "
						. "ORDER BY eventId DESC "
						. "LIMIT " . $rangeStart . "," . $number);
					$eventsChangeAlertArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsChangeAlertArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsChangeManager "
						. "ORDER BY eventId DESC "
						. "LIMIT " . $rangeStart . "," . $number);
					$eventsChangeManagerArray = array();
					while(
						$row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsChangeManagerArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsChangeNode ORDER BY "
						. "eventId DESC "
						. "LIMIT " . $rangeStart . "," . $number);
					$eventsChangeNodeArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsChangeNodeArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsChangeOption ORDER BY "
						. "eventId DESC "
						. "LIMIT " . $rangeStart . "," . $number);
					$eventsChangeOptionArray = array();
					while(
						$row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsChangeOptionArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsChangeSensor ORDER BY "
						. "eventId DESC "
						. "LIMIT " . $rangeStart . "," . $number);
					$eventsChangeSensorArray = array();
					while(
						$row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsChangeSensorArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsConnectedChange ORDER BY "
						. "eventId DESC "
						. "LIMIT " . $rangeStart . "," . $number);
					$eventsConnectedChangeArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsConnectedChangeArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsDeleteAlert ORDER BY "
						. "eventId DESC "
						. "LIMIT " . $rangeStart . "," . $number);
					$eventsDeleteAlertArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsDeleteAlertArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsDeleteManager ORDER BY "
						. "eventId DESC "
						. "LIMIT " . $rangeStart . "," . $number);
					$eventsDeleteManagerArray = array();
					while(
						$row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsDeleteManagerArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsDeleteNode ORDER BY "
						. "eventId DESC "
						. "LIMIT " . $rangeStart . "," . $number);
					$eventsDeleteNodeArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsDeleteNodeArray, $row);
						
					}

					$stmt = $db->query(
						"SELECT * FROM eventsDeleteSensor ORDER BY "
						. "eventId DESC "
						. "LIMIT " . $rangeStart . "," . $number);
					$eventsDeleteSensorArray = array();
					while(
						$row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsDeleteSensorArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsNewAlert ORDER BY "
						. "eventId DESC "
						. "LIMIT " . $rangeStart . "," . $number);
					$eventsNewAlertArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsNewAlertArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsNewManager ORDER BY "
						. "eventId DESC "
						. "LIMIT " . $rangeStart . "," . $number);
					$eventsNewManagerArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsNewManagerArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsNewNode ORDER BY "
						. "eventId DESC "
						. "LIMIT " . $rangeStart . "," . $number);
					$eventsNewNodeArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsNewNodeArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsNewOption ORDER BY "
						. "eventId DESC "
						. "LIMIT " . $rangeStart . "," . $number);
					$eventsNewOptionArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsNewOptionArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsNewSensor ORDER BY "
						. "eventId DESC "
						. "LIMIT " . $rangeStart . "," . $number);
					$eventsNewSensorArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsNewSensorArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsNewVersion ORDER BY "
						. "eventId DESC "
						. "LIMIT " . $rangeStart . "," . $number);
					$eventsNewVersionArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsNewVersionArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsSensorAlert ORDER BY "
						. "eventId DESC "
						. "LIMIT " . $rangeStart . "," . $number);
					$eventsSensorAlertArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsSensorAlertArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsSensorTimeOut ORDER BY "
						. "eventId DESC "
						. "LIMIT " . $rangeStart . "," . $number);
					$eventsSensorTimeOutArray = array();
					while(
						$row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsSensorTimeOutArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsStateChange ORDER BY "
						. "eventId DESC "
						. "LIMIT " . $rangeStart . "," . $number);
					$eventsStateChangeArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsStateChangeArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsDataInt ORDER BY "
						. "eventId DESC "
						. "LIMIT " . $rangeStart . "," . $number);
					$eventsDataIntArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsDataIntArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsDataFloat ORDER BY "
						. "eventId DESC "
						. "LIMIT " . $rangeStart . "," . $number);
					$eventsDataFloatArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsDataFloatArray, $row);
					}

				}
				// no range is given => get all events
				else {
					$stmt = $db->query('SELECT * FROM events ORDER BY id DESC');
					$resultEvents = $stmt->fetchAll(PDO::FETCH_ASSOC);

					$stmt = $db->query(
						"SELECT * FROM eventsChangeAlert ORDER BY "
						. "eventId DESC");
					$eventsChangeAlertArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsChangeAlertArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsChangeManager ORDER BY "
						. "eventId DESC");
					$eventsChangeManagerArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsChangeManagerArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsChangeNode ORDER BY "
						. "eventId DESC");
					$eventsChangeNodeArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsChangeNodeArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsChangeOption ORDER BY "
						. "eventId DESC");
					$eventsChangeOptionArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsChangeOptionArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsChangeSensor ORDER BY "
						. "eventId DESC");
					$eventsChangeSensorArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsChangeSensorArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsConnectedChange ORDER BY "
						. "eventId "
						. "DESC");
					$eventsConnectedChangeArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsConnectedChangeArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsDeleteAlert ORDER BY "
						. "eventId DESC");
					$eventsDeleteAlertArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsDeleteAlertArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsDeleteManager ORDER BY "
						. "eventId DESC");
					$eventsDeleteManagerArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsDeleteManagerArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsDeleteNode ORDER BY "
						. "eventId DESC");
					$eventsDeleteNodeArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsDeleteNodeArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsDeleteSensor ORDER BY "
						. "eventId DESC");
					$eventsDeleteSensorArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsDeleteSensorArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsNewAlert ORDER BY "
						. "eventId DESC");
					$eventsNewAlertArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsNewAlertArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsNewManager ORDER BY "
						. "eventId DESC");
					$eventsNewManagerArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsNewManagerArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsNewNode ORDER BY "
						. "eventId DESC");
					$eventsNewNodeArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsNewNodeArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsNewOption ORDER BY "
						. "eventId DESC");
					$eventsNewOptionArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsNewOptionArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsNewSensor ORDER BY "
						. "eventId DESC");
					$eventsNewSensorArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsNewSensorArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsNewVersion ORDER BY "
						. "eventId DESC");
					$eventsNewVersionArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsNewVersionArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsSensorAlert ORDER BY "
						. "eventId DESC");
					$eventsSensorAlertArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsSensorAlertArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsSensorTimeOut ORDER BY "
						. "eventId DESC");
					$eventsSensorTimeOutArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsSensorTimeOutArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsStateChange ORDER BY "
						. "eventId DESC");
					$eventsStateChangeArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsStateChangeArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsDataInt ORDER BY "
						. "eventId DESC");
					$eventsDataIntArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsDataIntArray, $row);
					}

					$stmt = $db->query(
						"SELECT * FROM eventsDataFloat ORDER BY "
						. "eventId DESC");
					$eventsDataFloatArray = array();
					while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
						array_push($eventsDataFloatArray, $row);
					}
				}

				$eventsArray = array();
				foreach($resultEvents as $row) {
					switch($row["type"]) {
						case "changeAlert":
							$oldDescription = null;
							$newDescription = null;
							foreach($eventsChangeAlertArray as $element) {
								if($element["eventId"] === $row["id"]) {
									$oldDescription =
										$element["oldDescription"];
									$newDescription =
										$element["newDescription"];
									break;
								}
							}
							$eventEntry = array("id" => $row["id"],
								"timeOccurred" => $row["timeOccurred"],
								"type" => $row["type"],
								"oldDescription" => $oldDescription,
								"newDescription" => $newDescription);
							break;

						case "changeManager":
							$oldDescription = null;
							$newDescription = null;
							foreach($eventsChangeManagerArray as $element) {
								if($element["eventId"] === $row["id"]) {
									$oldDescription =
										$element["oldDescription"];
									$newDescription =
										$element["newDescription"];
									break;
								}
							}
							$eventEntry = array("id" => $row["id"],
								"timeOccurred" => $row["timeOccurred"],
								"type" => $row["type"],
								"oldDescription" => $oldDescription,
								"newDescription" => $newDescription);
							break;

						case "changeNode":
							$oldHostname = null;
							$oldNodeType = null;
							$oldInstance = null;
							$oldVersion = null;
							$oldRev = null;
							$newHostname = null;
							$newNodeType = null;
							$newInstance = null;
							$newVersion = null;
							$newRev = null;
							foreach($eventsChangeNodeArray as $element) {
								if($element["eventId"] === $row["id"]) {
									$oldHostname = $element["oldHostname"];
									$oldNodeType = $element["oldNodeType"];
									$oldInstance = $element["oldInstance"];
									$oldVersion = $element["oldVersion"];
									$oldRev = $element["oldRev"];
									$oldUsername = $element["oldUsername"];
									$oldPersistent = $element["oldPersistent"];
									$newHostname = $element["newHostname"];
									$newNodeType = $element["newNodeType"];
									$newInstance = $element["newInstance"];
									$newVersion = $element["newVersion"];
									$newRev = $element["newRev"];
									$newUsername = $element["newUsername"];
									$newPersistent = $element["newPersistent"];
									break;
								}
							}
							$eventEntry = array("id" => $row["id"],
								"timeOccurred" => $row["timeOccurred"],
								"type" => $row["type"],
								"oldHostname" => $oldHostname,
								"oldNodeType" => $oldNodeType,
								"oldInstance" => $oldInstance,
								"oldVersion" => $oldVersion,
								"oldRev" => $oldRev,
								"oldUsername" => $oldUsername,
								"oldPersistent" => $oldPersistent,
								"newHostname" => $newHostname,
								"newNodeType" => $newNodeType,
								"newInstance" => $newInstance,
								"newVersion" => $newVersion,
								"newRev" => $newRev,
								"newUsername" => $newUsername,
								"newPersistent" => $newPersistent);
							break;

						case "changeOption":
							$optionType = null;
							$oldValue = null;
							$newValue = null;
							foreach($eventsChangeOptionArray as $element) {
								if($element["eventId"] === $row["id"]) {
									$optionType = $element["type"];
									$oldValue = $element["oldValue"];
									$newValue = $element["newValue"];
									break;
								}
							}
							$eventEntry = array("id" => $row["id"],
								"timeOccurred" => $row["timeOccurred"],
								"type" => $row["type"],
								"optionType" => $optionType,
								"oldValue" => $oldValue,
								"newValue" => $newValue);
							break;

						case "changeSensor":
							$oldAlertDelay = null;
							$oldDescription = null;
							$newAlertDelay = null;
							$newDescription = null;
							foreach($eventsChangeSensorArray as $element) {
								if($element["eventId"] === $row["id"]) {
									$oldAlertDelay = $element["oldAlertDelay"];
									$oldDescription = 
										$element["oldDescription"];
									$newAlertDelay = $element["newAlertDelay"];
									$newDescription =
										$element["newDescription"];
									break;
								}
							}
							$eventEntry = array("id" => $row["id"],
								"timeOccurred" => $row["timeOccurred"],
								"type" => $row["type"],
								"oldAlertDelay" => $oldAlertDelay,
								"oldDescription" => $oldDescription,
								"newAlertDelay" => $newAlertDelay,
								"newDescription" => $newDescription);
							break;

						case "connectedChange":
							$hostname = null;
							$nodeType = null;
							$instance = null;
							$connected = null;
							foreach($eventsConnectedChangeArray as $element) {
								if($element["eventId"] === $row["id"]) {
									$hostname = $element["hostname"];
									$nodeType = $element["nodeType"];
									$instance = $element["instance"];
									$connected = $element["connected"];
									break;
								}
							}
							$eventEntry = array("id" => $row["id"],
								"timeOccurred" => $row["timeOccurred"],
								"type" => $row["type"],
								"hostname" => $hostname,
								"nodeType" => $nodeType,
								"instance" => $instance,
								"connected" => $connected);
							break;

						case "deleteAlert":
							$description = null;
							foreach($eventsDeleteAlertArray as $element) {
								if($element["eventId"] === $row["id"]) {
									$description = $element["description"];
									break;
								}
							}
							$eventEntry = array("id" => $row["id"],
								"timeOccurred" => $row["timeOccurred"],
								"type" => $row["type"],
								"description" => $description);
							break;

						case "deleteManager":
							$description = null;
							foreach($eventsDeleteManagerArray as $element) {
								if($element["eventId"] === $row["id"]) {
									$description = $element["description"];
									break;
								}
							}
							$eventEntry = array("id" => $row["id"],
								"timeOccurred" => $row["timeOccurred"],
								"type" => $row["type"],
								"description" => $description);
							break;

						case "deleteNode":
							$hostname = null;
							$nodeType = null;
							$instance = null;
							foreach($eventsDeleteNodeArray as $element) {
								if($element["eventId"] === $row["id"]) {
									$hostname = $element["hostname"];
									$nodeType = $element["nodeType"];
									$instance = $element["instance"];
									break;
								}
							}
							$eventEntry = array("id" => $row["id"],
								"timeOccurred" => $row["timeOccurred"],
								"type" => $row["type"],
								"hostname" => $hostname,
								"nodeType" => $nodeType,
								"instance" => $instance);
							break;

						case "deleteSensor":
							$description = null;
							foreach($eventsDeleteSensor as $element) {
								if($element["eventId"] === $row["id"]) {
									$description = $element["description"];
									break;
								}
							}
							$eventEntry = array("id" => $row["id"],
								"timeOccurred" => $row["timeOccurred"],
								"type" => $row["type"],
								"description" => $description);
							break;

						case "newAlert":
							$hostname = null;
							$description = null;
							foreach($eventsNewAlertArray as $element) {
								if($element["eventId"] === $row["id"]) {
									$hostname = $element["hostname"];
									$description = $element["description"];
									break;
								}
							}
							$eventEntry = array("id" => $row["id"],
								"timeOccurred" => $row["timeOccurred"],
								"type" => $row["type"],
								"hostname" => $hostname,
								"description" => $description);
							break;

						case "newManager":
							$hostname = null;
							$description = null;
							foreach($eventsNewManagerArray as $element) {
								if($element["eventId"] === $row["id"]) {
									$hostname = $element["hostname"];
									$description = $element["description"];
									break;
								}
							}
							$eventEntry = array("id" => $row["id"],
								"timeOccurred" => $row["timeOccurred"],
								"type" => $row["type"],
								"hostname" => $hostname,
								"description" => $description);
							break;

						case "newNode":
							$hostname = null;
							$nodeType = null;
							$instance = null;
							foreach($eventsNewNodeArray as $element) {
								if($element["eventId"] === $row["id"]) {
									$hostname = $element["hostname"];
									$nodeType = $element["nodeType"];
									$instance = $element["instance"];
									break;
								}
							}
							$eventEntry = array("id" => $row["id"],
								"timeOccurred" => $row["timeOccurred"],
								"type" => $row["type"],
								"hostname" => $hostname,
								"nodeType" => $nodeType,
								"instance" => $instance);
							break;

						case "newOption":
							$optionType = null;
							$value = null;
							foreach($eventsNewOptionArray as $element) {
								if($element["eventId"] === $row["id"]) {
									$optionType = $element["type"];
									$value = $element["value"];
									break;
								}
							}
							$eventEntry = array("id" => $row["id"],
								"timeOccurred" => $row["timeOccurred"],
								"type" => $row["type"],
								"optionType" => $optionType,
								"value" => $value);
							break;

						case "newSensor":
							$hostname = null;
							$description = null;
							$state = null;
							foreach($eventsNewSensorArray as $element) {
								if($element["eventId"] === $row["id"]) {
									$hostname = $element["hostname"];
									$description = $element["description"];
									$state = $element["state"];
									break;
								}
							}
							$eventEntry = array("id" => $row["id"],
								"timeOccurred" => $row["timeOccurred"],
								"type" => $row["type"],
								"hostname" => $hostname,
								"description" => $description,
								"state" => $state);
							break;

						case "newVersion":
							$usedVersion = null;
							$usedRev = null;
							$newVersion = null;
							$newRev = null;
							$instance = null;
							$hostname = null;
							foreach($eventsNewVersionArray as $element) {
								if($element["eventId"] === $row["id"]) {
									$usedVersion = $element["usedVersion"];
									$usedRev = $element["usedRev"];
									$newVersion = $element["newVersion"];
									$newRev = $element["newRev"];
									$instance = $element["instance"];
									$hostname = $element["hostname"];
									break;
								}
							}
							$eventEntry = array("id" => $row["id"],
								"timeOccurred" => $row["timeOccurred"],
								"type" => $row["type"],
								"usedVersion" => $usedVersion,
								"usedRev" => $usedRev,
								"newVersion" => $newVersion,
								"newRev" => $newRev,
								"instance" => $instance,
								"hostname" => $hostname);
							break;

						case "sensorAlert":
							$description = null;
							$state = null;
							$dataType = null;
							$data = "";

							// Get details of event.
							foreach($eventsSensorAlertArray as $element) {
								if($element["eventId"] === $row["id"]) {
									$description = $element["description"];
									$state = $element["state"];
									$dataType = $element["dataType"];
									break;
								}
							}

							// Get data of event.
							switch($dataType) {
								case SensorDataType::INT_TYPE:
									foreach($eventsDataIntArray
										as $element) {

										if($element["eventId"]
											=== $row["id"]) {

											$data = $element["data"];
											break;
										}

									}
									break;

								case SensorDataType::FLOAT_TYPE:
									foreach($eventsDataFloatArray
										as $element) {

										if($element["eventId"]
											=== $row["id"]) {

											$data = $element["data"];
											break;
										}

									}
									break;

								case SensorDataType::NONE_TYPE:
								default:
									break;
							}

							$eventEntry = array("id" => $row["id"],
								"timeOccurred" => $row["timeOccurred"],
								"type" => $row["type"],
								"description" => $description,
								"state" => $state,
								"dataType" => $dataType,
								"data" => $data);
							break;

						case "sensorTimeOut":
							$hostname = null;
							$description = null;
							$state = null;
							foreach($eventsSensorTimeOutArray as $element) {
								if($element["eventId"] === $row["id"]) {
									$hostname = $element["hostname"];
									$description = $element["description"];
									$state = $element["state"];
									break;
								}
							}
							$eventEntry = array("id" => $row["id"],
								"timeOccurred" => $row["timeOccurred"],
								"type" => $row["type"],
								"hostname" => $hostname,
								"description" => $description,
								"state" => $state);
							break;

						case "stateChange":
							$hostname = null;
							$description = null;
							$state = null;
							$dataType = null;
							$data = "";

							// Get details of event.
							foreach($eventsStateChangeArray as $element) {
								if($element["eventId"] === $row["id"]) {
									$hostname = $element["hostname"];
									$description = $element["description"];
									$state = $element["state"];
									$dataType = $element["dataType"];
									break;
								}
							}

							// Get data of event.
							switch($dataType) {
								case SensorDataType::INT_TYPE:
									foreach($eventsDataIntArray
										as $element) {

										if($element["eventId"]
											=== $row["id"]) {

											$data = $element["data"];
											break;
										}

									}
									break;

								case SensorDataType::FLOAT_TYPE:
									foreach($eventsDataFloatArray
										as $element) {

										if($element["eventId"]
											=== $row["id"]) {

											$data = $element["data"];
											break;
										}

									}
									break;

								case SensorDataType::NONE_TYPE:
								default:
									break;
							}

							$eventEntry = array("id" => $row["id"],
								"timeOccurred" => $row["timeOccurred"],
								"type" => $row["type"],
								"hostname" => $hostname,
								"description" => $description,
								"state" => $state,
								"dataType" => $dataType,
								"data" => $data);
							break;

						default:
							break;
					}
					array_push($eventsArray, $eventEntry);
				}
				$alertSystemInformation["events"] = $eventsArray;
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
	echo "Error: \$data not set correctly.";
}


?>
