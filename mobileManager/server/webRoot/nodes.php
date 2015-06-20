<html>
	<head>

		<title>alertR mobile manager</title>

		<link rel="stylesheet" href="css/style.css" />

	</head>

	<body>

		<p><b>alertR mobile manager</b></p>

		<table border="0" width="300" id="nodesTable">
			<tbody id="nodesTableBody">
			</tbody>
		</table>

		<script>

			// set global configuration variables
			var request = new XMLHttpRequest();


			// processes the response of the server for the
			// requested data
			function processResponse() {
				if (request.readyState == 4) {


					// remove old nodes output
					// and generate a new clear one
					nodeTableObj = document.getElementById("nodesTable");
					newBody = document.createElement("tbody");
					newTr = document.createElement("tr");
					newTd = document.createElement("td");
					newB = document.createElement("b");
					newB.textContent = "Nodes:";
					newTd.appendChild(newB);
					newTr.appendChild(newTd);
					newBody.appendChild(newTr);
					oldBody = document.getElementById("nodesTableBody");
					oldBody.removeAttribute("id");
					newBody.setAttribute("id", "nodesTableBody");
					nodeTableObj.replaceChild(newBody, oldBody);
					delete oldBody;

					// get JSON response and parse it
					response = request.responseText;
					alertSystemInformation = JSON.parse(response);
					internals = alertSystemInformation["internals"];
					nodes = alertSystemInformation["nodes"];

					// get server time
					serverTime = 0.0;
					for(i = 0; i < internals.length; i++) {
						if(internals[i]["type"] == "serverTime") {
							serverTime = internals[i]["value"]
						}
					}


					// add all nodes to the output
					for(i = 0; i < nodes.length; i++) {

						nodeId = nodes[i]["id"];
						hostname = nodes[i]["hostname"];
						nodeType = nodes[i]["nodeType"];
						instance = nodes[i]["instance"];
						connected = nodes[i]["connected"];
						version = nodes[i]["version"];
						rev = nodes[i]["rev"];

						boxDiv = document.createElement("div");
						boxDiv.className = "box";

						nodeTable = document.createElement("table");
						nodeTable.style.width = "100%";
						nodeTable.setAttribute("border", "0");
						boxDiv.appendChild(nodeTable);


						// add hostname to the node
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
						newTd.textContent = version + "-" + rev;
						newTd.className = "neutralTd";
						newTr.appendChild(newTd);
						nodeTable.appendChild(newTr);


						// add node to the node table
						nodeTableObj =
							document.getElementById("nodesTableBody");
						newTr = document.createElement("tr");
						newTd = document.createElement("td");
						newTd.appendChild(boxDiv);
						newTr.appendChild(newTd);
						nodeTableObj.appendChild(newTr);

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