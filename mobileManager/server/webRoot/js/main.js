// set global configuration variables
var request = new XMLHttpRequest();
var setTimeoutIdRequest = null;
var setTimeoutIdOnlineCheck = null;
var sensorAlertsNumber = 50;
var sensorAlertsRangeStart = 0;
var eventsNumber = 50;
var eventsRangeStart = 0;
var configUnixSocketActive =
	(document.body.dataset.configunixsocketactive == "true");
var eventTypes = new Array("changeAlert", "changeManager", "changeNode",
	"changeOption", "changeSensor", "connectedChange", "deleteAlert",
	"deleteManager", "deleteNode", "deleteSensor", "newAlert", "newManager",
	"newNode", "newOption", "newSensor", "newVersion", "sensorAlert",
	"sensorTimeOut", "stateChange");
var eventTypesFilter = new Object();
for(var i = 0; i < eventTypes.length; i++) {
	eventTypesFilter[eventTypes[i]] = true;
}

// global objects filled with server responses
var alertLevels = null;
var alerts = null;
var events = null;
var internals = null;
var managers = null;
var nodes = null;
var options = null;
var sensorAlerts = null;
var sensors = null;

// needed to check the time out of the alertR database instance
var serverTime = 0.0;
var lastServerTime = 0.0;
var lastServerTimeUpdate = null;
var online = false;
var timeoutInterval = 80 // in seconds
var serverTimeTd = null;
var onlineTd = null;

// gives the output that is currently shown
var currentOutput = null;

var lastResponse = null;


// adds a menu for the navigation to the given table body
function addMenu(newBody, current) {

	// check if alertR database instance is online
	checkOnline();

	// generate date string from timestamp
	localDate = new Date(serverTime * 1000);
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
	serverTimeString = monthString + "/" + dateString + "/" +
		yearString + " " + hoursString + ":" +
		minutesString + ":" + secondsString;

	var boxDiv = document.createElement("div");
	boxDiv.className = "box";

	var menuTable = document.createElement("table");
	menuTable.style.width = "100%";
	menuTable.setAttribute("border", "0");
	boxDiv.appendChild(menuTable);

	// add status output
	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	var newB = document.createElement("b");
	newB.textContent = "Status:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	menuTable.appendChild(newTr);

	var newTr = document.createElement("tr");
	onlineTd = document.createElement("td");
	if(online) {
		onlineTd.className = "normalTd";
		onlineTd.textContent = "online";
	}
	else {
		onlineTd.className = "failTd";
		onlineTd.textContent = "offline";
	}
	newTr.appendChild(onlineTd);
	menuTable.appendChild(newTr);

	// add server time output
	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	var newB = document.createElement("b");
	newB.textContent = "Server Time:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	menuTable.appendChild(newTr);

	var newTr = document.createElement("tr");
	serverTimeTd = document.createElement("td");
	if(online) {
		serverTimeTd.className = "normalTd";
		serverTimeTd.textContent = serverTimeString;
	}
	else {
		serverTimeTd.className = "failTd";
		serverTimeTd.textContent = serverTimeString;
	}
	newTr.appendChild(serverTimeTd);
	menuTable.appendChild(newTr);

	// process options of the alert system
	for(var i = 0; i < options.length; i++) {

		// only evaluate "alertSystemActive"
		if(options[i]["type"].toUpperCase() == "ALERTSYSTEMACTIVE") {

			// add status of alert system
			var newTr = document.createElement("tr");
			var newTd = document.createElement("td");
			var newB = document.createElement("b");
			newB.textContent = "Status:";
			newTd.appendChild(newB);
			newTd.className = "boxEntryTd";
			newTr.appendChild(newTd);
			menuTable.appendChild(newTr);

			var newTr = document.createElement("tr");
			var newTd = document.createElement("td");
			if(options[i]["value"] == 0) {
				newTd.className = "deactivatedTd";
				newTd.textContent = "deactivated";
			}
			if(options[i]["value"] == 1) {
				newTd.className = "activatedTd";
				newTd.textContent = "activated";
			}
			newTr.appendChild(newTd);
			menuTable.appendChild(newTr);

			var newTr = document.createElement("tr");
			var newTd = document.createElement("td");
			newTd.className = "neutralTd";
			newTr.appendChild(newTd);
			menuTable.appendChild(newTr);

			// only display buttons if unix socket is activated
			if(configUnixSocketActive) {
				// create a temporary table to have the
				// buttons next to each other
				var tempTable = document.createElement("table");
				tempTable.style.width = "100%";
				tempTable.setAttribute("border", "0");
				newTd.appendChild(tempTable);

				var newTr = document.createElement("tr");
				tempTable.appendChild(newTr)

				var newTd = document.createElement("td");
				newTd.style.width = "50%";
				newTd.className = "buttonTd";
				var newA = document.createElement("a");
				newA.className = "buttonA";
				newA.textContent = "activate";
				newA.href = "javascript:void(0)";
				newA.onclick = function(){ confirmation(1); };
				newTd.appendChild(newA);
				newTr.appendChild(newTd);

				var newTd = document.createElement("td");
				newTd.style.width = "50%";
				newTd.className = "buttonTd";
				var newA = document.createElement("a");
				newA.className = "buttonA";
				newA.textContent = "deactivate";
				newA.href = "javascript:void(0)";
				newA.onclick = function(){ confirmation(0); };
				newTd.appendChild(newA);
				newTr.appendChild(newTd);
			}

			break;
		}
	}

	// add menu output
	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	var newB = document.createElement("b");
	newB.textContent = "Menu:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	menuTable.appendChild(newTr);

	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	if(current == "alertLevels") {
		newTd.className = "buttonActiveTd";
	}
	else {
		newTd.className = "buttonTd";
	}
	var newA = document.createElement("a");
	newA.className = "buttonA";
	newA.textContent = "Alert Levels";
	newA.href = "javascript:void(0)";
	newA.onclick = function(){ changeOutput("alertLevels"); };
	newTd.appendChild(newA);
	newTr.appendChild(newTd);
	menuTable.appendChild(newTr);

	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	if(current == "nodes") {
		newTd.className = "buttonActiveTd";
	}
	else {
		newTd.className = "buttonTd";
	}
	var newA = document.createElement("a");
	newA.className = "buttonA";
	newA.textContent = "Clients";
	newA.href = "javascript:void(0)";
	newA.onclick = function(){ changeOutput("nodes"); };
	newTd.appendChild(newA);
	newTr.appendChild(newTd);
	menuTable.appendChild(newTr);

	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	if(current == "alerts") {
		newTd.className = "buttonActiveTd";
	}
	else {
		newTd.className = "buttonTd";
	}
	var newA = document.createElement("a");
	newA.className = "buttonA";
	newA.textContent = "Clients (Type: Alert)";
	newA.href = "javascript:void(0)";
	newA.onclick = function(){ changeOutput("alerts"); };
	newTd.appendChild(newA);
	newTr.appendChild(newTd);
	menuTable.appendChild(newTr);

	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	if(current == "managers") {
		newTd.className = "buttonActiveTd";
	}
	else {
		newTd.className = "buttonTd";
	}
	var newA = document.createElement("a");
	newA.className = "buttonA";
	newA.textContent = "Clients (Type: Manager)";
	newA.href = "javascript:void(0)";
	newA.onclick = function(){ changeOutput("managers"); };
	newTd.appendChild(newA);
	newTr.appendChild(newTd);
	menuTable.appendChild(newTr);

	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	if(current == "sensors") {
		newTd.className = "buttonActiveTd";
	}
	else {
		newTd.className = "buttonTd";
	}
	var newA = document.createElement("a");
	newA.className = "buttonA";
	newA.textContent = "Clients (Type: Sensor)";
	newA.href = "javascript:void(0)";
	newA.onclick = function(){ changeOutput("sensors"); };
	newTd.appendChild(newA);
	newTr.appendChild(newTd);
	menuTable.appendChild(newTr);

	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	if(current == "events") {
		newTd.className = "buttonActiveTd";
	}
	else {
		newTd.className = "buttonTd";
	}
	var newA = document.createElement("a");
	newA.className = "buttonA";
	newA.textContent = "Events";
	newA.href = "javascript:void(0)";
	newA.onclick = function(){ changeOutput("events"); };
	newTd.appendChild(newA);
	newTr.appendChild(newTd);
	menuTable.appendChild(newTr);

	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	if(current == "overview") {
		newTd.className = "buttonActiveTd";
	}
	else {
		newTd.className = "buttonTd";
	}
	var newA = document.createElement("a");
	newA.className = "buttonA";
	newA.textContent = "Overview";
	newA.href = "javascript:void(0)";
	newA.onclick = function(){ changeOutput("overview"); };
	newTd.appendChild(newA);
	newTr.appendChild(newTd);
	menuTable.appendChild(newTr);

	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	if(current == "sensorAlerts") {
		newTd.className = "buttonActiveTd";
	}
	else {
		newTd.className = "buttonTd";
	}
	var newA = document.createElement("a");
	newA.className = "buttonA";
	newA.textContent = "Sensor Alerts";
	newA.href = "javascript:void(0)";
	newA.onclick = function(){ changeOutput("sensorAlerts"); };
	newTd.appendChild(newA);
	newTr.appendChild(newTd);
	menuTable.appendChild(newTr);

	var contentTableObj =
		document.getElementById("contentTableBody");
	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	newTd.appendChild(boxDiv);
	newTr.appendChild(newTd);
	contentTableObj.appendChild(newTr);

}


// changes the global configuration variable (eventsNumber)
function changeEventsNumber(number) {

	if(eventsNumber == number) {
		outputEvents();
	}
	else {
		eventsNumber = number;

		// get new data because of the changed number 
		requestData("events");	
	}
}


// changes the global configuration variable (eventTypesFilter)
// and updates the filter
function changeEventTypesFilter(eventType) {

	var usedTd = document.getElementById(eventType + "_td");

	// toggle entry
	if(eventTypesFilter[eventType]) {
		eventTypesFilter[eventType] = false;
		usedTd.className = "buttonTd";
	}
	else {
		eventTypesFilter[eventType] = true;
		usedTd.className = "buttonActiveTd";
	}

	// check if objects are set before output them
	if(events == null || internals == null) {
		requestData("events");
	}
	else {
		outputEvents();
	}

}


// changes the output that is shown (and requests data if needed)
function changeOutput(content) {

	// show loader and hide content
	var loaderObj = document.getElementById("loader");
	loaderObj.className = "elementShown";
	var contentObj = document.getElementById("content");
	contentObj.className = "elementHidden";

	var currentTime = new Date()

	switch(content) {
		case "alertLevels":
			currentOutput = "alertLevels";
			if(internals == null
				|| options == null
				|| alertLevels == null
				|| (lastResponse.getTime() + 10000) < currentTime.getTime()) {
				requestData("alertLevels");
			}
			else {
				// clear timeout if it is set
				if(setTimeoutIdRequest != null) {
					window.clearTimeout(setTimeoutIdRequest);
				}
				nextContent = "alertLevels";
				nextRequest = "requestData(\"" + nextContent + "\")";
				setTimeoutIdRequest = window.setTimeout(nextRequest, 10000);

				outputAlertLevels();
			}
			break;
		case "alerts":
			currentOutput = "alerts";
			if(internals == null
				|| options == null
				|| alertLevels == null
				|| alerts == null
				|| nodes == null
				|| (lastResponse.getTime() + 10000) < currentTime.getTime()) {
				requestData("alerts");
			}
			else {
				// clear timeout if it is set
				if(setTimeoutIdRequest != null) {
					window.clearTimeout(setTimeoutIdRequest);
				}
				nextContent = "alerts";
				nextRequest = "requestData(\"" + nextContent + "\")";
				setTimeoutIdRequest = window.setTimeout(nextRequest, 10000);

				outputAlerts();
			}
			break;
		case "events":
			currentOutput = "events";
			if(internals == null
				|| options == null
				|| events == null
				|| events.length < eventsNumber
				|| (lastResponse.getTime() + 10000) < currentTime.getTime()) {
				requestData("events");
			}
			else {
				// clear timeout if it is set
				if(setTimeoutIdRequest != null) {
					window.clearTimeout(setTimeoutIdRequest);
				}
				nextContent = "events";
				nextRequest = "requestData(\"" + nextContent + "\")";
				setTimeoutIdRequest = window.setTimeout(nextRequest, 10000);

				outputEvents();
			}
			break;
		case "managers":
			currentOutput = "managers";
			if(internals == null
				|| options == null
				|| nodes == null
				|| managers == null
				|| (lastResponse.getTime() + 10000) < currentTime.getTime()) {
				requestData("managers");
			}
			else {
				// clear timeout if it is set
				if(setTimeoutIdRequest != null) {
					window.clearTimeout(setTimeoutIdRequest);
				}
				nextContent = "managers";
				nextRequest = "requestData(\"" + nextContent + "\")";
				setTimeoutIdRequest = window.setTimeout(nextRequest, 10000);

				outputManagers();
			}
			break;
		case "nodes":
			currentOutput = "nodes";
			if(internals == null
				|| options == null
				|| nodes == null
				|| (lastResponse.getTime() + 10000) < currentTime.getTime()) {
				requestData("nodes");
			}
			else {
				// clear timeout if it is set
				if(setTimeoutIdRequest != null) {
					window.clearTimeout(setTimeoutIdRequest);
				}
				nextContent = "nodes";
				nextRequest = "requestData(\"" + nextContent + "\")";
				setTimeoutIdRequest = window.setTimeout(nextRequest, 10000);

				outputNodes();
			}
			break;
		case "sensorAlerts":
			currentOutput = "sensorAlerts";
			if(internals == null
				|| options == null
				|| sensorAlerts == null
				|| sensorAlerts.length < sensorAlertsNumber
				|| (lastResponse.getTime() + 10000) < currentTime.getTime()) {
				requestData("sensorAlerts");
			}
			else {
				// clear timeout if it is set
				if(setTimeoutIdRequest != null) {
					window.clearTimeout(setTimeoutIdRequest);
				}
				nextContent = "sensorAlerts";
				nextRequest = "requestData(\"" + nextContent + "\")";
				setTimeoutIdRequest = window.setTimeout(nextRequest, 10000);

				outputSensorAlerts();
			}
			break;
		case "sensors":
			currentOutput = "sensors";
			if(internals == null
				|| options == null
				|| nodes == null
				|| sensors == null
				|| alertLevels == null
				|| (lastResponse.getTime() + 10000) < currentTime.getTime()) {
				requestData("sensors");
			}
			else {
				// clear timeout if it is set
				if(setTimeoutIdRequest != null) {
					window.clearTimeout(setTimeoutIdRequest);
				}
				nextContent = "sensors";
				nextRequest = "requestData(\"" + nextContent + "\")";
				setTimeoutIdRequest = window.setTimeout(nextRequest, 10000);

				outputSensors();
			}
			break;
		case "overview":
		default:
			currentOutput = "overview";
			if(internals == null
				|| options == null
				|| nodes == null
				|| sensors == null
				|| sensorAlerts == null
				|| (lastResponse.getTime() + 10000) < currentTime.getTime()) {
				requestData("overview");
			}
			else {
				// clear timeout if it is set
				if(setTimeoutIdRequest != null) {
					window.clearTimeout(setTimeoutIdRequest);
				}
				nextContent = "overview";
				nextRequest = "requestData(\"" + nextContent + "\")";
				setTimeoutIdRequest = window.setTimeout(nextRequest, 10000);

				outputOverview();
			}
			break;
	}
}


// changes the global configuration variable (sensorAlertsNumber)
function changeSensorAlertsNumber(number) {

	if(sensorAlertsNumber == number) {
		outputSensorAlerts();
	}
	else {
		sensorAlertsNumber = number;

		// get new data because of the changed number 
		requestData("sensorAlerts");
	}

}


// checks if the alertR database instance is online
function checkOnline() {

	window.clearTimeout(setTimeoutIdOnlineCheck);

	// update last server time if it has changed
	if(serverTime > lastServerTime) {
		lastServerTime = serverTime;
		lastServerTimeUpdate = new Date();
		online = true;

		if(serverTimeTd != null) {
			// generate date string from timestamp
			localDate = new Date(serverTime * 1000);
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
			serverTimeString = monthString + "/" + dateString + "/" +
				yearString + " " + hoursString + ":" +
				minutesString + ":" + secondsString;

			serverTimeTd.className = "normalTd";
			serverTimeTd.textContent = serverTimeString;
		}

		if(onlineTd != null) {
			onlineTd.className = "normalTd";
			onlineTd.textContent = "online";	
		}
	}

	// check if server time has not changed since timeout interval
	var temp = new Date();
	if(temp.getTime() > 
		(lastServerTimeUpdate.getTime() + (timeoutInterval * 1000))) {
		online = false;

		if(onlineTd != null) {
			onlineTd.className = "failTd";
			onlineTd.textContent = "offline";	
		}
	}

	setTimeoutIdOnlineCheck = window.setTimeout("checkOnline()", 2000);
}


// function to compare alert level objects
function compareAlertLevelAsc(a, b) {

	if(a["alertLevel"] < b["alertLevel"]) {
		return -1;
	}
	if(a["alertLevel"] > b["alertLevel"]) {
		return 1;
	}
	return 0;
}


// function to compare alert objects
function compareAlertsAsc(a, b) {

	if(a["description"] < b["description"]) {
		return -1;
	}
	if(a["description"] > b["description"]) {
		return 1;
	}

	// case description == description
	if(a["id"] < b["id"]) {
		return -1;
	}
	if(a["id"] > b["id"]) {
		return 1;
	}

	return 0;
}


// function to compare event objects
function compareEventsDesc(a, b) {

	if(a["timeOccurred"] < b["timeOccurred"]) {
		return 1;
	}
	if(a["timeOccurred"] > b["timeOccurred"]) {
		return -1;
	}

	// case timeOccurred == timeOccurred
	if(a["id"] < b["id"]) {
		return 1;
	}
	if(a["id"] > b["id"]) {
		return -1;
	}

	return 0;
}


// function to compare manager objects
function compareManagersAsc(a, b) {

	if(a["description"] < b["description"]) {
		return -1;
	}
	if(a["description"] > b["description"]) {
		return 1;
	}

	// case description == description
	if(a["id"] < b["id"]) {
		return -1;
	}
	if(a["id"] > b["id"]) {
		return 1;
	}

	return 0;
}


// function to compare node objects
function compareNodesAsc(a, b) {

	// favor not connected nodes
	if(a["connected"] != b["connected"]) {
		if(a["connected"] == 1) {
			return 1;
		}
		return -1;
	}

	if(a["nodeType"] < b["nodeType"]) {
		return -1;
	}
	if(a["nodeType"] > b["nodeType"]) {
		return 1;
	}

	// case nodeType == nodeType
	if(a["instance"] < b["instance"]) {
		return -1;
	}
	if(a["instance"] > b["instance"]) {
		return 1;
	}

	// case instance == instance
	if(a["hostname"] < b["hostname"]) {
		return -1;
	}
	if(a["hostname"] > b["hostname"]) {
		return 1;
	}

	// case hostname == hostname
	if(a["id"] < b["id"]) {
		return -1;
	}
	if(a["id"] > b["id"]) {
		return 1;
	}

	return 0;
}


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


// function to compare sensor objects
function compareSensorsAsc(a, b) {

	if(a["description"].toLowerCase() < b["description"].toLowerCase()) {
		return -1;
	}
	if(a["description"].toLowerCase() > b["description"].toLowerCase()) {
		return 1;
	}

	// case description == description
	if(a["id"] < b["id"]) {
		return -1;
	}
	if(a["id"] > b["id"]) {
		return 1;
	}

	return 0;
}


// simple function to ask for confirmation if the alert system
// should be activated
function confirmation(activate) {

	if(activate == 1 && configUnixSocketActive) {
		result = confirm("Do you really want to activate the alert system?");
		if(result) {

			// show loader and hide content
			var loaderObj = document.getElementById("loader");
			loaderObj.className = "elementShown";
			var contentObj = document.getElementById("content");
			contentObj.className = "elementHidden";

			window.location = "index.php?activate=1";
		}
	}
	else if(activate == 0 && configUnixSocketActive) {
		result = confirm("Do you really want to deactivate " + 
			"the alert system?");
		if(result) {

			// show loader and hide content
			var loaderObj = document.getElementById("loader");
			loaderObj.className = "elementShown";
			var contentObj = document.getElementById("content");
			contentObj.className = "elementHidden";

			window.location = "index.php?activate=0";
		}
	}
}


// processes the response of the server for the
// requested "alert levels" data
function processResponseAlertLevels() {
	
	if (request.readyState == 4) {

		// update time we received the last response
		lastResponse = new Date();

		// get JSON response and parse it
		var response = request.responseText;
		var alertSystemInformation = JSON.parse(response);
		internals = alertSystemInformation["internals"];
		options = alertSystemInformation["options"];
		alertLevels = alertSystemInformation["alertLevels"];

		// only output received data if it is the current output
		if(currentOutput == "alertLevels") {
			// output received data
			outputAlertLevels();
		}
	}
}


// processes the response of the server for the
// requested "alerts" data
function processResponseAlerts() {
	
	if (request.readyState == 4) {

		// update time we received the last response
		lastResponse = new Date();

		// get JSON response and parse it
		var response = request.responseText;
		var alertSystemInformation = JSON.parse(response);
		internals = alertSystemInformation["internals"];
		options = alertSystemInformation["options"];
		nodes = alertSystemInformation["nodes"];
		alerts = alertSystemInformation["alerts"];
		alertLevels = alertSystemInformation["alertLevels"];

		// only output received data if it is the current output
		if(currentOutput == "alerts") {
			// output received data
			outputAlerts();
		}

	}
}


// processes the response of the server for the
// requested "events" data
function processResponseEvents() {

	if (request.readyState == 4) {

		// update time we received the last response
		lastResponse = new Date();

		// get JSON response and parse it
		var response = request.responseText;
		var alertSystemInformation = JSON.parse(response);
		internals = alertSystemInformation["internals"];
		options = alertSystemInformation["options"];
		events = alertSystemInformation["events"];

		// only output received data if it is the current output
		if(currentOutput == "events") {
			// output received data
			outputEvents();
		}

	}
}


// processes the response of the server for the
// requested "managers" data
function processResponseManagers() {
	
	if (request.readyState == 4) {

		// update time we received the last response
		lastResponse = new Date();

		// get JSON response and parse it
		var response = request.responseText;
		var alertSystemInformation = JSON.parse(response);
		internals = alertSystemInformation["internals"];
		options = alertSystemInformation["options"];
		nodes = alertSystemInformation["nodes"];
		managers = alertSystemInformation["managers"];

		// only output received data if it is the current output
		if(currentOutput == "managers") {
			// output received data
			outputManagers();
		}

	}
}


// processes the response of the server for the
// requested "nodes" data
function processResponseNodes() {

	if (request.readyState == 4) {

		// update time we received the last response
		lastResponse = new Date();

		// get JSON response and parse it
		var response = request.responseText;
		var alertSystemInformation = JSON.parse(response);
		internals = alertSystemInformation["internals"];
		options = alertSystemInformation["options"];
		nodes = alertSystemInformation["nodes"];

		// only output received data if it is the current output
		if(currentOutput == "nodes") {
			// output received data
			outputNodes();
		}

	}
}


// processes the response of the server for the
// requested "overview" data
function processResponseOverview() {
	
	if (request.readyState == 4) {

		// update time we received the last response
		lastResponse = new Date();

		// get JSON response and parse it
		var response = request.responseText;
		var alertSystemInformation = JSON.parse(response);
		internals = alertSystemInformation["internals"];
		options = alertSystemInformation["options"];
		nodes = alertSystemInformation["nodes"];
		sensors = alertSystemInformation["sensors"];
		sensorAlerts = alertSystemInformation["sensorAlerts"];

		// only output received data if it is the current output
		if(currentOutput == "overview") {
			// output received data
			outputOverview();
		}

	}
}


// processes the response of the server for the
// requested "sensor alerts" data
function processResponseSensorAlerts() {

	if (request.readyState == 4) {

		// update time we received the last response
		lastResponse = new Date();

		// get JSON response and parse it
		var response = request.responseText;
		var alertSystemInformation = JSON.parse(response);
		internals = alertSystemInformation["internals"];
		options = alertSystemInformation["options"];
		sensorAlerts = alertSystemInformation["sensorAlerts"];

		// only output received data if it is the current output
		if(currentOutput == "sensorAlerts") {
			// output received data
			outputSensorAlerts();
		}

	}
}


// processes the response of the server for the
// requested "sensors" data
function processResponseSensors() {
	
	if (request.readyState == 4) {

		// update time we received the last response
		lastResponse = new Date();

		// get JSON response and parse it
		var response = request.responseText;
		var alertSystemInformation = JSON.parse(response);
		internals = alertSystemInformation["internals"];
		options = alertSystemInformation["options"];
		nodes = alertSystemInformation["nodes"];
		sensors = alertSystemInformation["sensors"];
		alertLevels = alertSystemInformation["alertLevels"];

		// only output received data if it is the current output
		if(currentOutput == "sensors") {
			// output received data
			outputSensors();
		}

	}
}


// requests the data of the alert system
function requestData(content) {

	// clear timeout if it is set
	if(setTimeoutIdRequest != null) {
		window.clearTimeout(setTimeoutIdRequest);
	}
	var nextContent = null;

	switch(content) {
		case "alertLevels":
			var url = "./getJson.php"
				+ "?data[]=internals"
				+ "&data[]=options"
				+ "&data[]=alertlevels";
			request.open("GET", url, true);
			request.onreadystatechange = processResponseAlertLevels;
			nextContent = content;
			break;
		case "alerts":
			var url = "./getJson.php"
				+ "?data[]=internals"
				+ "&data[]=options"
				+ "&data[]=nodes"
				+ "&data[]=alerts"
				+ "&data[]=alertlevels";
			request.open("GET", url, true);
			request.onreadystatechange = processResponseAlerts;
			nextContent = content;
			break;
		case "events":
			if(eventsNumber < 0) {
				var url = "./getJson.php"
					+ "?data[]=internals"
					+ "&data[]=options"
					+ "&data[]=events";
			}
			else {
				var url = "./getJson.php"
					+ "?data[]=internals"
					+ "&data[]=options"
					+ "&data[]=events"
					+ "&eventsRangeStart=" + eventsRangeStart
					+ "&eventsNumber=" + eventsNumber;
			}
			request.open("GET", url, true);
			request.onreadystatechange = processResponseEvents;
			nextContent = content;
			break;
		case "managers":
			var url = "./getJson.php"
				+ "?data[]=internals"
				+ "&data[]=options"
				+ "&data[]=nodes"
				+ "&data[]=managers";
			request.open("GET", url, true);
			request.onreadystatechange = processResponseManagers;
			nextContent = content;
			break;
		case "nodes":
			var url = "./getJson.php"
				+ "?data[]=internals"
				+ "&data[]=options"
				+ "&data[]=nodes";
			request.open("GET", url, true);
			request.onreadystatechange = processResponseNodes;
			nextContent = content;
			break;
		case "sensorAlerts":
			if(sensorAlertsNumber < 0) {
				var url = "./getJson.php"
					+ "?data[]=internals"
					+ "&data[]=options"
					+ "&data[]=sensorAlerts";
			}
			else {
				var url = "./getJson.php"
					+ "?data[]=internals"
					+ "&data[]=options"
					+ "&data[]=sensorAlerts"
					+ "&sensorAlertsRangeStart=" + sensorAlertsRangeStart
					+ "&sensorAlertsNumber=" + sensorAlertsNumber;
			}
			request.open("GET", url, true);
			request.onreadystatechange = processResponseSensorAlerts;
			nextContent = content;
			break;
		case "sensors":
			var url = "./getJson.php"
				+ "?data[]=internals"
				+ "&data[]=options"
				+ "&data[]=nodes"
				+ "&data[]=sensors"
				+ "&data[]=alertLevels";
			request.open("GET", url, true);
			request.onreadystatechange = processResponseSensors;
			nextContent = content;
			break;
		case "overview":
		default:
			var url = "./getJson.php"
				+ "?data[]=internals"
				+ "&data[]=options"
				+ "&data[]=nodes"
				+ "&data[]=sensorAlerts"
				+ "&sensorAlertsRangeStart=0"
				+ "&sensorAlertsNumber=5"
				+ "&data[]=sensors";
			request.open("GET", url, true);
			request.onreadystatechange = processResponseOverview;
			nextContent = "overview";
			break;
	}

	request.send(null);

	// wait 10 seconds before requesting the next data update
	nextRequest = "requestData(\"" + nextContent + "\")";
	setTimeoutIdRequest = window.setTimeout(nextRequest, 10000);
}


// outputs the "alertLevels" data
function outputAlertLevels() {

	// hide loader and show content
	var loaderObj = document.getElementById("loader");
	loaderObj.className = "elementHidden";
	var contentObj = document.getElementById("content");
	contentObj.className = "elementShown";

	// remove old content output
	// and generate a new clear one
	var contentTableObj = document.getElementById("contentTable");
	var newBody = document.createElement("tbody");
	var oldBody = document.getElementById("contentTableBody");
	oldBody.removeAttribute("id");
	newBody.setAttribute("id", "contentTableBody");
	contentTableObj.replaceChild(newBody, oldBody);
	delete oldBody;

	// get server time
	for(var i = 0; i < internals.length; i++) {
		if(internals[i]["type"].toUpperCase() == "SERVERTIME") {
			serverTime = internals[i]["value"]
		}
	}

	// add header of site
	addMenu(newBody, "alertLevels");

	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	var newB = document.createElement("b");
	newB.textContent = "Alert Levels:";
	newTd.appendChild(newB);
	newTr.appendChild(newTd);
	newBody.appendChild(newTr);

	alertLevels.sort(compareAlertLevelAsc);

	// add all alertLevels to the output
	for(var i = 0; i < alertLevels.length; i++) {

		var alertLevel = alertLevels[i]["alertLevel"];
		var name = alertLevels[i]["name"];
		var triggerAlways = alertLevels[i]["triggerAlways"];
		var smtpActivated = alertLevels[i]["smtpActivated"];
		var toAddr = alertLevels[i]["toAddr"];


		var boxDiv = document.createElement("div");
		boxDiv.className = "box";

		var alertLevelTable = document.createElement("table");
		alertLevelTable.style.width = "100%";
		alertLevelTable.setAttribute("border", "0");
		boxDiv.appendChild(alertLevelTable);


		// add alertLevel to output
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		newTd.textContent = "Alert Level: " + alertLevel;			
		newTd.className = "boxHeaderTd";
		newTr.appendChild(newTd);
		alertLevelTable.appendChild(newTr);


		// add name to the alertLevel
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		var newB = document.createElement("b");
		newB.textContent = "Name:";
		newTd.appendChild(newB);
		newTd.className = "boxEntryTd";
		newTr.appendChild(newTd);
		alertLevelTable.appendChild(newTr);

		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		newTd.textContent = name;
		newTd.className = "neutralTd";
		newTr.appendChild(newTd);
		alertLevelTable.appendChild(newTr);


		// add triggerAlways to the alertLevel
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		var newB = document.createElement("b");
		newB.textContent = "Trigger Always:";
		newTd.appendChild(newB);
		newTd.className = "boxEntryTd";
		newTr.appendChild(newTd);
		alertLevelTable.appendChild(newTr);

		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		if(triggerAlways == 0) {
			newTd.textContent = "false";
		}
		else {
			newTd.textContent = "true";
		}
		newTd.className = "neutralTd";
		newTr.appendChild(newTd);
		alertLevelTable.appendChild(newTr);


		// add email recipient to the alertLevel
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		var newB = document.createElement("b");
		newB.textContent = "eMail Recipient:";
		newTd.appendChild(newB);
		newTd.className = "boxEntryTd";
		newTr.appendChild(newTd);
		alertLevelTable.appendChild(newTr);

		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		if(smtpActivated == 0) {
			newTd.textContent = "none";
		}
		else {
			newTd.textContent = toAddr;
		}
		newTd.className = "neutralTd";
		newTr.appendChild(newTd);
		alertLevelTable.appendChild(newTr);


		// add alertLevel to the content table
		var contentTableObj =
			document.getElementById("contentTableBody");
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		newTd.appendChild(boxDiv);
		newTr.appendChild(newTd);
		contentTableObj.appendChild(newTr);

	}

}


// outputs the "alerts" data
function outputAlerts() {

	// hide loader and show content
	var loaderObj = document.getElementById("loader");
	loaderObj.className = "elementHidden";
	var contentObj = document.getElementById("content");
	contentObj.className = "elementShown";

	// remove old content output
	// and generate a new clear one
	var contentTableObj = document.getElementById("contentTable");
	var newBody = document.createElement("tbody");
	var oldBody = document.getElementById("contentTableBody");
	oldBody.removeAttribute("id");
	newBody.setAttribute("id", "contentTableBody");
	contentTableObj.replaceChild(newBody, oldBody);
	delete oldBody;

	// get server time
	for(var i = 0; i < internals.length; i++) {
		if(internals[i]["type"].toUpperCase() == "SERVERTIME") {
			serverTime = internals[i]["value"]
		}
	}

	// add header of site
	addMenu(newBody, "alerts");

	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	var newB = document.createElement("b");
	newB.textContent = "Clients (Type: Alert):";
	newTd.appendChild(newB);
	newTr.appendChild(newTd);
	newBody.appendChild(newTr);

	nodes.sort(compareNodesAsc);

	// add all nodes to the output
	for(var i = 0; i < nodes.length; i++) {

		var nodeId = nodes[i]["id"];
		var hostname = nodes[i]["hostname"];
		var nodeType = nodes[i]["nodeType"];
		var instance = nodes[i]["instance"];
		var connected = nodes[i]["connected"];
		var version = nodes[i]["version"];
		var rev = nodes[i]["rev"];

		// skip if node is not of type sensor
		if(nodeType.toUpperCase() != "ALERT") {
			continue;
		}

		var boxDiv = document.createElement("div");
		boxDiv.className = "box";

		var nodeTable = document.createElement("table");
		nodeTable.style.width = "100%";
		nodeTable.setAttribute("border", "0");
		boxDiv.appendChild(nodeTable);


		// add id to the node
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		newTd.textContent = "Node: " + nodeId;			
		newTd.className = "boxHeaderTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);


		// add hostname to the node
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		var newB = document.createElement("b");
		newB.textContent = "Hostname:";
		newTd.appendChild(newB);
		newTd.className = "boxEntryTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);

		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		newTd.textContent = hostname;
		newTd.className = "neutralTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);


		// add instance to the node
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		var newB = document.createElement("b");
		newB.textContent = "Instance:";
		newTd.appendChild(newB);
		newTd.className = "boxEntryTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);

		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		newTd.textContent = instance;
		newTd.className = "neutralTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);


		// add connected to the node
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		var newB = document.createElement("b");
		newB.textContent = "Connected:";
		newTd.appendChild(newB);
		newTd.className = "boxEntryTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);

		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		if(connected == 0) {
			newTd.className = "failTd";
			newTd.textContent = "false";
		}
		else {
			newTd.className = "neutralTd";
			newTd.textContent = "true";
		}
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);


		// get an array of alerts that are related to the current node
		var relatedAlerts = [];
		for(j = 0; j < alerts.length; j++) {
			if(alerts[j]["nodeId"] == nodeId) {
				relatedAlerts.push(alerts[j]);
			}
		}

		relatedAlerts.sort(compareAlertsAsc);

		// add all alerts to the node
		for(j = 0; j < relatedAlerts.length; j++) {

			var alertId = relatedAlerts[j]["id"];
			var description = relatedAlerts[j]["description"];
			var relatedAlertLevels = relatedAlerts[j]["alertLevels"];


			// create row for alert output
			var newTr = document.createElement("tr");
			var newTd = document.createElement("td");
			newTr.appendChild(newTd);
			nodeTable.appendChild(newTr);


			// create sub box for alert
			var subBoxDiv = document.createElement("div");
			subBoxDiv.className = "subbox";
			newTd.appendChild(subBoxDiv);


			// create new table for the alert information
			var alertTable = document.createElement("table");
			alertTable.style.width = "100%";
			alertTable.setAttribute("border", "0");
			subBoxDiv.appendChild(alertTable);


			// add id to alert
			var newTr = document.createElement("tr");
			var newTd = document.createElement("td");
			newTd.textContent = "Alert: " + alertId;			
			newTd.className = "boxHeaderTd";
			newTr.appendChild(newTd);
			alertTable.appendChild(newTr);


			// add description to alert
			var newTr = document.createElement("tr");
			var newTd = document.createElement("td");
			var newB = document.createElement("b");
			newB.textContent = "Description:";
			newTd.appendChild(newB);
			newTd.className = "boxEntryTd";
			newTr.appendChild(newTd);
			alertTable.appendChild(newTr);

			var newTr = document.createElement("tr");
			var newTd = document.createElement("td");
			newTd.textContent = description;
			newTd.className = "neutralTd";
			newTr.appendChild(newTd);
			alertTable.appendChild(newTr);

			relatedAlertLevels.sort();

			// output all related alertLevels of this alert
			for(k = 0; k < relatedAlertLevels.length; k++) {
				for(l = 0; l < alertLevels.length; l++) {

					// output alertLevel when found
					if(relatedAlertLevels[k] == 
						alertLevels[l]["alertLevel"]) {

						var alertLevel = relatedAlertLevels[k];
						var name = alertLevels[l]["name"];


						// create row for alertLevel output
						var newTr = document.createElement("tr");
						var newTd = document.createElement("td");
						newTr.appendChild(newTd);
						alertTable.appendChild(newTr);


						// create sub box for alertLevels
						var subSubBoxDiv = document.createElement("div");
						subSubBoxDiv.className = "subbox";
						newTd.appendChild(subSubBoxDiv);


						// create new table for the alertLevel information
						var alertLevelTable =
							document.createElement("table");
						alertLevelTable.style.width = "100%";
						alertLevelTable.setAttribute("border", "0");
						subSubBoxDiv.appendChild(alertLevelTable);


						// add alertLevel
						var newTr = document.createElement("tr");
						var newTd = document.createElement("td");
						newTd.textContent = "Alert Level: " + alertLevel;
						newTd.className = "boxHeaderTd";
						newTr.appendChild(newTd);
						alertLevelTable.appendChild(newTr);


						// add name to alertLevel
						var newTr = document.createElement("tr");
						var newTd = document.createElement("td");
						var newB = document.createElement("b");
						newB.textContent = "Name:";
						newTd.appendChild(newB);
						newTd.className = "boxEntryTd";
						newTr.appendChild(newTd);
						alertLevelTable.appendChild(newTr);

						var newTr = document.createElement("tr");
						var newTd = document.createElement("td");
						newTd.textContent = name;
						newTd.className = "neutralTd";
						newTr.appendChild(newTd);
						alertLevelTable.appendChild(newTr);

						break;

					}

				}

			}

		}


		// add alert to the content table
		var contentTableObj =
			document.getElementById("contentTableBody");
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		newTd.appendChild(boxDiv);
		newTr.appendChild(newTd);
		contentTableObj.appendChild(newTr);

	}
}


// outputs the "events" data
function outputEvents() {

	// hide loader and show content
	var loaderObj = document.getElementById("loader");
	loaderObj.className = "elementHidden";
	var contentObj = document.getElementById("content");
	contentObj.className = "elementShown";

	// remove old content output
	// and generate a new clear one
	var contentTableObj = document.getElementById("contentTable");
	var newBody = document.createElement("tbody");
	var oldBody = document.getElementById("contentTableBody");
	oldBody.removeAttribute("id");
	newBody.setAttribute("id", "contentTableBody");
	contentTableObj.replaceChild(newBody, oldBody);
	delete oldBody;

	// get server time
	for(var i = 0; i < internals.length; i++) {
		if(internals[i]["type"] == "serverTime") {
			serverTime = internals[i]["value"]
		}
	}

	// add header of site
	addMenu(newBody, "events");

	// generate menu for number of shown sensor alerts output
	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	var newB = document.createElement("b");
	newB.textContent = "Number Shown Events:";
	newTd.appendChild(newB);
	newTr.appendChild(newTd);
	newBody.appendChild(newTr);

	var boxDiv = document.createElement("div");
	boxDiv.className = "box";

	var numbersTable = document.createElement("table");
	numbersTable.style.width = "100%";
	numbersTable.setAttribute("border", "0");
	boxDiv.appendChild(numbersTable);

	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	numbersTable.appendChild(newTr);

	// create a temporary table to have the
	// buttons next to each other
	var tempTable = document.createElement("table");
	tempTable.style.width = "100%";
	tempTable.setAttribute("border", "0");
	newTd.appendChild(tempTable);

	var newTr = document.createElement("tr");
	tempTable.appendChild(newTr)

	var newTd = document.createElement("td");
	newTd.style.width = "25%";
	if(eventsNumber == 50) {
		newTd.className = "buttonActiveTd";
	}
	else {
	newTd.className = "buttonTd";
	}
	var newA = document.createElement("a");
	newA.className = "buttonA";
	newA.textContent = "50";
	newA.href = "javascript:void(0)";
	newA.onclick = function(){ changeEventsNumber(50); };
	newTd.appendChild(newA);
	newTr.appendChild(newTd);

	var newTd = document.createElement("td");
	newTd.style.width = "25%";
	if(eventsNumber == 100) {
		newTd.className = "buttonActiveTd";
	}
	else {
		newTd.className = "buttonTd";
	}
	var newA = document.createElement("a");
	newA.className = "buttonA";
	newA.textContent = "100";
	newA.href = "javascript:void(0)";
	newA.onclick = function(){ changeEventsNumber(100); };
	newTd.appendChild(newA);
	newTr.appendChild(newTd);

	var newTd = document.createElement("td");
	newTd.style.width = "25%";
	if(eventsNumber == 200) {
		newTd.className = "buttonActiveTd";
	}
	else {
		newTd.className = "buttonTd";
	}
	var newA = document.createElement("a");
	newA.className = "buttonA";
	newA.textContent = "200";
	newA.href = "javascript:void(0)";
	newA.onclick = function(){ changeEventsNumber(200); };
	newTd.appendChild(newA);
	newTr.appendChild(newTd);

	var newTd = document.createElement("td");
	newTd.style.width = "25%";
	if(eventsNumber == -1) {
		newTd.className = "buttonActiveTd";
	}
	else {
		newTd.className = "buttonTd";
	}
	var newA = document.createElement("a");
	newA.className = "buttonA";
	newA.textContent = "all";
	newA.href = "javascript:void(0)";
	newA.onclick = function(){ changeEventsNumber(-1); };
	newTd.appendChild(newA);
	newTr.appendChild(newTd);

	// add output to the content table
	var contentTableObj =
		document.getElementById("contentTableBody");
	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	newTd.appendChild(boxDiv);
	newTr.appendChild(newTd);
	contentTableObj.appendChild(newTr);


	// generate menu for the filter for type of events that are shown
	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	var newB = document.createElement("b");
	newB.textContent = "Types Shown Filter:";
	newTd.appendChild(newB);
	newTr.appendChild(newTd);
	newBody.appendChild(newTr);

	var boxDiv = document.createElement("div");
	boxDiv.className = "box";

	var typesTable = document.createElement("table");
	typesTable.style.width = "100%";
	typesTable.setAttribute("border", "0");
	boxDiv.appendChild(typesTable);


	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	typesTable.appendChild(newTr);


	// create a form for the filter options
	var newForm = document.createElement("form");
	newForm.setAttribute("action", "#");
	newTd.appendChild(newForm);

	var tempTable = document.createElement("table");
	tempTable.style.width = "100%";
	tempTable.setAttribute("border", "0");
	newForm.appendChild(tempTable);

	// output all filter options
	eventTypes.forEach(function(eventType) {

		newTr = document.createElement("tr");
		newTd = document.createElement("td");
		newTd.setAttribute("id", eventType + "_td");

		var newLabel = document.createElement("label");
		newLabel.className = "filterLabel";
		newLabel.setAttribute("for", eventType + "_id");
		newTd.appendChild(newLabel);

		var newInput = document.createElement("input");
		newInput.setAttribute("type", "checkbox");
		newInput.setAttribute("name", "event_type_filter");
		newInput.setAttribute("value", "1");
		newInput.setAttribute("id", eventType + "_id");

		// check global variable if filter is checked
		if(eventTypesFilter[eventType]) {
			newInput.setAttribute("checked", "");
			newTd.className = "buttonActiveTd";
		}
		else {
			newTd.className = "buttonTd";
		}

		newInput.onchange =
			function(){ changeEventTypesFilter( eventType ); };

		newLabel.appendChild(newInput);
		newLabel.appendChild(document.createTextNode(eventType));

		newTr.appendChild(newTd);
		tempTable.appendChild(newTr);

	});

	// add output to the content table
	var contentTableObj =
		document.getElementById("contentTableBody");
	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	newTd.appendChild(boxDiv);
	newTr.appendChild(newTd);
	contentTableObj.appendChild(newTr);


	// generate events output
	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	var newB = document.createElement("b");
	newB.textContent = "Events:";
	newTd.appendChild(newB);
	newTr.appendChild(newTd);
	newBody.appendChild(newTr);

	events.sort(compareEventsDesc);

	// add all events to the output
	for(var i = 0; i < events.length; i++) {

		var eventId = events[i]["id"];
		var timeOccurred = events[i]["timeOccurred"];
		var type = events[i]["type"];

		// skip if filter disables this type
		if(!eventTypesFilter[type]) {
			continue;
		}

		var boxDiv = document.createElement("div");
		boxDiv.className = "box";

		var eventsTable = document.createElement("table");
		eventsTable.style.width = "100%";
		eventsTable.setAttribute("border", "0");
		boxDiv.appendChild(eventsTable);


		// add id to the event
		newTr = document.createElement("tr");
		newTd = document.createElement("td");
		newTd.textContent = "Event: " + eventId;
		newTd.className = "boxHeaderTd";
		newTr.appendChild(newTd);
		eventsTable.appendChild(newTr);


		// generate date string from timestamp
		localDate = new Date(timeOccurred * 1000);
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


		// add type to the events
		newTr = document.createElement("tr");
		newTd = document.createElement("td");
		newB = document.createElement("b");
		newB.textContent = "Type:";
		newTd.appendChild(newB);
		newTd.className = "boxEntryTd";
		newTr.appendChild(newTd);
		eventsTable.appendChild(newTr);

		newTr = document.createElement("tr");
		newTd = document.createElement("td");
		newTd.textContent = type;
		newTd.className = "neutralTd";
		newTr.appendChild(newTd);
		eventsTable.appendChild(newTr);


		// add time received to the events
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		var newB = document.createElement("b");
		newB.textContent = "Time Occurred:";
		newTd.appendChild(newB);
		newTd.className = "boxEntryTd";
		newTr.appendChild(newTd);
		eventsTable.appendChild(newTr);

		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		newTd.textContent = monthString + "/" + dateString + "/" +
			yearString + " " + hoursString + ":" +
			minutesString + ":" + secondsString;
		newTd.className = "neutralTd";
		newTr.appendChild(newTd);
		eventsTable.appendChild(newTr);
		newTd.className = "neutralTd";
		newTr.appendChild(newTd);
		eventsTable.appendChild(newTr);


		// add output of the specific type to the events
		switch(type) {
			case "changeAlert":
				var oldDescription = events[i]["oldDescription"];
				var newDescription = events[i]["newDescription"];
				addEventChangeAlert(eventsTable, oldDescription,
					newDescription);
				break;

			case "changeManager":
				var oldDescription = events[i]["oldDescription"];
				var newDescription = events[i]["newDescription"];
				addEventChangeManager(eventsTable, oldDescription,
					newDescription);
				break;

			case "changeNode":
				var oldHostname = events[i]["oldHostname"];
				var oldNodeType = events[i]["oldNodeType"];
				var oldInstance = events[i]["oldInstance"];
				var oldVersion = events[i]["oldVersion"];
				var oldRev = events[i]["oldRev"];
				var newHostname = events[i]["newHostname"];
				var newNodeType = events[i]["newNodeType"];
				var newInstance = events[i]["newInstance"];
				var newVersion = events[i]["newVersion"];
				var newRev = events[i]["newRev"];
				addEventChangeNode(eventsTable, oldHostname, oldNodeType,
					oldInstance, oldVersion, oldRev, newHostname,
					newNodeType, newInstance, newVersion, newRev);
				break;

			case "changeOption":
				var optionType = events[i]["optionType"];
				var oldValue = events[i]["oldValue"];
				var newValue = events[i]["newValue"];
				addEventChangeOption(eventsTable, optionType, oldValue,
					newValue);
				break;

			case "changeSensor":
				var oldAlertDelay = events[i]["oldAlertDelay"];
				var oldDescription = events[i]["oldDescription"];
				var newAlertDelay = events[i]["newAlertDelay"];
				var newDescription = events[i]["newDescription"];
				addEventChangeSensor(eventsTable, oldAlertDelay,
					oldDescription, newAlertDelay, newDescription);
				break;

			case "connectedChange":
				var hostname = events[i]["hostname"];
				var nodeType = events[i]["nodeType"];
				var instance = events[i]["instance"];
				var connected = events[i]["connected"];
				addEventConnectedChange(eventsTable, hostname, nodeType,
					instance, connected);
				break;

			case "deleteAlert":
				var description = events[i]["description"];
				addEventDeleteAlert(eventsTable, description);
				break;

			case "deleteManager":
				var description = events[i]["description"];
				addEventDeleteManager(eventsTable, description);
				break;

			case "deleteNode":
				var hostname = events[i]["hostname"];
				var nodeType = events[i]["nodeType"];
				var instance = events[i]["instance"];
				addEventDeleteNode(eventsTable, hostname, nodeType,
					instance);
				break;

			case "deleteSensor":
				var description = events[i]["description"];
				addEventDeleteSensor(eventsTable, description);
				break;

			case "newAlert":
				var hostname = events[i]["hostname"];
				var description = events[i]["description"];
				addEventNewAlert(eventsTable, hostname, description);
				break;

			case "newManager":
				var hostname = events[i]["hostname"];
				var description = events[i]["description"];
				addEventNewManager(eventsTable, hostname, description);
				break;

			case "newNode":
				var hostname = events[i]["hostname"];
				var nodeType = events[i]["nodeType"];
				var instance = events[i]["instance"];
				addEventNewNode(eventsTable, hostname, nodeType, instance);
				break;

			case "newOption":
				var optionType = events[i]["optionType"];
				var value = events[i]["value"];
				addEventNewOption(eventsTable, optionType, value);
				break;

			case "newSensor":
				var hostname = events[i]["hostname"];
				var description = events[i]["description"];
				var state = events[i]["state"];
				addEventNewSensor(eventsTable, hostname, description,
					state);
				break;

			case "newVersion":
				var usedVersion = events[i]["usedVersion"];
				var usedRev = events[i]["usedRev"];
				var newVersion = events[i]["newVersion"];
				var newRev = events[i]["newRev"];
				var instance = events[i]["instance"];
				var hostname = events[i]["hostname"];
				addEventNewVersion(eventsTable, usedVersion, usedRev,
					newVersion, newRev, instance, hostname);
				break;

			case "sensorAlert":
				var description = events[i]["description"];
				var state = events[i]["state"];
				addEventSensorAlert(eventsTable, description, state);
				break;

			case "sensorTimeOut":
				var hostname = events[i]["hostname"];
				var description = events[i]["description"];
				var state = events[i]["state"];
				addEventSensorTimeOut(eventsTable, hostname, description,
					state);
				break;

			case "stateChange":
				var hostname = events[i]["hostname"];
				var description = events[i]["description"];
				var state = events[i]["state"];
				addEventStateChange(eventsTable, hostname, description,
					state)
				break;

			default:
				break;
		}


		// add events to the content table
		contentTableObj =
			document.getElementById("contentTableBody");
		newTr = document.createElement("tr");
		newTd = document.createElement("td");
		newTd.appendChild(boxDiv);
		newTr.appendChild(newTd);
		contentTableObj.appendChild(newTr);

	}

}


// outputs the "managers" data
function outputManagers() {

	// hide loader and show content
	var loaderObj = document.getElementById("loader");
	loaderObj.className = "elementHidden";
	var contentObj = document.getElementById("content");
	contentObj.className = "elementShown";

	// remove old content output
	// and generate a new clear one
	var contentTableObj = document.getElementById("contentTable");
	var newBody = document.createElement("tbody");
	var oldBody = document.getElementById("contentTableBody");
	oldBody.removeAttribute("id");
	newBody.setAttribute("id", "contentTableBody");
	contentTableObj.replaceChild(newBody, oldBody);
	delete oldBody;

	// get server time
	for(var i = 0; i < internals.length; i++) {
		if(internals[i]["type"].toUpperCase() == "SERVERTIME") {
			serverTime = internals[i]["value"]
		}
	}

	// add header of site
	addMenu(newBody, "managers");

	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	var newB = document.createElement("b");
	newB.textContent = "Clients (Type: Manager):";
	newTd.appendChild(newB);
	newTr.appendChild(newTd);
	newBody.appendChild(newTr);

	nodes.sort(compareNodesAsc);

	// add all nodes to the output
	for(var i = 0; i < nodes.length; i++) {

		var nodeId = nodes[i]["id"];
		var hostname = nodes[i]["hostname"];
		var nodeType = nodes[i]["nodeType"];
		var instance = nodes[i]["instance"];
		var connected = nodes[i]["connected"];
		var version = nodes[i]["version"];
		var rev = nodes[i]["rev"];

		// skip if node is not of type manager
		if(nodeType.toUpperCase() != "MANAGER") {
			continue;
		}

		var boxDiv = document.createElement("div");
		boxDiv.className = "box";

		var nodeTable = document.createElement("table");
		nodeTable.style.width = "100%";
		nodeTable.setAttribute("border", "0");
		boxDiv.appendChild(nodeTable);


		// add id to the node
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		newTd.textContent = "Node: " + nodeId;			
		newTd.className = "boxHeaderTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);


		// add hostname to the node
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		var newB = document.createElement("b");
		newB.textContent = "Hostname:";
		newTd.appendChild(newB);
		newTd.className = "boxEntryTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);

		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		newTd.textContent = hostname;
		newTd.className = "neutralTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);


		// add instance to the node
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		var newB = document.createElement("b");
		newB.textContent = "Instance:";
		newTd.appendChild(newB);
		newTd.className = "boxEntryTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);

		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		newTd.textContent = instance;
		newTd.className = "neutralTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);


		// add connected to the node
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		var newB = document.createElement("b");
		newB.textContent = "Connected:";
		newTd.appendChild(newB);
		newTd.className = "boxEntryTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);

		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		if(connected == 0) {
			newTd.className = "failTd";
			newTd.textContent = "false";
		}
		else {
			newTd.className = "neutralTd";
			newTd.textContent = "true";
		}
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);

		nodes.sort(compareManagersAsc);

		// add manager information to the node
		for(j = 0; j < managers.length; j++) {

			if(managers[j]["nodeId"] != nodeId) {
				continue;
			}


			var managerId = managers[j]["id"];
			var description = managers[j]["description"];


			// create row for manager output
			var newTr = document.createElement("tr");
			var newTd = document.createElement("td");
			newTr.appendChild(newTd);
			nodeTable.appendChild(newTr);


			// create sub box for manager
			var subBoxDiv = document.createElement("div");
			subBoxDiv.className = "subbox";
			newTd.appendChild(subBoxDiv);


			// create new table for the manager information
			var managerTable = document.createElement("table");
			managerTable.style.width = "100%";
			managerTable.setAttribute("border", "0");
			subBoxDiv.appendChild(managerTable);


			// add id to manager
			var newTr = document.createElement("tr");
			var newTd = document.createElement("td");
			newTd.textContent = "Manager: " + managerId;			
			newTd.className = "boxHeaderTd";
			newTr.appendChild(newTd);
			managerTable.appendChild(newTr);


			// add description to manager
			var newTr = document.createElement("tr");
			var newTd = document.createElement("td");
			var newB = document.createElement("b");
			newB.textContent = "Description:";
			newTd.appendChild(newB);
			newTd.className = "boxEntryTd";
			newTr.appendChild(newTd);
			managerTable.appendChild(newTr);

			var newTr = document.createElement("tr");
			var newTd = document.createElement("td");
			newTd.textContent = description;
			newTd.className = "neutralTd";
			newTr.appendChild(newTd);
			managerTable.appendChild(newTr);


			break;

		}


		// add manager to the content table
		var contentTableObj =
			document.getElementById("contentTableBody");
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		newTd.appendChild(boxDiv);
		newTr.appendChild(newTd);
		contentTableObj.appendChild(newTr);

	}

}


// outputs the "nodes" data
function outputNodes() {

	// hide loader and show content
	var loaderObj = document.getElementById("loader");
	loaderObj.className = "elementHidden";
	var contentObj = document.getElementById("content");
	contentObj.className = "elementShown";

	// remove old content output
	// and generate a new clear one
	var contentTableObj = document.getElementById("contentTable");
	var newBody = document.createElement("tbody");
	var oldBody = document.getElementById("contentTableBody");
	oldBody.removeAttribute("id");
	newBody.setAttribute("id", "contentTableBody");
	contentTableObj.replaceChild(newBody, oldBody);
	delete oldBody;

	// get server time
	for(var i = 0; i < internals.length; i++) {
		if(internals[i]["type"] == "serverTime") {
			serverTime = internals[i]["value"]
		}
	}

	// add header of site
	addMenu(newBody, "nodes");

	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	var newB = document.createElement("b");
	newB.textContent = "Clients:";
	newTd.appendChild(newB);
	newTr.appendChild(newTd);
	newBody.appendChild(newTr);

	nodes.sort(compareNodesAsc);

	// add all nodes to the output
	for(var i = 0; i < nodes.length; i++) {

		var nodeId = nodes[i]["id"];
		var hostname = nodes[i]["hostname"];
		var nodeType = nodes[i]["nodeType"];
		var instance = nodes[i]["instance"];
		var connected = nodes[i]["connected"];
		var version = nodes[i]["version"];
		var rev = nodes[i]["rev"];
		var newestVersion = nodes[i]["newestVersion"];
		var newestRev = nodes[i]["newestRev"];

		var boxDiv = document.createElement("div");
		boxDiv.className = "box";

		var nodeTable = document.createElement("table");
		nodeTable.style.width = "100%";
		nodeTable.setAttribute("border", "0");
		boxDiv.appendChild(nodeTable);


		// add id to the node
		newTr = document.createElement("tr");
		newTd = document.createElement("td");
		newTd.textContent = "Node: " + nodeId;			
		newTd.className = "boxHeaderTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);


		// add hostname to the node
		newTr = document.createElement("tr");
		newTd = document.createElement("td");
		newB = document.createElement("b");
		newB.textContent = "Hostname:";
		newTd.appendChild(newB);
		newTd.className = "boxEntryTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);

		newTr = document.createElement("tr");
		newTd = document.createElement("td");
		newTd.textContent = hostname;
		newTd.className = "neutralTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);


		// add type to the node
		newTr = document.createElement("tr");
		newTd = document.createElement("td");
		newB = document.createElement("b");
		newB.textContent = "Type:";
		newTd.appendChild(newB);
		newTd.className = "boxEntryTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);

		newTr = document.createElement("tr");
		newTd = document.createElement("td");
		newTd.textContent = nodeType;
		newTd.className = "neutralTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);


		// add instance to the node
		newTr = document.createElement("tr");
		newTd = document.createElement("td");
		newB = document.createElement("b");
		newB.textContent = "Instance:";
		newTd.appendChild(newB);
		newTd.className = "boxEntryTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);

		newTr = document.createElement("tr");
		newTd = document.createElement("td");
		newTd.textContent = instance;
		newTd.className = "neutralTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);


		// add connected to the node
		newTr = document.createElement("tr");
		newTd = document.createElement("td");
		newB = document.createElement("b");
		newB.textContent = "Connected:";
		newTd.appendChild(newB);
		newTd.className = "boxEntryTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);

		newTr = document.createElement("tr");
		newTd = document.createElement("td");
		if(connected == 0) {
			newTd.className = "failTd";
			newTd.textContent = "false";
		}
		else {
			newTd.className = "neutralTd";
			newTd.textContent = "true";
		}
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);


		// add version and revision to the node
		newTr = document.createElement("tr");
		newTd = document.createElement("td");
		newB = document.createElement("b");
		newB.textContent = "Version:";
		newTd.appendChild(newB);
		newTd.className = "boxEntryTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);

		newTr = document.createElement("tr");
		newTd = document.createElement("td");
		if(newestVersion < 0
			|| newestRev < 0) {
			newTd.textContent = version + "-" + rev;
		}
		else {
			newTd.textContent = version + "-" + rev
				+ " (newest: " + newestVersion + "-" + newestRev + ")";
		}
		if(newestVersion > version
			|| (newestRev > rev && newestVersion == version)) {
			newTd.className = "triggeredTd";
		}
		else {
			newTd.className = "neutralTd";
		}
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);


		// add node to the content table
		contentTableObj =
			document.getElementById("contentTableBody");
		newTr = document.createElement("tr");
		newTd = document.createElement("td");
		newTd.appendChild(boxDiv);
		newTr.appendChild(newTd);
		contentTableObj.appendChild(newTr);

	}
}


// outputs the "overview" data
function outputOverview() {

	// hide loader and show content
	var loaderObj = document.getElementById("loader");
	loaderObj.className = "elementHidden";
	var contentObj = document.getElementById("content");
	contentObj.className = "elementShown";

	// remove old content output
	// and generate a new clear one
	var contentTableObj = document.getElementById("contentTable");
	var newBody = document.createElement("tbody");
	var oldBody = document.getElementById("contentTableBody");
	oldBody.removeAttribute("id");
	newBody.setAttribute("id", "contentTableBody");
	contentTableObj.replaceChild(newBody, oldBody);
	delete oldBody;

	// get server time
	for(var i = 0; i < internals.length; i++) {
		if(internals[i]["type"].toUpperCase() == "SERVERTIME") {
			serverTime = internals[i]["value"]
		}
	}

	// add header of site
	addMenu(newBody, "overview");

	// generate sensor alerts overview output
	sensorAlerts.sort(compareSensorAlertsDesc);

	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	var newB = document.createElement("b");
	newB.textContent = "Last Sensor Alerts (Overview):";
	newTd.appendChild(newB);
	newTr.appendChild(newTd);
	newBody.appendChild(newTr);


	var boxDiv = document.createElement("div");
	boxDiv.className = "box";

	var sensorAlertsTable = document.createElement("table");
	sensorAlertsTable.style.width = "100%";
	sensorAlertsTable.setAttribute("border", "0");
	boxDiv.appendChild(sensorAlertsTable);

	// add the last sensor alerts to the output
	for(var i = 0; i < sensorAlerts.length; i++) {

		var timeReceived = sensorAlerts[i]["timeReceived"];
		var state = sensorAlerts[i]["state"];
		var description = sensorAlerts[i]["description"];

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
		timeReceivedString = monthString + "/" + dateString + "/" +
			yearString + " " + hoursString + ":" +
			minutesString + ":" + secondsString;

		// output sensor alert description
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		newTd.appendChild(document.createTextNode(description));
		if(state == 0) {
			newTd.className = "normalTd";
			newTd.appendChild(document.createTextNode(" (normal)"));
		}
		else {
			newTd.className = "triggeredTd";
			newTd.appendChild(document.createTextNode(" (triggered)"));
		}
		newTd.appendChild(document.createElement("br"));
		newTr.appendChild(newTd);
		newTd.appendChild(document.createTextNode(timeReceivedString));
		sensorAlertsTable.appendChild(newTr);
	}

	// add output to the content table
	var contentTableObj =
		document.getElementById("contentTableBody");
	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	newTd.appendChild(boxDiv);
	newTr.appendChild(newTd);
	contentTableObj.appendChild(newTr);


	// generate sensors overview output
	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	var newB = document.createElement("b");
	newB.textContent = "Sensors (Overview):";
	newTd.appendChild(newB);
	newTr.appendChild(newTd);
	newBody.appendChild(newTr);

	var boxDiv = document.createElement("div");
	boxDiv.className = "box";

	var sensorTable = document.createElement("table");
	sensorTable.style.width = "100%";
	sensorTable.setAttribute("border", "0");
	boxDiv.appendChild(sensorTable);

	sensors.sort(compareSensorsAsc);

	// add all sensors to the output
	for(var i = 0; i < sensors.length; i++) {

		var sensorId = sensors[i]["id"];
		var nodeId = sensors[i]["nodeId"];
		var description = sensors[i]["description"];
		var lastStateUpdated = sensors[i]["lastStateUpdated"];
		var state = sensors[i]["state"];
		var connected = 0;

		// get connected information from corresponding node
		for(j = 0; j < nodes.length; j++) {
			if(nodes[j]["id"] == nodeId) {
				var connected = nodes[j]["connected"];
			}
		}

		// output sensor descriptions according to state/connected/updated
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		newTd.appendChild(document.createTextNode(description));

		if(connected == 0) {
			newTd.className = "failTd";
			newTd.appendChild(document.createElement("br"));
			newTd.appendChild(document.createTextNode(" (not connected)"));
		}
		else if(lastStateUpdated < (serverTime - 2* 60)) {
			newTd.className = "failTd";
			newTd.appendChild(document.createElement("br"));
			newTd.appendChild(document.createTextNode(" (timed out)"));
		}
		else {
			if(state == 0) {
				newTd.className = "normalTd";
				newTd.appendChild(document.createElement("br"));
				newTd.appendChild(document.createTextNode("(normal)"));
			}
			else {
				newTd.className = "triggeredTd";
				newTd.appendChild(document.createElement("br"));
				newTd.appendChild(document.createTextNode("(triggered)"));
			}
		}
		newTr.appendChild(newTd);
		sensorTable.appendChild(newTr);

	}

	// add output to the content table
	var contentTableObj =
		document.getElementById("contentTableBody");
	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	newTd.appendChild(boxDiv);
	newTr.appendChild(newTd);
	contentTableObj.appendChild(newTr);

}


// outputs the "sensorAlerts" data
function outputSensorAlerts() {

	// hide loader and show content
	var loaderObj = document.getElementById("loader");
	loaderObj.className = "elementHidden";
	var contentObj = document.getElementById("content");
	contentObj.className = "elementShown";

	// remove old content output
	// and generate a new clear one
	var contentTableObj = document.getElementById("contentTable");
	var newBody = document.createElement("tbody");
	var oldBody = document.getElementById("contentTableBody");
	oldBody.removeAttribute("id");
	newBody.setAttribute("id", "contentTableBody");
	contentTableObj.replaceChild(newBody, oldBody);
	delete oldBody;

	// get server time
	for(var i = 0; i < internals.length; i++) {
		if(internals[i]["type"] == "serverTime") {
			serverTime = internals[i]["value"]
		}
	}

	// add header of site
	addMenu(newBody, "sensorAlerts");

	// generate menu for number of shown sensor alerts output
	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	var newB = document.createElement("b");
	newB.textContent = "Number Shown Sensor Alerts:";
	newTd.appendChild(newB);
	newTr.appendChild(newTd);
	newBody.appendChild(newTr);

	var boxDiv = document.createElement("div");
	boxDiv.className = "box";

	var numbersTable = document.createElement("table");
	numbersTable.style.width = "100%";
	numbersTable.setAttribute("border", "0");
	boxDiv.appendChild(numbersTable);

	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	numbersTable.appendChild(newTr);

	// create a temporary table to have the
	// buttons next to each other
	var tempTable = document.createElement("table");
	tempTable.style.width = "100%";
	tempTable.setAttribute("border", "0");
	newTd.appendChild(tempTable);

	var newTr = document.createElement("tr");
	tempTable.appendChild(newTr)

	var newTd = document.createElement("td");
	newTd.style.width = "25%";
	if(sensorAlertsNumber == 50) {
		newTd.className = "buttonActiveTd";
	}
	else {
		newTd.className = "buttonTd";
	}
	var newA = document.createElement("a");
	newA.className = "buttonA";
	newA.textContent = "50";
	newA.href = "javascript:void(0)";
	newA.onclick = function(){ changeSensorAlertsNumber(50); };
	newTd.appendChild(newA);
	newTr.appendChild(newTd);

	var newTd = document.createElement("td");
	newTd.style.width = "25%";
	if(sensorAlertsNumber == 100) {
		newTd.className = "buttonActiveTd";
	}
	else {
		newTd.className = "buttonTd";
	}
	var newA = document.createElement("a");
	newA.className = "buttonA";
	newA.textContent = "100";
	newA.href = "javascript:void(0)";
	newA.onclick = function(){ changeSensorAlertsNumber(100); };
	newTd.appendChild(newA);
	newTr.appendChild(newTd);

	var newTd = document.createElement("td");
	newTd.style.width = "25%";
	if(sensorAlertsNumber == 200) {
		newTd.className = "buttonActiveTd";
	}
	else {
		newTd.className = "buttonTd";
	}
	var newA = document.createElement("a");
	newA.className = "buttonA";
	newA.textContent = "200";
	newA.href = "javascript:void(0)";
	newA.onclick = function(){ changeSensorAlertsNumber(200); };
	newTd.appendChild(newA);
	newTr.appendChild(newTd);

	var newTd = document.createElement("td");
	newTd.style.width = "25%";
	if(sensorAlertsNumber == -1) {
		newTd.className = "buttonActiveTd";
	}
	else {
		newTd.className = "buttonTd";
	}
	var newA = document.createElement("a");
	newA.className = "buttonA";
	newA.textContent = "all";
	newA.href = "javascript:void(0)";
	newA.onclick = function(){ changeSensorAlertsNumber(-1); };
	newTd.appendChild(newA);
	newTr.appendChild(newTd);


	// add output to the content table
	var contentTableObj =
		document.getElementById("contentTableBody");
	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	newTd.appendChild(boxDiv);
	newTr.appendChild(newTd);
	contentTableObj.appendChild(newTr);


	// generate sensor alerts output
	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	var newB = document.createElement("b");
	newB.textContent = "Sensor Alerts:";
	newTd.appendChild(newB);
	newTr.appendChild(newTd);
	newBody.appendChild(newTr);

	sensorAlerts.sort(compareSensorAlertsDesc);

	// add all sensor alerts to the output
	for(var i = 0; i < sensorAlerts.length; i++) {

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
			newTd.className = "triggeredTd";
			newTd.textContent = "triggered";
		}
		else {
			newTd.className = "normalTd";
			newTd.textContent = "normal";
		}
		newTr.appendChild(newTd);
		sensorAlertTable.appendChild(newTr);


		// add time received to the sensor alert
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		var newB = document.createElement("b");
		newB.textContent = "Time Received:";
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


		// add sensor alert to the content table
		contentTableObj =
			document.getElementById("contentTableBody");
		newTr = document.createElement("tr");
		newTd = document.createElement("td");
		newTd.appendChild(boxDiv);
		newTr.appendChild(newTd);
		contentTableObj.appendChild(newTr);

	}
}


// outputs the "sensors" data
function outputSensors() {

	// hide loader and show content
	var loaderObj = document.getElementById("loader");
	loaderObj.className = "elementHidden";
	var contentObj = document.getElementById("content");
	contentObj.className = "elementShown";

	// remove old content output
	// and generate a new clear one
	var contentTableObj = document.getElementById("contentTable");
	var newBody = document.createElement("tbody");
	var oldBody = document.getElementById("contentTableBody");
	oldBody.removeAttribute("id");
	newBody.setAttribute("id", "contentTableBody");
	contentTableObj.replaceChild(newBody, oldBody);
	delete oldBody;

	// get server time
	for(var i = 0; i < internals.length; i++) {
		if(internals[i]["type"].toUpperCase() == "SERVERTIME") {
			serverTime = internals[i]["value"]
		}
	}

	// add header of site
	addMenu(newBody, "sensors");

	var newTr = document.createElement("tr");
	var newTd = document.createElement("td");
	var newB = document.createElement("b");
	newB.textContent = "Clients (Type: Sensor):";
	newTd.appendChild(newB);
	newTr.appendChild(newTd);
	newBody.appendChild(newTr);

	nodes.sort(compareNodesAsc);

	// add all nodes to the output
	for(var i = 0; i < nodes.length; i++) {

		var nodeId = nodes[i]["id"];
		var hostname = nodes[i]["hostname"];
		var nodeType = nodes[i]["nodeType"];
		var instance = nodes[i]["instance"];
		var connected = nodes[i]["connected"];
		var version = nodes[i]["version"];
		var rev = nodes[i]["rev"];

		// skip if node is not of type sensor
		if(nodeType.toUpperCase() != "SENSOR") {
			continue;
		}

		var boxDiv = document.createElement("div");
		boxDiv.className = "box";

		var nodeTable = document.createElement("table");
		nodeTable.style.width = "100%";
		nodeTable.setAttribute("border", "0");
		boxDiv.appendChild(nodeTable);


		// add id to the node
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		newTd.textContent = "Node: " + nodeId;			
		newTd.className = "boxHeaderTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);


		// add hostname to the node
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		var newB = document.createElement("b");
		newB.textContent = "Hostname:";
		newTd.appendChild(newB);
		newTd.className = "boxEntryTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);

		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		newTd.textContent = hostname;
		newTd.className = "neutralTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);


		// add instance to the node
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		var newB = document.createElement("b");
		newB.textContent = "Instance:";
		newTd.appendChild(newB);
		newTd.className = "boxEntryTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);

		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		newTd.textContent = instance;
		newTd.className = "neutralTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);


		// add connected to the node
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		var newB = document.createElement("b");
		newB.textContent = "Connected:";
		newTd.appendChild(newB);
		newTd.className = "boxEntryTd";
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);

		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		if(connected == 0) {
			newTd.className = "failTd";
			newTd.textContent = "false";
		}
		else {
			newTd.className = "neutralTd";
			newTd.textContent = "true";
		}
		newTr.appendChild(newTd);
		nodeTable.appendChild(newTr);


		// get an array of sensors that are related to the current node
		var relatedSensors = [];
		for(j = 0; j < sensors.length; j++) {
			if(sensors[j]["nodeId"] == nodeId) {
				relatedSensors.push(sensors[j]);
			}
		}

		relatedSensors.sort(compareSensorsAsc);

		// add all sensors to the node
		for(j = 0; j < relatedSensors.length; j++) {

			var sensorId = relatedSensors[j]["id"];
			var description = relatedSensors[j]["description"];
			var lastStateUpdated = relatedSensors[j]["lastStateUpdated"];
			var state = relatedSensors[j]["state"];
			var relatedAlertLevels = relatedSensors[j]["alertLevels"];


			// create row for sensor output
			var newTr = document.createElement("tr");
			var newTd = document.createElement("td");
			newTr.appendChild(newTd);
			nodeTable.appendChild(newTr);


			// create sub box for sensor
			var subBoxDiv = document.createElement("div");
			subBoxDiv.className = "subbox";
			newTd.appendChild(subBoxDiv);


			// create new table for the sensor information
			var sensorTable = document.createElement("table");
			sensorTable.style.width = "100%";
			sensorTable.setAttribute("border", "0");
			subBoxDiv.appendChild(sensorTable);


			// add id to sensor
			var newTr = document.createElement("tr");
			var newTd = document.createElement("td");
			newTd.textContent = "Sensor: " + sensorId;			
			newTd.className = "boxHeaderTd";
			newTr.appendChild(newTd);
			sensorTable.appendChild(newTr);


			// add description to sensor
			var newTr = document.createElement("tr");
			var newTd = document.createElement("td");
			var newB = document.createElement("b");
			newB.textContent = "Description:";
			newTd.appendChild(newB);
			newTd.className = "boxEntryTd";
			newTr.appendChild(newTd);
			sensorTable.appendChild(newTr);

			var newTr = document.createElement("tr");
			var newTd = document.createElement("td");
			newTd.textContent = description;
			newTd.className = "neutralTd";
			newTr.appendChild(newTd);
			sensorTable.appendChild(newTr);


			// add state to sensor
			var newTr = document.createElement("tr");
			var newTd = document.createElement("td");
			var newB = document.createElement("b");
			newB.textContent = "State:";
			newTd.appendChild(newB);
			newTd.className = "boxEntryTd";
			newTr.appendChild(newTd);
			sensorTable.appendChild(newTr);

			var newTr = document.createElement("tr");
			var newTd = document.createElement("td"); 
			if(state == 1) {
				newTd.className = "triggeredTd";
				newTd.textContent = "triggered";
			}
			else {
				newTd.className = "normalTd";
				newTd.textContent = "normal";
			}
			newTr.appendChild(newTd);
			sensorTable.appendChild(newTr);


			// generate date string from timestamp
			localDate = new Date(lastStateUpdated * 1000);
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
			var newTr = document.createElement("tr");
			var newTd = document.createElement("td");
			var newB = document.createElement("b");
			newB.textContent = "Last Updated:";
			newTd.appendChild(newB);
			newTd.className = "boxEntryTd";
			newTr.appendChild(newTd);
			sensorTable.appendChild(newTr);

			var newTr = document.createElement("tr");
			var newTd = document.createElement("td");
			newTd.textContent = monthString + "/" + dateString + "/" +
				yearString + " " + hoursString + ":" +
				minutesString + ":" + secondsString;
			newTd.className = "neutralTd";
			newTr.appendChild(newTd);
			sensorTable.appendChild(newTr);
			// set color to red if the sensor has timed out
			if(lastStateUpdated < (serverTime - 2* 60)) {
				newTd.className = "failTd";
			}
			else {
				newTd.className = "neutralTd";
			}
			newTr.appendChild(newTd);
			sensorTable.appendChild(newTr);

			relatedAlertLevels.sort();

			// output all related alertLevels of this sensor
			for(k = 0; k < relatedAlertLevels.length; k++) {
				for(l = 0; l < alertLevels.length; l++) {

					// output alertLevel when found
					if(relatedAlertLevels[k] == 
						alertLevels[l]["alertLevel"]) {

						var alertLevel = relatedAlertLevels[k];
						var name = alertLevels[l]["name"];


						// create row for alertLevel output
						var newTr = document.createElement("tr");
						var newTd = document.createElement("td");
						newTr.appendChild(newTd);
						sensorTable.appendChild(newTr);


						// create sub box for alertLevels
						var subSubBoxDiv = document.createElement("div");
						subSubBoxDiv.className = "subbox";
						newTd.appendChild(subSubBoxDiv);


						// create new table for the alertLevel information
						var alertLevelTable =
							document.createElement("table");
						alertLevelTable.style.width = "100%";
						alertLevelTable.setAttribute("border", "0");
						subSubBoxDiv.appendChild(alertLevelTable);


						// add alertLevel
						var newTr = document.createElement("tr");
						var newTd = document.createElement("td");
						newTd.textContent = "Alert Level: " + alertLevel;
						newTd.className = "boxHeaderTd";
						newTr.appendChild(newTd);
						alertLevelTable.appendChild(newTr);


						// add name to alertLevel
						var newTr = document.createElement("tr");
						var newTd = document.createElement("td");
						var newB = document.createElement("b");
						newB.textContent = "Name:";
						newTd.appendChild(newB);
						newTd.className = "boxEntryTd";
						newTr.appendChild(newTd);
						alertLevelTable.appendChild(newTr);

						var newTr = document.createElement("tr");
						var newTd = document.createElement("td");
						newTd.textContent = name;
						newTd.className = "neutralTd";
						newTr.appendChild(newTd);
						alertLevelTable.appendChild(newTr);

						break;

					}
				}		
			}
		}


		// add sensors to the content table
		var contentTableObj =
			document.getElementById("contentTableBody");
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		newTd.appendChild(boxDiv);
		newTr.appendChild(newTd);
		contentTableObj.appendChild(newTr);

	}
}


changeOutput("overview");