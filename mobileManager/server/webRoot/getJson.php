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
	echo "error mysql_connection";
	exit(1);				
}
if(!mysql_select_db($configMysqlDb, $mysqlConnection)) {
	echo "error mysql_select_db";
	exit(1);
}

// get all alert system information stored in the database
$resultInternals = mysql_query("SELECT * FROM internals");
$resultOptions = mysql_query("SELECT * FROM options");
$resultNodes = mysql_query("SELECT * FROM nodes");
$resultSensors = mysql_query("SELECT * FROM sensors");
$resultSensorsAlertLevels = mysql_query("SELECT * FROM sensorsAlertLevels");
$resultAlerts = mysql_query("SELECT * FROM alerts");
$resultAlertsAlertLevels = mysql_query("SELECT * FROM alertsAlertLevels");
$resultManagers = mysql_query("SELECT * FROM managers");
$resultSensorAlerts = mysql_query("SELECT * FROM sensorAlerts");
$resultAlertLevels = mysql_query("SELECT * FROM alertLevels");


// process the alert system information and generate arrays to output
// it as json data

// generate internals array
$internalsArray = array();
while($row = mysql_fetch_array($resultInternals)) {
	$internalEntry = array("id" => $row["id"],
		"type" => $row["type"],
		"value" => $row["value"]);
	array_push($internalsArray, $internalEntry);
}

// generate options array
$optionsArray = array();
while($row = mysql_fetch_array($resultOptions)) {
	$optionEntry = array("id" => $row["id"],
		"type" => $row["type"],
		"value" => $row["value"]);
	array_push($optionsArray, $optionEntry);
}

// generate nodes array
$nodesArray = array();
while($row = mysql_fetch_array($resultNodes)) {
	$nodeEntry = array("id" => $row["id"],
		"hostname" => $row["hostname"],
		"nodeType" => $row["nodeType"],
		"instance" => $row["instance"],
		"connected" => $row["connected"],
		"version" => $row["version"],
		"rev" => $row["rev"]);
	array_push($nodesArray, $nodeEntry);
}

// generate sensors array
$sensorsAlertLevelsArray = array();
while($row = mysql_fetch_array($resultSensorsAlertLevels)) {
    $sensorsAlertLevelEntry = array("sensorId" => $row["sensorId"],
    	"alertLevel" => $row["alertLevel"]);
    array_push($sensorsAlertLevelsArray, $sensorsAlertLevelEntry);
}
$sensorsArray = array();
while($row = mysql_fetch_array($resultSensors)) {

	// get alert levels of sensor
	$alertLevelArray = array();
	for($i = 0; $i < count($sensorsAlertLevelsArray); $i++) {
		if($row["id"] === $sensorsAlertLevelsArray[$i]["sensorId"]) {
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

// generate alerts array
$alertsAlertLevelsArray = array();
while($row = mysql_fetch_array($resultAlertsAlertLevels)) {
    $alertsAlertLevelEntry = array("alertId" => $row["alertId"],
    	"alertLevel" => $row["alertLevel"]);
    array_push($alertsAlertLevelsArray, $alertsAlertLevelEntry);
}
$alertsArray = array();
while($row = mysql_fetch_array($resultAlerts)) {

	// get alert levels of sensor
	$alertLevelArray = array();
	for($i = 0; $i < count($alertsAlertLevelsArray); $i++) {
		if($row["id"] === $alertsAlertLevelsArray[$i]["alertId"]) {
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

// generate managers array
$managersArray = array();
while($row = mysql_fetch_array($resultManagers)) {
	$managerEntry = array("id" => $row["id"],
		"nodeId" => $row["nodeId"],
		"description" => $row["description"]);
	array_push($managersArray, $managerEntry);
}

// generate alert levels array
$alertLevelsArray = array();
while($row = mysql_fetch_array($resultAlertLevels)) {
	$alertLevelEntry = array("alertLevel" => $row["alertLevel"],
		"name" => $row["name"],
		"triggerAlways" => $row["triggerAlways"],
		"smtpActivated" => $row["smtpActivated"],
		"toAddr" => $row["toAddr"]);
	array_push($alertLevelsArray, $alertLevelEntry);
}

// generate array that contains all other arrays
$alertSystemInformation = array("internals" => $internalsArray,
	"options" => $optionsArray,
	"nodes" => $nodesArray,
	"sensors" => $sensorsArray,
	"alerts" => $alertsArray,
	"managers" => $managersArray,
	"alertLevels" => $alertLevelsArray);

// output array as a json object
header('Content-type: application/json');
echo json_encode($alertSystemInformation);

?>