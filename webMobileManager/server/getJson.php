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
    const GPS_TYPE = 3;
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
$mysqli = new mysqli($configMysqlServer,
                     $configMysqlUsername,
                     $configMysqlPassword,
                     $configMysqlDb,
                     $configMysqlPort);

if($mysqli->connect_errno) {
    die("Error: Database connection failed: " . $mysqli->connect_error);
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
                $stmt = $mysqli->query('SELECT * FROM internals');
                $internalsArray = array();
                while($row = $stmt->fetch_assoc()) {
                    $internalEntry = array("type" => $row["type"],
                        "value" => $row["value"]);
                    array_push($internalsArray, $internalEntry);
                }
                $alertSystemInformation["internals"] = $internalsArray;
                break;

            // generate profiles array
            case "PROFILES":
                $stmt = $mysqli->query('SELECT * FROM profiles');
                $profilesArray = array();
                while($row = $stmt->fetch_assoc()) {
                    $profileEntry = array("profileId" => $row["id"],
                        "name" => $row["name"]);
                    array_push($profilesArray, $profileEntry);
                }
                $alertSystemInformation["profiles"] = $profilesArray;
                break;

            // generate options array
            case "OPTIONS":
                $stmt = $mysqli->query('SELECT * FROM options');
                $optionsArray = array();
                while($row = $stmt->fetch_assoc()) {
                    $optionEntry = array("type" => $row["type"],
                        "value" => $row["value"]);
                    array_push($optionsArray, $optionEntry);
                }
                $alertSystemInformation["options"] = $optionsArray;
                break;

            // generate nodes array
            case "NODES":
                $stmt = $mysqli->query('SELECT * FROM nodes');
                $nodesArray = array();
                while($row = $stmt->fetch_assoc()) {
                    $nodeEntry = array("id" => $row["id"],
                        "hostname" => $row["hostname"],
                        "nodeType" => $row["nodeType"],
                        "instance" => $row["instance"],
                        "connected" => $row["connected"],
                        "version" => $row["version"],
                        "rev" => $row["rev"],
                        "username" => $row["username"],
                        "persistent" => $row["persistent"]);
                    array_push($nodesArray, $nodeEntry);
                }
                $alertSystemInformation["nodes"] = $nodesArray;
                break;

            // generate sensors array
            case "SENSORS":
                $stmt = $mysqli->query('SELECT * FROM sensors');
                $resultSensors = $stmt->fetch_all(MYSQLI_ASSOC);

                $stmt = $mysqli->query('SELECT * FROM sensorsAlertLevels');
                $resultSensorsAlertLevels = $stmt->fetch_all(MYSQLI_ASSOC);

                $sensorsAlertLevelsArray = array();
                while($row = $stmt->fetch_assoc()) {
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
                            $stmt = $mysqli->query("SELECT value, unit FROM "
                                . "sensorsDataInt WHERE sensorId = "
                                . intval($row["id"]));
                            $dataRow = $stmt->fetch_assoc();
                            $data = $dataRow["value"];
                            break;

                        case SensorDataType::FLOAT_TYPE:
                            $stmt = $mysqli->query("SELECT value, unit FROM "
                                . "sensorsDataFloat WHERE sensorId = "
                                . intval($row["id"]));
                            $dataRow = $stmt->fetch_assoc();
                            $data = $dataRow["value"];
                            break;

                        case SensorDataType::NONE_TYPE:
                        default:
                            break;
                    }

                    $sensorEntry = array("id" => $row["id"],
                        "clientSensorId" => $row["clientSensorId"],
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
                $stmt = $mysqli->query("SELECT * FROM alerts");
                $resultAlerts = $stmt->fetch_all(MYSQLI_ASSOC);

                $stmt = $mysqli->query("SELECT * FROM alertsAlertLevels");
                $alertsAlertLevelsArray = array();
                while($row = $stmt->fetch_assoc()) {
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
                        "clientAlertId" => $row["clientAlertId"],
                        "nodeId" => $row["nodeId"],
                        "description" => $row["description"],
                        "alertLevels" => $alertLevelArray);
                    array_push($alertsArray, $alertEntry);
                }
                $alertSystemInformation["alerts"] = $alertsArray;
                break;

            // generate managers array
            case "MANAGERS":
                $stmt = $mysqli->query("SELECT * FROM managers");
                $managersArray = array();
                while($row = $stmt->fetch_assoc()) {
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
                    $stmt = $mysqli->query("SELECT * FROM sensorAlerts ORDER BY id DESC "
                        . "LIMIT " . $rangeStart . "," . $number);
                    $resultSensorAlerts = $stmt->fetch_all(MYSQLI_ASSOC);
                }
                // no range is given => get all sensor alerts
                else {
                    $stmt = $mysqli->query("SELECT * FROM sensorAlerts ORDER BY id DESC");
                    $resultSensorAlerts = $stmt->fetch_all(MYSQLI_ASSOC);
                }

                // Get alert levels of the sensor alerts.
                $stmt = $mysqli->query("SELECT * FROM sensorAlertsAlertLevels");
                $sensorAlertsAlertLevelsArray = array();
                while($row = $stmt->fetch_assoc()) {
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
                            $stmt = $mysqli->query("SELECT value, unit FROM "
                                . "sensorAlertsDataInt WHERE sensorAlertId = "
                                . intval($row["id"]));
                            $dataRow = $stmt->fetch_assoc();
                            $data = $dataRow["value"];
                            break;

                        case SensorDataType::FLOAT_TYPE:
                            $stmt = $mysqli->query("SELECT value, unit FROM "
                                . "sensorAlertsDataFloat WHERE "
                                . "sensorAlertId = "
                                . intval($row["id"]));
                            $dataRow = $stmt->fetch_assoc();
                            $data = $dataRow["value"];
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
                $stmt = $mysqli->query("SELECT * FROM alertLevels");
                $alertLevelsArray = array();
                while($row = $stmt->fetch_assoc()) {

                    // get profiles of alert level
                    $subStmt = $mysqli->prepare("SELECT profileId FROM alertLevelsProfiles WHERE alertLevel=?");
                    $subStmt->bind_param("i", $row["alertLevel"]);
                    $subStmt->execute();
                    $subResult = $subStmt->get_result();

                    $profilesArray = array();
                    while($subRow = $subResult->fetch_assoc()) {
                        array_push($profilesArray, $subRow["profileId"]);
                    }

                    $alertLevelEntry = array(
                        "alertLevel" => $row["alertLevel"],
                        "name" => $row["name"],
                        "instrumentation_active" => $row["instrumentation_active"],
                        "profiles" => $profilesArray,);
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
    echo "Error: \$data not set correctly.";
}


?>
