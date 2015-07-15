// set global configuration variables
var request = new XMLHttpRequest();


// function to compare sensor alert objects
function compareSensorAlertsDesc(a, b) {
	if(a["timeReceived"] < b["timeReceived"]) {
		return 1;
	}
	if(a["timeReceived"] > b["timeReceived"]) {
		return -1;
	}
	return 0;
}


// processes the response of the server for the
// requested data
function processResponse() {

	if (request.readyState == 4) {

		// remove old nodes output
		// and generate a new clear one
		var nodeTableObj = document.getElementById("contentTable");
		var newBody = document.createElement("tbody");
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		var newB = document.createElement("b");
		newB.textContent = "Nodes:";
		newTd.appendChild(newB);
		newTr.appendChild(newTd);
		newBody.appendChild(newTr);
		var oldBody = document.getElementById("contentTableBody");
		oldBody.removeAttribute("id");
		newBody.setAttribute("id", "contentTableBody");
		nodeTableObj.replaceChild(newBody, oldBody);
		delete oldBody;

		// get JSON response and parse it
		var response = request.responseText;
		var alertSystemInformation = JSON.parse(response);
		var internals = alertSystemInformation["internals"];
		var options = alertSystemInformation["options"];
		var nodes = alertSystemInformation["nodes"];
		var sensors = alertSystemInformation["sensors"];
		var managers = alertSystemInformation["managers"];
		var alerts = alertSystemInformation["alerts"];
		var alertLevels = alertSystemInformation["alertLevels"];
		var sensorAlerts = alertSystemInformation["sensorAlerts"];

		// get server time
		var serverTime = 0.0;
		for(i = 0; i < internals.length; i++) {
			if(internals[i]["type"] == "serverTime") {
				serverTime = internals[i]["value"]
			}
		}

		sensorAlerts.sort(compareSensorAlertsDesc);

		// add all sensor alerts to the output
		for(i = 0; i < sensorAlerts.length; i++) {

			var sensorAlertId = sensorAlerts[i]["id"];
			var sensorId = sensorAlerts[i]["sensorId"];
			var timeReceived = sensorAlerts[i]["timeReceived"];
			var jsonData = sensorAlerts[i]["data"];
			var state = sensorAlerts[i]["state"];
			var description = sensorAlerts[i]["description"];
			var data = JSON.parse(jsonData);


			var boxDiv = document.createElement("div");
			boxDiv.className = "box";

			var sensorAlertTable = document.createElement("table");
			sensorAlertTable.style.width = "100%";
			sensorAlertTable.setAttribute("border", "0");
			boxDiv.appendChild(sensorAlertTable);


			// add id to the sensor alert
			newTr = document.createElement("tr");
			newTd = document.createElement("td");
			newTd.textContent = "Sensor Alert: " + sensorAlertId;			
			newTd.className = "boxHeaderTd";
			newTr.appendChild(newTd);
			sensorAlertTable.appendChild(newTr);


			// generate date string from timestamp
			localDate = new Date(timeReceived * 1000);
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


			// add description to the sensor alert
			newTr = document.createElement("tr");
			newTd = document.createElement("td");
			newB = document.createElement("b");
			newB.textContent = "Description:";
			newTd.appendChild(newB);
			newTd.className = "boxEntryTd";
			newTr.appendChild(newTd);
			sensorAlertTable.appendChild(newTr);

			newTr = document.createElement("tr");
			newTd = document.createElement("td");
			newTd.textContent = description;
			newTd.className = "neutralTd";
			newTr.appendChild(newTd);
			sensorAlertTable.appendChild(newTr);


			// add state to the sensor alert
			newTr = document.createElement("tr");
			newTd = document.createElement("td");
			newB = document.createElement("b");
			newB.textContent = "State:";
			newTd.appendChild(newB);
			newTd.className = "boxEntryTd";
			newTr.appendChild(newTd);
			sensorAlertTable.appendChild(newTr);

			newTr = document.createElement("tr");
			newTd = document.createElement("td");
			if(state == 1) {
				newTd.textContent = "triggered";
			}
			else {
				newTd.textContent = "normal";
			}
			newTd.className = "neutralTd";
			newTr.appendChild(newTd);
			sensorAlertTable.appendChild(newTr);


			// add time received to the sensor alert
			var newTr = document.createElement("tr");
			var newTd = document.createElement("td");
			var newB = document.createElement("b");
			newB.textContent = "Time received:";
			newTd.appendChild(newB);
			newTd.className = "boxEntryTd";
			newTr.appendChild(newTd);
			sensorAlertTable.appendChild(newTr);

			var newTr = document.createElement("tr");
			var newTd = document.createElement("td");
			newTd.textContent = monthString + "/" + dateString + "/" +
				yearString + " " + hoursString + ":" +
				minutesString + ":" + secondsString;
			newTd.className = "neutralTd";
			newTr.appendChild(newTd);
			sensorAlertTable.appendChild(newTr);
			newTd.className = "neutralTd";
			newTr.appendChild(newTd);
			sensorAlertTable.appendChild(newTr);


			// check if a message was sent along with the sensor alert
			if(data.hasOwnProperty("message")) {

				// add received message to the sensor alert
				var newTr = document.createElement("tr");
				var newTd = document.createElement("td");
				var newB = document.createElement("b");
				newB.textContent = "Message:";
				newTd.appendChild(newB);
				newTd.className = "boxEntryTd";
				newTr.appendChild(newTd);
				sensorAlertTable.appendChild(newTr);

				var newTr = document.createElement("tr");
				var newTd = document.createElement("td");
				newTd.textContent = data["message"];
				newTd.className = "neutralTd";
				newTr.appendChild(newTd);
				sensorAlertTable.appendChild(newTr);
				newTd.className = "neutralTd";
				newTr.appendChild(newTd);
				sensorAlertTable.appendChild(newTr);
			}


			// add sensor alert to the sensor alert table
			sensorAlertTableObj =
				document.getElementById("contentTableBody");
			newTr = document.createElement("tr");
			newTd = document.createElement("td");
			newTd.appendChild(boxDiv);
			newTr.appendChild(newTd);
			sensorAlertTableObj.appendChild(newTr);


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