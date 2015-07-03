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