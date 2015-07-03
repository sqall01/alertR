// set global configuration variables
var request = new XMLHttpRequest();


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

		// get server time
		var serverTime = 0.0;
		for(i = 0; i < internals.length; i++) {
			if(internals[i]["type"].toUpperCase() == "SERVERTIME") {
				var serverTime = internals[i]["value"]
			}
		}

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


			// add node to the node table
			var nodeTableObj =
				document.getElementById("contentTableBody");
			var newTr = document.createElement("tr");
			var newTd = document.createElement("td");
			newTd.appendChild(boxDiv);
			newTr.appendChild(newTd);
			nodeTableObj.appendChild(newTr);

		}
	}
}


// requests the data of the alert system
function requestData() {
	var url = "./getJson.php";
	request.open("GET", url, true);
	request.onreadystatechange = processResponse;
	request.send(null);

	// wait 10 seconds before requesting the next data update
	window.setTimeout("requestData()", 10000);	
}

requestData();