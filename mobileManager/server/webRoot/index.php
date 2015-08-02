<?php

// written by sqall
// twitter: https://twitter.com/sqall01
// blog: http://blog.h4des.org
// github: https://github.com/sqall01
// 
// Licensed under the GNU Public License, version 2.


// check if the GET parameter for activate/deactivate the alert system
// is set
if(isset($_GET["activate"])) {

	// validate integer
	$activate = intval($_GET["activate"]);

	// include config data
	require_once("./config/config.php");

	// open connection to local manager client
	@$fd = stream_socket_client(
		"unix://" . $configUnixSocket, $errno, $errstr, 5);

	// check if connection could be established
	if ($errno != 0) {
		echo "Error: Could not connect to local manager client<br />";
		echo "Reason: " . $errstr . "\n";
		exit(1);
	}

	// send activate/deactivate according to the given parameter
	if($activate === 0) {
		fwrite($fd, "DEACTIVATE");
	}
	else if($activate === 1) {
		fwrite($fd, "ACTIVATE");
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

	<body>

		<table border="0" width="300" id="contentTable">
			<tbody id="contentTableBody">
			</tbody>
		</table>

		<script src="js/events.js"></script>
		<script src="js/main.js"></script>

	</body>

</html>