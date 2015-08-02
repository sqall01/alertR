function addEventChangeAlert(eventsTable, oldDescription, newDescription) {

	// add old description to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Old Description:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = oldDescription;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add new description to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "New Description:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	if(oldDescription != newDescription) {
		newTd.className = "triggeredTd";
	}
	else {
		newTd.className = "neutralTd";
	}
	newTd.textContent = newDescription;
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

}


function addEventChangeManager(eventsTable, oldDescription, newDescription) {

	// add old description to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Old Description:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = oldDescription;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add new description to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "New Description:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	if(oldDescription != newDescription) {
		newTd.className = "triggeredTd";
	}
	else {
		newTd.className = "neutralTd";
	}
	newTd.textContent = newDescription;
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

}


function addEventChangeOption(eventsTable, optionType, oldValue, newValue) {

	// add option type to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Option Type:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = optionType;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add old value to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Old Value:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	if(optionType == "alertSystemActive") {
		if(oldValue == 1) {
			newTd.className = "activatedTd";
			newTd.textContent = "activated"
		}
		else {
			newTd.className = "deactivatedTd";
			newTd.textContent = "deactivated"
		}
	}
	else {
		newTd.className = "neutralTd";
		newTd.textContent = oldValue;
	}
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add new value to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "New Value:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	if(optionType == "alertSystemActive") {
		if(newValue == 1) {
			newTd.className = "activatedTd";
			newTd.textContent = "activated"
		}
		else {
			newTd.className = "deactivatedTd";
			newTd.textContent = "deactivated"
		}
	}
	else {
		newTd.className = "neutralTd";
		newTd.textContent = newValue;
	}
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

}


function addEventChangeNode(eventsTable, oldHostname, oldNodeType,
	oldInstance, oldVersion, oldRev, newHostname, newNodeType, newInstance,
	newVersion, newRev) {

	// add old hostname to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Old Hostname:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = oldHostname;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add new hostname to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "New Hostname:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	if(oldHostname != newHostname) {
		newTd.className = "triggeredTd";
	}
	else {
		newTd.className = "neutralTd";
	}
	newTd.textContent = newHostname;
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add old node type to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Old Node Type:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = oldNodeType;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add new node type to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "New Node Type:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	if(oldNodeType != newNodeType) {
		newTd.className = "triggeredTd";
	}
	else {
		newTd.className = "neutralTd";
	}
	newTd.textContent = newNodeType;
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add old instance to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Old Instance:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = oldInstance;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add new instance to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "New Instance:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	if(oldInstance != newInstance) {
		newTd.className = "triggeredTd";
	}
	else {
		newTd.className = "neutralTd";
	}
	newTd.textContent = newInstance;
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add old version to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Old Version:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = oldVersion;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add new version to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "New Version:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	if(oldVersion != newVersion) {
		newTd.className = "triggeredTd";
	}
	else {
		newTd.className = "neutralTd";
	}
	newTd.textContent = newVersion;
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add old revision to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Old Revision:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = oldRev;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add new revision to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "New Revision:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	if(oldRev != newRev) {
		newTd.className = "triggeredTd";
	}
	else {
		newTd.className = "neutralTd";
	}
	newTd.textContent = newRev;
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

}


function addEventChangeSensor(eventsTable, oldAlertDelay, oldDescription,
	newAlertDelay, newDescription) {

	// add old alert delay to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Old Alert Delay:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = oldAlertDelay;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add new alert delay to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "New Alert Delay:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	if(oldAlertDelay != newAlertDelay) {
		newTd.className = "triggeredTd";
	}
	else {
		newTd.className = "neutralTd";
	}
	newTd.textContent = newAlertDelay;
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add old description to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Old Description:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = oldDescription;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add new description to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "New Description:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	if(oldDescription != newDescription) {
		newTd.className = "triggeredTd";
	}
	else {
		newTd.className = "neutralTd";
	}
	newTd.textContent = newDescription;
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

}


function addEventConnectedChange(eventsTable, hostname, nodeType, instance,
	connected) {

	// add hostname to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Hostname:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = hostname;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add nodeType to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Node Type:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = nodeType;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add instance to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Instance:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = instance;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add connected to the output
	event_AddConnectedOutput(eventsTable, connected);

}


function addEventDeleteAlert(eventsTable, description) {

	// add description to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Description:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = description;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

}


function addEventDeleteManager(eventsTable, description) {

	// add description to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Description:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = description;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

}


function addEventDeleteNode(eventsTable, hostname, nodeType, instance) {

	// add hostname to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Hostname:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = hostname;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add nodeType to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Node Type:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = nodeType;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add instance to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Instance:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = instance;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

}


function addEventDeleteSensor(eventsTable, description) {

	// add description to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Description:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = description;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

}


function addEventNewAlert(eventsTable, hostname, description) {

	// add hostname to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Hostname:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = hostname;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add description to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Description:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = description;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

}


function addEventNewManager(eventsTable, hostname, description) {

	// add hostname to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Hostname:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = hostname;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add description to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Description:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = description;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

}


function addEventNewNode(eventsTable, hostname, nodeType, instance) {

	// add hostname to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Hostname:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = hostname;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add nodeType to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Node Type:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = nodeType;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add instance to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Instance:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = instance;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

}


function addEventNewOption(eventsTable, optionType, value) {

	// add optionType to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Option Type:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = optionType;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add value to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Value:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	if(optionType == "alertSystemActive") {
		if(value == 1) {
			newTd.className = "activatedTd";
			newTd.textContent = "activated"
		}
		else {
			newTd.className = "deactivatedTd";
			newTd.textContent = "deactivated"
		}
	}
	else {
		newTd.className = "neutralTd";
		newTd.textContent = value;
	}
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

}


function addEventNewSensor(eventsTable, hostname, description, state) {

	// add hostname to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Hostname:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = hostname;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add description to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Description:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = description;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add state to the output
	event_AddStateOutput(eventsTable, state);

}


function addEventNewVersion(eventsTable, usedVersion, usedRev, newVersion,
	newRev, instance, hostname) {

	// add hostname to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Hostname:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = hostname;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add instance to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Instance:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = instance;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add used version to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Used Version:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = usedVersion;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add new version to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "New Version:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	if(usedVersion != newVersion) {
		newTd.className = "triggeredTd";
	}
	else {
		newTd.className = "neutralTd";
	}
	newTd.textContent = newVersion;
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add used revision to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Used Revision:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = usedRev;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add new revision to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "New Revision:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	if(usedRev != newRev) {
		newTd.className = "triggeredTd";
	}
	else {
		newTd.className = "neutralTd";
	}
	newTd.textContent = newRev;
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

}


function addEventSensorAlert(eventsTable, description, state) {

	// add description to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Description:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = description;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add state to the output
	event_AddStateOutput(eventsTable, state);

}


function addEventSensorTimeOut(eventsTable, hostname, description, state) {

	// add hostname to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Hostname:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = hostname;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add description to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Description:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = description;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add state to the output
	event_AddStateOutput(eventsTable, state);

}


function addEventStateChange(eventsTable, hostname, description, state) {

	// add hostname to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Hostname:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = hostname;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add description to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Description:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newTd.textContent = description;
	newTd.className = "neutralTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);


	// add state to the output
	event_AddStateOutput(eventsTable, state);

}


function event_AddStateOutput(eventsTable, state) {

	// add state to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "State:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	if(state == 1) {
		newTd.className = "triggeredTd";
		newTd.textContent = "triggered"
	}
	else {
		newTd.className = "okTd";
		newTd.textContent = "normal"
	}
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

}


function event_AddConnectedOutput(eventsTable, connected) {

	// add connected to the event
	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	newB = document.createElement("b");
	newB.textContent = "Connected:";
	newTd.appendChild(newB);
	newTd.className = "boxEntryTd";
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

	newTr = document.createElement("tr");
	newTd = document.createElement("td");
	if(connected == 1) {
		newTd.className = "okTd";
		newTd.textContent = "true";
	}
	else {
		newTd.className = "failTd";
		newTd.textContent = "false";
	}
	newTr.appendChild(newTd);
	eventsTable.appendChild(newTr);

}