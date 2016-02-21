<?php

// written by sqall
// twitter: https://twitter.com/sqall01
// blog: http://blog.h4des.org
// github: https://github.com/sqall01
// 
// Licensed under the GNU Public License, version 2.

// include config data
require_once("./config/config.php");

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
				while($row = mysql_fetch_assoc($resultInternals)) {
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
				while($row = mysql_fetch_assoc($resultOptions)) {
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
				while($row = mysql_fetch_assoc($resultNodes)) {
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
				$resultSensors = mysql_query("SELECT * FROM sensors");
				$resultSensorsAlertLevels = mysql_query(
					"SELECT * FROM sensorsAlertLevels");
				$sensorsAlertLevelsArray = array();
				while($row = mysql_fetch_assoc($resultSensorsAlertLevels)) {
					$sensorsAlertLevelEntry = array(
						"sensorId" => $row["sensorId"],
						"alertLevel" => $row["alertLevel"]);
					array_push($sensorsAlertLevelsArray,
						$sensorsAlertLevelEntry);
				}
				$sensorsArray = array();
				while($row = mysql_fetch_assoc($resultSensors)) {

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
				while($row = mysql_fetch_assoc($resultAlertsAlertLevels)) {
					$alertsAlertLevelEntry = array(
						"alertId" => $row["alertId"],
						"alertLevel" => $row["alertLevel"]);
					array_push($alertsAlertLevelsArray,
						$alertsAlertLevelEntry);
				}
				$alertsArray = array();
				while($row = mysql_fetch_assoc($resultAlerts)) {

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
				while($row = mysql_fetch_assoc($resultManagers)) {
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
				while($row = mysql_fetch_assoc($resultSensorAlerts)) {
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
				while($row = mysql_fetch_assoc($resultAlertLevels)) {
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
					$resultEvents = mysql_query(
						"SELECT * FROM events ORDER BY id DESC "
						. "LIMIT " . $rangeStart . "," . $number);

					$resultEventsChangeAlert = mysql_query(
						"SELECT * FROM eventsChangeAlert ORDER BY id DESC");
					$eventsChangeAlertArray = array();
					while($row = mysql_fetch_assoc($resultEventsChangeAlert)) {
						array_push($eventsChangeAlertArray, $row);
						
					}

					$resultEventsChangeManager = mysql_query(
						"SELECT * FROM eventsChangeManager ORDER BY id DESC");
					$eventsChangeManagerArray = array();
					while(
						$row = mysql_fetch_assoc($resultEventsChangeManager)) {
						array_push($eventsChangeManagerArray, $row);
						
					}

					$resultEventsChangeNode = mysql_query(
						"SELECT * FROM eventsChangeNode ORDER BY id DESC");
					$eventsChangeNodeArray = array();
					while($row = mysql_fetch_assoc($resultEventsChangeNode)) {
						array_push($eventsChangeNodeArray, $row);
						
					}

					$resultEventsChangeOption = mysql_query(
						"SELECT * FROM eventsChangeOption ORDER BY id DESC");
					$eventsChangeOptionArray = array();
					while(
						$row = mysql_fetch_assoc($resultEventsChangeOption)) {
						array_push($eventsChangeOptionArray, $row);
						
					}

					$resultEventsChangeSensor = mysql_query(
						"SELECT * FROM eventsChangeSensor ORDER BY id DESC");
					$eventsChangeSensorArray = array();
					while(
						$row = mysql_fetch_assoc($resultEventsChangeSensor)) {
						array_push($eventsChangeSensorArray, $row);
						
					}

					$resultEventsConnectedChange = mysql_query(
						"SELECT * FROM eventsConnectedChange ORDER BY id DESC");
					$eventsConnectedChangeArray = array();
					while($row =
						mysql_fetch_assoc($resultEventsConnectedChange)) {
						array_push($eventsConnectedChangeArray, $row);
						
					}

					$resultEventsDeleteAlert = mysql_query(
						"SELECT * FROM eventsDeleteAlert ORDER BY id DESC");
					$eventsDeleteAlertArray = array();
					while($row = mysql_fetch_assoc($resultEventsDeleteAlert)) {
						array_push($eventsDeleteAlertArray, $row);
						
					}

					$resultEventsDeleteManager = mysql_query(
						"SELECT * FROM eventsDeleteManager ORDER BY id DESC");
					$eventsDeleteManagerArray = array();
					while(
						$row = mysql_fetch_assoc($resultEventsDeleteManager)) {
						array_push($eventsDeleteManagerArray, $row);
						
					}

					$resultEventsDeleteNode = mysql_query(
						"SELECT * FROM eventsDeleteNode ORDER BY id DESC");
					$eventsDeleteNodeArray = array();
					while($row = mysql_fetch_assoc($resultEventsDeleteNode)) {
						array_push($eventsDeleteNodeArray, $row);
						
					}

					$resultEventsDeleteSensor = mysql_query(
						"SELECT * FROM eventsDeleteSensor ORDER BY id DESC");
					$eventsDeleteSensorArray = array();
					while(
						$row = mysql_fetch_assoc($resultEventsDeleteSensor)) {
						array_push($eventsDeleteSensorArray, $row);
						
					}

					$resultEventsNewAlert = mysql_query(
						"SELECT * FROM eventsNewAlert ORDER BY id DESC");
					$eventsNewAlertArray = array();
					while($row = mysql_fetch_assoc($resultEventsNewAlert)) {
						array_push($eventsNewAlertArray, $row);
						
					}

					$resultEventsNewManager = mysql_query(
						"SELECT * FROM eventsNewManager ORDER BY id DESC");
					$eventsNewManagerArray = array();
					while($row = mysql_fetch_assoc($resultEventsNewManager)) {
						array_push($eventsNewManagerArray, $row);
						
					}

					$resultEventsNewNode = mysql_query(
						"SELECT * FROM eventsNewNode ORDER BY id DESC");
					$eventsNewNodeArray = array();
					while($row = mysql_fetch_assoc($resultEventsNewNode)) {
						array_push($eventsNewNodeArray, $row);
						
					}

					$resultEventsNewOption = mysql_query(
						"SELECT * FROM eventsNewOption ORDER BY id DESC");
					$eventsNewOptionArray = array();
					while($row = mysql_fetch_assoc($resultEventsNewOption)) {
						array_push($eventsNewOptionArray, $row);
						
					}

					$resultEventsNewSensor = mysql_query(
						"SELECT * FROM eventsNewSensor ORDER BY id DESC");
					$eventsNewSensorArray = array();
					while($row = mysql_fetch_assoc($resultEventsNewSensor)) {
						array_push($eventsNewSensorArray, $row);
						
					}

					$resultEventsNewVersion = mysql_query(
						"SELECT * FROM eventsNewVersion ORDER BY id DESC");
					$eventsNewVersionArray = array();
					while($row = mysql_fetch_assoc($resultEventsNewVersion)) {
						array_push($eventsNewVersionArray, $row);
						
					}

					$resultEventsSensorAlert = mysql_query(
						"SELECT * FROM eventsSensorAlert ORDER BY id DESC");
					$eventsSensorAlertArray = array();
					while($row = mysql_fetch_assoc($resultEventsSensorAlert)) {
						array_push($eventsSensorAlertArray, $row);
						
					}

					$resultEventsSensorTimeOut = mysql_query(
						"SELECT * FROM eventsSensorTimeOut ORDER BY id DESC");
					$eventsSensorTimeOutArray = array();
					while(
						$row = mysql_fetch_assoc($resultEventsSensorTimeOut)) {
						array_push($eventsSensorTimeOutArray, $row);
						
					}

					$resultEventsStateChange = mysql_query(
						"SELECT * FROM eventsStateChange ORDER BY id DESC");
					$eventsStateChangeArray = array();
					while($row = mysql_fetch_assoc($resultEventsStateChange)) {
						array_push($eventsStateChangeArray, $row);
						
					}
				}
				// no range is given => get all events
				else {
					$resultEvents = mysql_query(
						"SELECT * FROM events ORDER BY id DESC");

					$resultEventsChangeAlert = mysql_query(
						"SELECT * FROM eventsChangeAlert ORDER BY id DESC");
					$eventsChangeAlertArray = array();
					while($row = mysql_fetch_assoc($resultEventsChangeAlert)) {
						array_push($eventsChangeAlertArray, $row);
						
					}

					$resultEventsChangeManager = mysql_query(
						"SELECT * FROM eventsChangeManager ORDER BY id DESC");
					$eventsChangeManagerArray = array();
					while(
						$row = mysql_fetch_assoc($resultEventsChangeManager)) {
						array_push($eventsChangeManagerArray, $row);
						
					}

					$resultEventsChangeNode = mysql_query(
						"SELECT * FROM eventsChangeNode ORDER BY id DESC");
					$eventsChangeNodeArray = array();
					while($row = mysql_fetch_assoc($resultEventsChangeNode)) {
						array_push($eventsChangeNodeArray, $row);
						
					}

					$resultEventsChangeOption = mysql_query(
						"SELECT * FROM eventsChangeOption ORDER BY id DESC");
					$eventsChangeOptionArray = array();
					while(
						$row = mysql_fetch_assoc($resultEventsChangeOption)) {
						array_push($eventsChangeOptionArray, $row);
						
					}

					$resultEventsChangeSensor = mysql_query(
						"SELECT * FROM eventsChangeSensor ORDER BY id DESC");
					$eventsChangeSensorArray = array();
					while(
						$row = mysql_fetch_assoc($resultEventsChangeSensor)) {
						array_push($eventsChangeSensorArray, $row);
						
					}

					$resultEventsConnectedChange = mysql_query(
						"SELECT * FROM eventsConnectedChange ORDER BY id "
						. "DESC");
					$eventsConnectedChangeArray = array();
					while($row =
						mysql_fetch_assoc($resultEventsConnectedChange)) {
						array_push($eventsConnectedChangeArray, $row);
						
					}

					$resultEventsDeleteAlert = mysql_query(
						"SELECT * FROM eventsDeleteAlert ORDER BY id DESC");
					$eventsDeleteAlertArray = array();
					while($row = mysql_fetch_assoc($resultEventsDeleteAlert)) {
						array_push($eventsDeleteAlertArray, $row);
						
					}

					$resultEventsDeleteManager = mysql_query(
						"SELECT * FROM eventsDeleteManager ORDER BY id DESC");
					$eventsDeleteManagerArray = array();
					while(
						$row = mysql_fetch_assoc($resultEventsDeleteManager)) {
						array_push($eventsDeleteManagerArray, $row);
						
					}

					$resultEventsDeleteNode = mysql_query(
						"SELECT * FROM eventsDeleteNode ORDER BY id DESC");
					$eventsDeleteNodeArray = array();
					while($row = mysql_fetch_assoc($resultEventsDeleteNode)) {
						array_push($eventsDeleteNodeArray, $row);
						
					}

					$resultEventsDeleteSensor = mysql_query(
						"SELECT * FROM eventsDeleteSensor ORDER BY id DESC");
					$eventsDeleteSensorArray = array();
					while(
						$row = mysql_fetch_assoc($resultEventsDeleteSensor)) {
						array_push($eventsDeleteSensorArray, $row);
						
					}

					$resultEventsNewAlert = mysql_query(
						"SELECT * FROM eventsNewAlert ORDER BY id DESC");
					$eventsNewAlertArray = array();
					while($row = mysql_fetch_assoc($resultEventsNewAlert)) {
						array_push($eventsNewAlertArray, $row);
						
					}

					$resultEventsNewManager = mysql_query(
						"SELECT * FROM eventsNewManager ORDER BY id DESC");
					$eventsNewManagerArray = array();
					while($row = mysql_fetch_assoc($resultEventsNewManager)) {
						array_push($eventsNewManagerArray, $row);
						
					}

					$resultEventsNewNode = mysql_query(
						"SELECT * FROM eventsNewNode ORDER BY id DESC");
					$eventsNewNodeArray = array();
					while($row = mysql_fetch_assoc($resultEventsNewNode)) {
						array_push($eventsNewNodeArray, $row);
						
					}

					$resultEventsNewOption = mysql_query(
						"SELECT * FROM eventsNewOption ORDER BY id DESC");
					$eventsNewOptionArray = array();
					while($row = mysql_fetch_assoc($resultEventsNewOption)) {
						array_push($eventsNewOptionArray, $row);
						
					}

					$resultEventsNewSensor = mysql_query(
						"SELECT * FROM eventsNewSensor ORDER BY id DESC");
					$eventsNewSensorArray = array();
					while($row = mysql_fetch_assoc($resultEventsNewSensor)) {
						array_push($eventsNewSensorArray, $row);
						
					}

					$resultEventsNewVersion = mysql_query(
						"SELECT * FROM eventsNewVersion ORDER BY id DESC");
					$eventsNewVersionArray = array();
					while($row = mysql_fetch_assoc($resultEventsNewVersion)) {
						array_push($eventsNewVersionArray, $row);
						
					}

					$resultEventsSensorAlert = mysql_query(
						"SELECT * FROM eventsSensorAlert ORDER BY id DESC");
					$eventsSensorAlertArray = array();
					while($row = mysql_fetch_assoc($resultEventsSensorAlert)) {
						array_push($eventsSensorAlertArray, $row);
						
					}

					$resultEventsSensorTimeOut = mysql_query(
						"SELECT * FROM eventsSensorTimeOut ORDER BY id DESC");
					$eventsSensorTimeOutArray = array();
					while(
						$row = mysql_fetch_assoc($resultEventsSensorTimeOut)) {
						array_push($eventsSensorTimeOutArray, $row);
						
					}

					$resultEventsStateChange = mysql_query(
						"SELECT * FROM eventsStateChange ORDER BY id DESC");
					$eventsStateChangeArray = array();
					while($row = mysql_fetch_assoc($resultEventsStateChange)) {
						array_push($eventsStateChangeArray, $row);
						
					}
				}

				$eventsArray = array();
				while($row = mysql_fetch_assoc($resultEvents)) {
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
							foreach($eventsSensorAlertArray as $element) {
								if($element["eventId"] === $row["id"]) {
									$description = $element["description"];
									$state = $element["state"];
									break;
								}
							}
							$eventEntry = array("id" => $row["id"],
								"timeOccurred" => $row["timeOccurred"],
								"type" => $row["type"],
								"description" => $description,
								"state" => $state);
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
							foreach($eventsStateChangeArray as $element) {
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