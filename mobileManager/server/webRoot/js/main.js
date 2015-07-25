// set global configuration variables
var request = new XMLHttpRequest();
var setTimeoutId = null;


// simple function to ask for confirmation if the alert system
// should be activated
function confirmation(activate) {

	if(activate == 1) {
		result = confirm("Do you really want to activate the alert system?");
		if(result) {
			window.location = "index.php?activate=1";
		}
	}
	else if(activate == 0) {
		result = confirm("Do you really want to deactivate " + 
			"the alert system?");
		if(result) {
			window.location = "index.php?activate=0";
		}
	}
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


// adds a menu for the navigation to the given table body
function addMenu(newBody, current) {

		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		var newB = document.createElement("b");
		newB.textContent = "Menu:";
		newTd.appendChild(newB);
		newTr.appendChild(newTd);
		newBody.appendChild(newTr);

		var boxDiv = document.createElement("div");
		boxDiv.className = "box";

		var menuTable = document.createElement("table");
		menuTable.style.width = "100%";
		menuTable.setAttribute("border", "0");
		boxDiv.appendChild(menuTable);

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
		newA.onclick = function(){ requestData("alertLevels"); };
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
		newA.onclick = function(){ requestData("nodes"); };
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
		newA.onclick = function(){ requestData("alerts"); };
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
		newA.onclick = function(){ requestData("managers"); };
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
		newA.onclick = function(){ requestData("sensors"); };
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
		newA.onclick = function(){ requestData("overview"); };
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
		newA.onclick = function(){ requestData("sensorAlerts"); };
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


// processes the response of the server for the
// requested "alert levels" data
function processResponseAlertLevels() {
	
	if (request.readyState == 4) {

		// remove old content output
		// and generate a new clear one
		var contentTableObj = document.getElementById("contentTable");
		var newBody = document.createElement("tbody");
		var oldBody = document.getElementById("contentTableBody");
		oldBody.removeAttribute("id");
		newBody.setAttribute("id", "contentTableBody");
		contentTableObj.replaceChild(newBody, oldBody);
		delete oldBody;

		// get JSON response and parse it
		var response = request.responseText;
		var alertSystemInformation = JSON.parse(response);
		var internals = alertSystemInformation["internals"];
		var alertLevels = alertSystemInformation["alertLevels"];

		// get server time
		var serverTime = 0.0;
		for(i = 0; i < internals.length; i++) {
			if(internals[i]["type"].toUpperCase() == "SERVERTIME") {
				var serverTime = internals[i]["value"]
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
		for(i = 0; i < alertLevels.length; i++) {

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





			// TODO







			// add triggerAlways to the alertLevel
			var newTr = document.createElement("tr");
			var newTd = document.createElement("td");
			var newB = document.createElement("b");
			newB.textContent = "Trigger always:";
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
			newB.textContent = "eMail recipient:";
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
}


// processes the response of the server for the
// requested "alerts" data
function processResponseAlerts() {
	
	if (request.readyState == 4) {

		// remove old content output
		// and generate a new clear one
		var contentTableObj = document.getElementById("contentTable");
		var newBody = document.createElement("tbody");
		var oldBody = document.getElementById("contentTableBody");
		oldBody.removeAttribute("id");
		newBody.setAttribute("id", "contentTableBody");
		contentTableObj.replaceChild(newBody, oldBody);
		delete oldBody;

		// get JSON response and parse it
		var response = request.responseText;
		var alertSystemInformation = JSON.parse(response);
		var internals = alertSystemInformation["internals"];
		var nodes = alertSystemInformation["nodes"];
		var alerts = alertSystemInformation["alerts"];
		var alertLevels = alertSystemInformation["alertLevels"];

		// get server time
		var serverTime = 0.0;
		for(i = 0; i < internals.length; i++) {
			if(internals[i]["type"].toUpperCase() == "SERVERTIME") {
				var serverTime = internals[i]["value"]
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
		for(i = 0; i < nodes.length; i++) {

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
}


// processes the response of the server for the
// requested "managers" data
function processResponseManagers() {
	
	if (request.readyState == 4) {

		// remove old content output
		// and generate a new clear one
		var contentTableObj = document.getElementById("contentTable");
		var newBody = document.createElement("tbody");
		var oldBody = document.getElementById("contentTableBody");
		oldBody.removeAttribute("id");
		newBody.setAttribute("id", "contentTableBody");
		contentTableObj.replaceChild(newBody, oldBody);
		delete oldBody;

		// get JSON response and parse it
		var response = request.responseText;
		var alertSystemInformation = JSON.parse(response);
		var internals = alertSystemInformation["internals"];
		var nodes = alertSystemInformation["nodes"];
		var managers = alertSystemInformation["managers"];

		// get server time
		var serverTime = 0.0;
		for(i = 0; i < internals.length; i++) {
			if(internals[i]["type"].toUpperCase() == "SERVERTIME") {
				var serverTime = internals[i]["value"]
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
		for(i = 0; i < nodes.length; i++) {

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
}


// processes the response of the server for the
// requested "nodes" data
function processResponseNodes() {

	if (request.readyState == 4) {

		// remove old content output
		// and generate a new clear one
		var contentTableObj = document.getElementById("contentTable");
		var newBody = document.createElement("tbody");
		var oldBody = document.getElementById("contentTableBody");
		oldBody.removeAttribute("id");
		newBody.setAttribute("id", "contentTableBody");
		contentTableObj.replaceChild(newBody, oldBody);
		delete oldBody;

		// get JSON response and parse it
		var response = request.responseText;
		var alertSystemInformation = JSON.parse(response);
		var internals = alertSystemInformation["internals"];
		var nodes = alertSystemInformation["nodes"];

		// get server time
		var serverTime = 0.0;
		for(i = 0; i < internals.length; i++) {
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
		for(i = 0; i < nodes.length; i++) {

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
				newTd.className = "failTd";
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
}


// processes the response of the server for the
// requested "overview" data
function processResponseOverview() {
	
	if (request.readyState == 4) {

		// remove old content output
		// and generate a new clear one
		var contentTableObj = document.getElementById("contentTable");
		var newBody = document.createElement("tbody");
		var oldBody = document.getElementById("contentTableBody");
		oldBody.removeAttribute("id");
		newBody.setAttribute("id", "contentTableBody");
		contentTableObj.replaceChild(newBody, oldBody);
		delete oldBody;

		// get JSON response and parse it
		var response = request.responseText;
		var alertSystemInformation = JSON.parse(response);
		var internals = alertSystemInformation["internals"];
		var options = alertSystemInformation["options"];
		var nodes = alertSystemInformation["nodes"];
		var sensors = alertSystemInformation["sensors"];
		var sensorAlerts = alertSystemInformation["sensorAlerts"];


		// get server time
		var serverTime = 0.0;
		for(i = 0; i < internals.length; i++) {
			if(internals[i]["type"].toUpperCase() == "SERVERTIME") {
				var serverTime = internals[i]["value"]
			}
		}

		// add header of site
		addMenu(newBody, "overview");


		// generate alert system overview output
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		var newB = document.createElement("b");
		newB.textContent = "Alert System:";
		newTd.appendChild(newB);
		newTr.appendChild(newTd);
		newBody.appendChild(newTr);

		var boxDiv = document.createElement("div");
		boxDiv.className = "box";

		var optionsTable = document.createElement("table");
		optionsTable.style.width = "100%";
		optionsTable.setAttribute("border", "0");
		boxDiv.appendChild(optionsTable);


		// process options of the alert system
		for(i = 0; i < options.length; i++) {

			// only evaluate "alertSystemActive"
			if(options[i]["type"].toUpperCase() == "ALERTSYSTEMACTIVE") {

				// add status of alert system
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
				optionsTable.appendChild(newTr);

				var newTr = document.createElement("tr");
				var newTd = document.createElement("td");
				newTd.className = "neutralTd";
				newTr.appendChild(newTd);
				optionsTable.appendChild(newTr);


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

				break;
			}
		}

		// add output to the content table
		var contentTableObj =
			document.getElementById("contentTableBody");
		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		newTd.appendChild(boxDiv);
		newTr.appendChild(newTd);
		contentTableObj.appendChild(newTr);


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
		for(i = 0; i < 5; i++) {

			// skip if there are no sensor alerts left
			if(i >= sensorAlerts.length) {
				break;
			}

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
				newTd.appendChild(document.createTextNode(" (normal)"));
				newTd.className = "okTd";
			}
			else {
				newTd.appendChild(document.createTextNode(" (triggered)"));
				newTd.className = "triggeredTd";
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


		// add all sensors to the output
		for(i = 0; i < sensors.length; i++) {

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
			newTd.textContent = description;
			if(state == 0) {
				newTd.className = "okTd";
			}
			else {
				newTd.className = "triggeredTd";
			}
			if(lastStateUpdated < (serverTime - 2* 60)) {
				newTd.className = "failTd";
			}
			if(connected == 0) {
				newTd.className = "failTd";
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
}


// processes the response of the server for the
// requested "sensor alerts" data
function processResponseSensorAlerts() {

	if (request.readyState == 4) {

		// remove old content output
		// and generate a new clear one
		var contentTableObj = document.getElementById("contentTable");
		var newBody = document.createElement("tbody");
		var oldBody = document.getElementById("contentTableBody");
		oldBody.removeAttribute("id");
		newBody.setAttribute("id", "contentTableBody");
		contentTableObj.replaceChild(newBody, oldBody);
		delete oldBody;

		// get JSON response and parse it
		var response = request.responseText;
		var alertSystemInformation = JSON.parse(response);
		var internals = alertSystemInformation["internals"];
		var sensorAlerts = alertSystemInformation["sensorAlerts"];

		// get server time
		var serverTime = 0.0;
		for(i = 0; i < internals.length; i++) {
			if(internals[i]["type"] == "serverTime") {
				serverTime = internals[i]["value"]
			}
		}

		// add header of site
		addMenu(newBody, "sensorAlerts");


		var newTr = document.createElement("tr");
		var newTd = document.createElement("td");
		var newB = document.createElement("b");
		newB.textContent = "Sensor Alerts:";
		newTd.appendChild(newB);
		newTr.appendChild(newTd);
		newBody.appendChild(newTr);

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
}


// processes the response of the server for the
// requested "sensors" data
function processResponseSensors() {
	
	if (request.readyState == 4) {

		// remove old content output
		// and generate a new clear one
		var contentTableObj = document.getElementById("contentTable");
		var newBody = document.createElement("tbody");
		var oldBody = document.getElementById("contentTableBody");
		oldBody.removeAttribute("id");
		newBody.setAttribute("id", "contentTableBody");
		contentTableObj.replaceChild(newBody, oldBody);
		delete oldBody;

		// get JSON response and parse it
		var response = request.responseText;
		var alertSystemInformation = JSON.parse(response);
		var internals = alertSystemInformation["internals"];
		var nodes = alertSystemInformation["nodes"];
		var sensors = alertSystemInformation["sensors"];
		var alertLevels = alertSystemInformation["alertLevels"];

		// get server time
		var serverTime = 0.0;
		for(i = 0; i < internals.length; i++) {
			if(internals[i]["type"].toUpperCase() == "SERVERTIME") {
				var serverTime = internals[i]["value"]
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
		for(i = 0; i < nodes.length; i++) {

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
				newTd.textContent = state;
				if(state == 1) {
					newTd.className = "triggeredTd";
				}
				else {
					newTd.className = "neutralTd";
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
				newB.textContent = "Last updated:";
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
}


// requests the data of the alert system
function requestData(content) {

	// clear timeout if it is set
	if(setTimeoutId != null) {
		window.clearTimeout(setTimeoutId);
	}
	var nextContent = null;

	switch(content) {
		case "alertLevels":
			var url = "./getJson.php"
				+ "?data[]=internals"
				+ "&data[]=alertlevels";
			request.open("GET", url, true);
			request.onreadystatechange = processResponseAlertLevels;
			nextContent = content;
			break;
		case "alerts":
			var url = "./getJson.php"
				+ "?data[]=internals"
				+ "&data[]=nodes"
				+ "&data[]=alerts"
				+ "&data[]=alertlevels";
			request.open("GET", url, true);
			request.onreadystatechange = processResponseAlerts;
			nextContent = content;
			break;
		case "managers":
			var url = "./getJson.php"
				+ "?data[]=internals"
				+ "&data[]=nodes"
				+ "&data[]=managers";
			request.open("GET", url, true);
			request.onreadystatechange = processResponseManagers;
			nextContent = content;
			break;
		case "nodes":
			var url = "./getJson.php"
				+ "?data[]=internals"
				+ "&data[]=nodes";
			request.open("GET", url, true);
			request.onreadystatechange = processResponseNodes;
			nextContent = content;
			break;
		case "sensorAlerts":
			var url = "./getJson.php"
				+ "?data[]=internals"
				+ "&data[]=sensorAlerts";
			request.open("GET", url, true);
			request.onreadystatechange = processResponseSensorAlerts;
			nextContent = content;
			break;
		case "sensors":
			var url = "./getJson.php"
				+ "?data[]=internals"
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
				+ "&data[]=sensors";
			request.open("GET", url, true);
			request.onreadystatechange = processResponseOverview;
			nextContent = "overview";
			break;
	}

	request.send(null);

	// wait 10 seconds before requesting the next data update
	nextRequest = "requestData(\"" + nextContent + "\")";
	setTimeoutId = window.setTimeout(nextRequest, 10000);
}


requestData("overview");