<?php

// written by sqall
// twitter: https://twitter.com/sqall01
// blog: http://blog.h4des.org
// github: https://github.com/sqall01
// 
// Licensed under the GNU Affero General Public License, version 3.

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

// check if the GET parameter for changing the system profile is set
if(isset($_GET["profilechange"]) && $configUnixSocketActive) {

	// validate integer
	$profileId = intval($_GET["profilechange"]);

	// open connection to local manager client
	@$fd = stream_socket_client(
		"unix://" . $configUnixSocketPath, $errno, $errstr, 5);

	// check if connection could be established
	if ($errno != 0) {
		echo "Error: Could not connect to local manager client<br />";
		echo "Reason: " . $errstr . "\n";
		exit(1);
	}

	// send profile option according to the given parameter
	$message = array();
	$message["message"] = "option";
	$payload = array();
	$payload["optionType"] = "profile";
	$payload["value"] = $profileId;
	$payload["timeDelay"] = 0;
	$message["payload"] = $payload;

	fwrite($fd, json_encode($message));

	// get response
	$response = json_decode(fread($fd, 1024), true);
	if($response == NULL) {
		echo "Error: Could not decode server response.";
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

		<title>AlertR Mobile Manager</title>

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

		<div class="elementShown" id="loader" align="center">
			<table border="0" width="300">
				<tr>
					<td align="center">
						<img src="img/loader.gif" />
						<p>Loading ...</p>
					</td>
				</tr>
			</table>
		</div>

		<div class="elementHidden" id="content" align="center">
			<table border="0" width="300" id="contentTable">
				<tbody id="contentTableBody">
				</tbody>
			</table>
		</div>

		<script src="js/main.js"></script>

	</body>

</html>
