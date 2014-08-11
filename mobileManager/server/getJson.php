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
$resultOptions = mysql_query("SELECT * FROM options");
$resultNodes = mysql_query("SELECT * FROM nodes");
$resultSensors = mysql_query("SELECT * FROM sensors");
$resultManagers = mysql_query("SELECT * FROM managers");
$resultAlerts = mysql_query("SELECT * FROM alerts");
$resultSensorAlerts = mysql_query("SELECT * FROM sensorAlerts");
$resultAlertLevels = mysql_query("SELECT * FROM alertLevels");

// process the alert system information and generate arrays to output
// it as json data
$optionsArray = array();
while($row = mysql_fetch_array($resultOptions)) {
	$optionEntry = array("id" => $row["id"],
		"type" => $row["type"],
		"value" => $row["value"]);
	array_push($optionsArray, $optionEntry);
}
$nodesArray = array();
while($row = mysql_fetch_array($resultNodes)) {
	$nodeEntry = array("id" => $row["id"],
		"hostname" => $row["hostname"],
		"nodeType" => $row["nodeType"],
		"connected" => $row["connected"]);
	array_push($nodesArray, $nodeEntry);
}
$sensorsArray = array();
while($row = mysql_fetch_array($resultSensors)) {
	$sensorEntry = array("id" => $row["id"],
		"nodeId" => $row["nodeId"],
		"description" => $row["description"],
		"lastStateUpdated" => $row["lastStateUpdated"],
		"state" => $row["state"]);
	array_push($sensorsArray, $sensorEntry);
}
$managersArray = array();
while($row = mysql_fetch_array($resultManagers)) {
	$managerEntry = array("id" => $row["id"],
		"nodeId" => $row["nodeId"],
		"description" => $row["description"]);
	array_push($managersArray, $managerEntry);
}
$alertsArray = array();
while($row = mysql_fetch_array($resultAlerts)) {
	$alertEntry = array("id" => $row["id"],
		"nodeId" => $row["nodeId"],
		"description" => $row["description"]);
	array_push($alertsArray, $alertEntry);
}
$sensorAlertsArray = array();
while($row = mysql_fetch_array($resultSensorAlerts)) {
	$sensorAlertEntry = array("id" => $row["id"],
		"nodeId" => $row["nodeId"],
		"sensorId" => $row["sensorId"],
		"timeReceived" => $row["timeReceived"]);
	array_push($sensorAlertsArray, $sensorAlertEntry);
}
$alertLevelsArray = array();
while($row = mysql_fetch_array($resultAlertLevels)) {
	$alertLevelEntry = array("id" => $row["id"],
		"nodeId" => $row["nodeId"],
		"alertLevel" => $row["alertLevel"]);
	array_push($alertLevelsArray, $alertLevelEntry);
}

// generate array that contains all other arrays
$alertSystemInformation = array();
array_push($alertSystemInformation, $optionsArray);
array_push($alertSystemInformation, $nodesArray);
array_push($alertSystemInformation, $sensorsArray);
array_push($alertSystemInformation, $managersArray);
array_push($alertSystemInformation, $alertsArray);
array_push($alertSystemInformation, $sensorAlertsArray);
array_push($alertSystemInformation, $alertLevelsArray);

// output array as a json object
header('Content-type: application/json');
echo json_encode($alertSystemInformation);

?>