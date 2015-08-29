<?php

// written by sqall
// twitter: https://twitter.com/sqall01
// blog: http://blog.h4des.org
// github: https://github.com/sqall01
// 
// Licensed under the GNU Public License, version 2.

// include config data
require_once("./config/config.php");

// check if the GET parameter for activate/deactivate the alert system
// is set
if(isset($_GET["activate"]) && $configUnixSocketActive) {

	// validate integer
	$activate = intval($_GET["activate"]);

	// open connection to local manager client
	@$fd = stream_socket_client(
		"unix://" . $configUnixSocketPath, $errno, $errstr, 5);

	// check if connection could be established
	if ($errno != 0) {
		echo "Error: Could not connect to local manager client<br />";
		echo "Reason: " . $errstr . "\n";
		exit(1);
	}

	// send activate/deactivate according to the given parameter
	$message = array();
	$message["message"] = "option";
	if($activate === 0) {
		$payload = array();
		$payload["optionType"] = "alertSystemActive";
		$payload["value"] = 0;
		$payload["timeDelay"] = 0;
		$message["payload"] = $payload;
	}
	else {
		$payload = array();
		$payload["optionType"] = "alertSystemActive";
		$payload["value"] = 1;
		$payload["timeDelay"] = 0;
		$message["payload"] = $payload;	
	}
	fwrite($fd, json_encode($message));

	// get response
	$response = json_decode(fread($fd, 1024), true);
	if($response == NULL) {
		echo "Error: Could not decode server response";
		exit(1);
	}
	else {
		if($response["payload"]["result"] != "ok") {
			echo "Error: Received response is not 'ok': "
				. $response["payload"]["result"];
			exit(1);
		}
	}

	// close connection
	fclose($fd);

	// wait two seconds in order to let the server process the request
	sleep(2);
}

?>


<html>
	<head>

		<meta content="text/html;charset=utf-8" http-equiv="Content-Type">

		<title>alertR mobile manager</title>

		<link rel="stylesheet" href="css/style.css" />

	</head>

	<body data-configUnixSocketActive="<?php
			if($configUnixSocketActive) {
				echo "true";
			}
			else {
				echo "false";
			}
		?>" >

		<table border="0" width="300" id="contentTable">
			<tbody id="contentTableBody">
			</tbody>
		</table>

		<script src="js/events.js"></script>
		<script src="js/main.js"></script>

	</body>

</html>