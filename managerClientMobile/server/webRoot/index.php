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

		<title>alertR mobile manager</title>

	</head>


	<body>

		<p><b>alertR mobile manager</b></p>

		<table border="0" width="300" id="optionsTable">
			<tr>
				<td>
					<b>Options:</b>
				</td>
			</tr>
			<tr>
				<td bgcolor="#d5cbcb">
					<b>Status</b>
				</td>
			</tr>
			<tr>
				<td id="alertSystemActive">
					Unknown
				</td>
			</tr>
			<tr>
				<td>
					<a href="javascript:confirmation(1)">activate</a>
					| |
					<a href="javascript:confirmation(0)">deactivate</a>
				</td>
			</tr>
		</table>

		<table border="0" width="300" id="sensorsTable">
			<tbody id="sensorsTableBody">
			</tbody>
		</table>

		<script>

			// set global configuration variables
			var request = new XMLHttpRequest();


			// simple function to ask for confirmation if the alarm system
			// should be activated
			function confirmation(activate) {

				if(activate == 1) {
					result = confirm("Do you really want to activate " + 
						"the alarm system?");
					if(result) {
						window.location = "index.php?activate=1";
					}
				}
				else if(activate == 0) {
					result = confirm("Do you really want to deactivate " + 
						"the alarm system?");
					if(result) {
						window.location = "index.php?activate=0";
					}
				}
			}


			// processes the response of the server for the
			// requested data
			function processResponse() {
				if (request.readyState == 4) {

					// remove old sensors output
					// and generate a new clear one
					sensorTableObj = document.getElementById("sensorsTable");
					newBody = document.createElement("tbody");
					newTr = document.createElement("tr");
					newTd = document.createElement("td");
					newB = document.createElement("b");
					newB.textContent = "Sensors:";
					newTd.appendChild(newB);
					newTr.appendChild(newTd);
					newBody.appendChild(newTr);
					oldBody = document.getElementById("sensorsTableBody");
					oldBody.removeAttribute("id");
					newBody.setAttribute("id", "sensorsTableBody");
					sensorTableObj.replaceChild(newBody, oldBody);
					delete oldBody;

					// get JSON response and parse it
					response = request.responseText;
					alertSystemInformation = JSON.parse(response);
					options = alertSystemInformation["options"];
					nodes = alertSystemInformation["nodes"];
					sensors = alertSystemInformation["sensors"];
					managers = alertSystemInformation["managers"];
					alerts = alertSystemInformation["alerts"];
					alertLevels = alertSystemInformation["alertLevels"];

					// process options of the alert system
					for(i = 0; i < options.length; i++) {

						// only evaluate "alertSystemActive"
						if(options[i]["type"] == "alertSystemActive") {

							// get alert system active object
							alertSystemActiveObj = 
								document.getElementById("alertSystemActive");

							// set object text and color according
							// to its status
							if(options[i]["value"] == 0) {
								alertSystemActiveObj.style.backgroundColor =
									"#ff0000";
								alertSystemActiveObj.textContent =
									"Deactivated"
							}
							if(options[i]["value"] == 1) {
								alertSystemActiveObj.style.backgroundColor =
									"#00ff00";
								alertSystemActiveObj.textContent =
									"Activated"
							}
							break;
						}
					}

					// add all sensors to the output
					for(i = 0; i < sensors.length; i++) {

						// get hostname of the client which manages this sensor
						hostname = "unknown";
						connected = 0
						for(j = 0; j < nodes.length; j++) {
							if(nodes[j]["id"] == sensors[i]["nodeId"]) {
								hostname = nodes[j]["hostname"];
								connected = nodes[j]["connected"];
								break;
							}
						}

						state = sensors[i]["state"];

						sensorTable = document.createElement("table");
						sensorTable.style.width = "100%";
						sensorTable.setAttribute("border", "0");

						// add hostname to the sensor
						newTr = document.createElement("tr");
						newTd = document.createElement("td");
						newTd.textContent = hostname						
						newTd.style.backgroundColor = "#d5cbcb";
						newTr.appendChild(newTd);
						sensorTable.appendChild(newTr);

						// add description to the sensor
						newTr = document.createElement("tr");
						newTd = document.createElement("td");
						newTd.textContent = "Desc.: " +
							sensors[i]["description"]
						// set color according to state and last update
						if(connected == 0) {
							// set background color to red
							newTd.style.backgroundColor = "#ff0000";
						}
						else if(state != 1
							&& connected == 1) {
							// set background color to green
							newTd.style.backgroundColor = "#00ff00";
						}
						else {
							// set background color to yellow
							newTd.style.backgroundColor = "#fff000";
						}
						// set color to red if the sensor has timed out
						currentTime = parseInt(new Date().getTime() / 1000)
						if(sensors[i]["lastStateUpdated"] <
							(currentTime - 2* 60)) {
							// set background color to red
							newTd.style.backgroundColor = "#ff0000";
						}
						newTr.appendChild(newTd);
						sensorTable.appendChild(newTr);

						// generate date string from timestamp
						localDate =
							new Date(sensors[i]["lastStateUpdated"] * 1000);
						yearString = localDate.getFullYear();
						monthString =
							("0" + (localDate.getMonth() + 1)).slice(-2);
						dateString =
							("0" + localDate.getDate()).slice(-2);
						hoursString =
							("0" + localDate.getHours()).slice(-2);
						minutesString =
							("0" + localDate.getMinutes()).slice(-2);
						secondsString =
							("0" + localDate.getSeconds()).slice(-2);

						// add last updated state to the sensor
						newTr = document.createElement("tr");
						newTd = document.createElement("td");
						newTd.textContent = "Last updated: " +
							monthString + "/" + dateString + "/" +
							yearString + " " + hoursString + ":" +
							minutesString + ":" + secondsString;
						// set color according to state and last update
						if(connected == 0) {
							// set background color to red
							newTd.style.backgroundColor = "#ff0000";
						}
						else if(state != 1
							&& connected == 1) {
							// set background color to green
							newTd.style.backgroundColor = "#00ff00";
						}
						else {
							// set background color to yellow
							newTd.style.backgroundColor = "#fff000";
						}
						// set color to red if the sensor has timed out
						currentTime = parseInt(new Date().getTime() / 1000)
						if(sensors[i]["lastStateUpdated"] <
							(currentTime - 2* 60)) {
							// set background color to red
							newTd.style.backgroundColor = "#ff0000";
						}
						newTr.appendChild(newTd);
						sensorTable.appendChild(newTr);

						// add sensor to the sensor table
						sensorTableBodyObj =
							document.getElementById("sensorsTableBody");
						newTr = document.createElement("tr");
						newTd = document.createElement("td");
						newTd.appendChild(sensorTable);
						newTr.appendChild(newTd);
						sensorTableBodyObj.appendChild(newTr);
					}
				}
			}


			// requests the data of the alert system
			function requestData() {
				url = "./getJson.php";
				request.open("GET", url, true);
				request.onreadystatechange = processResponse;
				request.send(null);

				// wait 10 seconds before requesting the next data update
				window.setTimeout("requestData()", 10000);	
			}

			requestData();
		</script>


	</body>
</html>