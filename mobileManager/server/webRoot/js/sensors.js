// set global configuration variables
var request = new XMLHttpRequest();


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
			if(internals[i]["type"] == "serverTime") {
				var serverTime = internals[i]["value"]
			}
		}


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






			// add all sensors to the node
			for(j = 0; j < relatedSensors.length; j++) {

				var sensorId = relatedSensors[j]["id"];
				var description = relatedSensors[j]["description"];
				var lastStateUpdated = relatedSensors[j]["lastStateUpdated"];
				var state = relatedSensors[j]["state"];






				var newTr = document.createElement("tr");
				var newTd = document.createElement("td");
				newTr.appendChild(newTd);
				nodeTable.appendChild(newTr);


				var subBoxDiv = document.createElement("div");
				subBoxDiv.className = "box";
				newTd.appendChild(subBoxDiv);

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
				newTd.textContent = state; // TODO should be yellow if triggered
				newTd.className = "neutralTd";
				newTr.appendChild(newTd);
				sensorTable.appendChild(newTr);






				HIER WEITER





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