// set global configuration variables
var request = new XMLHttpRequest();


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


// processes the response of the server for the
// requested data
function processResponse() {
	
	if (request.readyState == 4) {

		// remove old nodes output
		// and generate a new clear one
		var alertLevelTableObj = document.getElementById("contentTable");
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
		alertLevelTableObj.replaceChild(newBody, oldBody);
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





			// add alertLevel to the alertLevel table
			var alertLevelTableObj =
				document.getElementById("contentTableBody");
			var newTr = document.createElement("tr");
			var newTd = document.createElement("td");
			newTd.appendChild(boxDiv);
			newTr.appendChild(newTd);
			alertLevelTableObj.appendChild(newTr);

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