// set global configuration variables
var request = new XMLHttpRequest();
var setTimeoutIdRequest = null;
var setTimeoutIdOnlineCheck = null;
var sensorAlertsNumber = 50;
var sensorAlertsRangeStart = 0;
var configUnixSocketActive =
    (document.body.dataset.configunixsocketactive == "true");

// This enum gives the different data types of a sensor.
var SensorDataType = {
    NONE: 0,
    INT: 1,
    FLOAT: 2,
    GPS: 3
}

// This enum gives the different sensor error states.
var SensorErrorState = {
    OK: 0,
    GenericError: 1,
    ProcessingError: 2,
    TimeoutError: 3,
    ConnectionError: 4,
    ExecutionError: 5,
    ValueError: 6
}

// global objects filled with server responses
var alertLevels = null;
var alerts = null;
var internals = null;
var managers = null;
var nodes = null;
var options = null;
var profiles = null;
var sensorAlerts = null;
var sensors = null;

// needed to check the time out of the alertR database instance
var msgTime = 0.0;
var lastmsgTime = 0.0;
var lastmsgTimeUpdate = null;
var online = false;
var timeoutInterval = 80 // in seconds
var msgTimeTd = null;
var onlineTd = null;

// gives the output that is currently shown
var currentOutput = null;

var lastResponse = null;

// needed to decide the correct color of the used system profile.
var profilesColor = ["profile0Td", "profile1Td", "profile2Td", "profile3Td", "profile4Td"];


// adds a menu for the navigation to the given table body
function addMenu(newBody, current) {

    // check if alertR database instance is online
    checkOnline();

    // generate date string from timestamp
    localDate = new Date(msgTime * 1000);
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
    msgTimeString = monthString + "/" + dateString + "/" +
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

    // add msg time output
    var newTr = document.createElement("tr");
    var newTd = document.createElement("td");
    var newB = document.createElement("b");
    newB.textContent = "Last Message Received:";
    newTd.appendChild(newB);
    newTd.className = "boxEntryTd";
    newTr.appendChild(newTd);
    menuTable.appendChild(newTr);

    var newTr = document.createElement("tr");
    msgTimeTd = document.createElement("td");
    if(online) {
        msgTimeTd.className = "normalTd";
        msgTimeTd.textContent = msgTimeString;
    }
    else {
        msgTimeTd.className = "failTd";
        msgTimeTd.textContent = msgTimeString;
    }
    newTr.appendChild(msgTimeTd);
    menuTable.appendChild(newTr);

    // process options of the alert system
    for(var i = 0; i < options.length; i++) {

        // only evaluate "profile"
        if(options[i]["type"].toUpperCase() == "PROFILE") {

            // add system profile of AlertR system
            var newTr = document.createElement("tr");
            var newTd = document.createElement("td");
            var newB = document.createElement("b");
            newB.textContent = "Profile:";
            newTd.appendChild(newB);
            newTd.className = "boxEntryTd";
            newTr.appendChild(newTd);
            menuTable.appendChild(newTr);

            var newTr = document.createElement("tr");
            var newTd = document.createElement("td");

            for(var j = 0; j < profiles.length; j++) {
                if(profiles[j]["profileId"] == Math.trunc(options[i]["value"])) {
                    newTd.className = profilesColor[profiles[j]["profileId"] % profilesColor.length];
                    newTd.textContent = profiles[j]["name"];
                    break;
                }
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

                for(var j = 0; j < profiles.length; j++) {
                    var newTr = document.createElement("tr");
                    tempTable.appendChild(newTr)

                    var newTd = document.createElement("td");
                    newTd.className = "buttonTd";

                    var newA = document.createElement("a");
                    newA.className = "buttonA";
                    newA.textContent = profiles[j]["name"];
                    newA.href = "javascript:void(0)";

                    let profileId = profiles[j]["profileId"];
                    let profileName = profiles[j]["name"];
                    newA.onclick = function(){ confirmation(profileId, profileName, current); };
                    newTd.appendChild(newA);
                    newTr.appendChild(newTd);
                }
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
                || profiles == null
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
                || profiles == null
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
        case "managers":
            currentOutput = "managers";
            if(internals == null
                || options == null
                || profiles == null
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
                || profiles == null
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
                || profiles == null
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
                || profiles == null
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
                || profiles == null
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

    // update last msg time if it has changed
    if(msgTime > lastmsgTime) {
        lastmsgTime = msgTime;
        lastmsgTimeUpdate = new Date();
        online = true;

        if(msgTimeTd != null) {
            // generate date string from timestamp
            localDate = new Date(msgTime * 1000);
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
            msgTimeString = monthString + "/" + dateString + "/" +
                yearString + " " + hoursString + ":" +
                minutesString + ":" + secondsString;

            msgTimeTd.className = "normalTd";
            msgTimeTd.textContent = msgTimeString;
        }

        if(onlineTd != null) {
            onlineTd.className = "normalTd";
            onlineTd.textContent = "online";    
        }
    }

    // check if msg time has not changed since timeout interval
    var temp = new Date();
    if(lastmsgTimeUpdate && temp.getTime() > 
        (lastmsgTimeUpdate.getTime() + (timeoutInterval * 1000))) {
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


// simple function to ask for confirmation if the AlertR system
// should change the system profile
function confirmation(profileId, profileName, current) {

    if(configUnixSocketActive) {
        result = confirm("Do you really want to change the system profile to '" + profileName + "'?");
        if(result) {

            // show loader and hide content
            var loaderObj = document.getElementById("loader");
            loaderObj.className = "elementShown";
            var contentObj = document.getElementById("content");
            contentObj.className = "elementHidden";

            window.location = "index.php?profilechange=" + profileId + "#content=" + current;
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
        profiles = alertSystemInformation["profiles"];
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
        profiles = alertSystemInformation["profiles"];
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
        profiles = alertSystemInformation["profiles"];
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
        profiles = alertSystemInformation["profiles"];
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
        profiles = alertSystemInformation["profiles"];
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
        profiles = alertSystemInformation["profiles"];
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
        profiles = alertSystemInformation["profiles"];
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
                + "&data[]=profiles"
                + "&data[]=alertlevels";
            request.open("GET", url, true);
            request.onreadystatechange = processResponseAlertLevels;
            nextContent = content;
            break;
        case "alerts":
            var url = "./getJson.php"
                + "?data[]=internals"
                + "&data[]=options"
                + "&data[]=profiles"
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
                + "&data[]=options"
                + "&data[]=profiles"
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
                + "&data[]=profiles"
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
                    + "&data[]=profiles"
                    + "&data[]=sensorAlerts";
            }
            else {
                var url = "./getJson.php"
                    + "?data[]=internals"
                    + "&data[]=options"
                    + "&data[]=profiles"
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
                + "&data[]=profiles"
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
                + "&data[]=profiles"
                + "&data[]=nodes"
                + "&data[]=sensorAlerts"
                + "&sensorAlertsRangeStart=0"
                + "&sensorAlertsNumber=10"
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

    // get msg time
    for(var i = 0; i < internals.length; i++) {
        if(internals[i]["type"].toUpperCase() == "MSGTIME") {
            msgTime = internals[i]["value"]
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
        var instrumentation_active = alertLevels[i]["instrumentation_active"];
        var alertLevelProfiles = alertLevels[i]["profiles"];


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


        // add instrumentation_active to the alertLevel
        var newTr = document.createElement("tr");
        var newTd = document.createElement("td");
        var newB = document.createElement("b");
        newB.textContent = "Instrumentation Active:";
        newTd.appendChild(newB);
        newTd.className = "boxEntryTd";
        newTr.appendChild(newTd);
        alertLevelTable.appendChild(newTr);

        var newTr = document.createElement("tr");
        var newTd = document.createElement("td");
        if(instrumentation_active == 0) {
            newTd.textContent = "false";
        }
        else {
            newTd.textContent = "true";
        }
        newTd.className = "neutralTd";
        newTr.appendChild(newTd);
        alertLevelTable.appendChild(newTr);


        // add profiles to the alertLevel
        var newTr = document.createElement("tr");
        var newTd = document.createElement("td");
        var newB = document.createElement("b");
        newB.textContent = "Profiles:";
        newTd.appendChild(newB);
        newTd.className = "boxEntryTd";
        newTr.appendChild(newTd);
        alertLevelTable.appendChild(newTr);

        var newTr = document.createElement("tr");
        var newTd = document.createElement("td");
        newTd.textContent = alertLevelProfiles;
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

    // get msg time
    for(var i = 0; i < internals.length; i++) {
        if(internals[i]["type"].toUpperCase() == "MSGTIME") {
            msgTime = internals[i]["value"]
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
        var persistent = nodes[i]["persistent"];

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
            if(persistent == 1) {
                newTd.className = "failTd";
            }
            else {
                newTd.className = "neutralTd";
            }
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

    // get msg time
    for(var i = 0; i < internals.length; i++) {
        if(internals[i]["type"].toUpperCase() == "MSGTIME") {
            msgTime = internals[i]["value"]
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
        var persistent = nodes[i]["persistent"];

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
            if(persistent == 1) {
                newTd.className = "failTd";
            }
            else {
                newTd.className = "neutralTd";
            }
            newTd.textContent = "false";
        }
        else {
            newTd.className = "neutralTd";
            newTd.textContent = "true";
        }
        newTr.appendChild(newTd);
        nodeTable.appendChild(newTr);

        managers.sort(compareManagersAsc);

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

    // get msg time
    for(var i = 0; i < internals.length; i++) {
        if(internals[i]["type"].toUpperCase() == "MSGTIME") {
            msgTime = internals[i]["value"]
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
        var persistent = nodes[i]["persistent"];

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
            if(persistent == 1) {
                newTd.className = "failTd";
            }
            else {
                newTd.className = "neutralTd";
            }
            newTd.textContent = "false";
        }
        else {
            newTd.className = "neutralTd";
            newTd.textContent = "true";
        }
        newTr.appendChild(newTd);
        nodeTable.appendChild(newTr);


        // add persistent to the node
        newTr = document.createElement("tr");
        newTd = document.createElement("td");
        newB = document.createElement("b");
        newB.textContent = "Persistent Connection:";
        newTd.appendChild(newB);
        newTd.className = "boxEntryTd";
        newTr.appendChild(newTd);
        nodeTable.appendChild(newTr);

        newTr = document.createElement("tr");
        newTd = document.createElement("td");
        if(persistent == 0) {
            newTd.className = "neutralTd";
            newTd.textContent = "false";
        }
        else {
            if(connected == 0) {
                newTd.className = "failTd";
            }
            else {
                newTd.className = "neutralTd";
            }
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

    // get msg time
    for(var i = 0; i < internals.length; i++) {
        if(internals[i]["type"].toUpperCase() == "MSGTIME") {
            msgTime = internals[i]["value"]
        }
    }

    // add header of site
    addMenu(newBody, "overview");

    // generate sensor alerts overview output
    sensorAlerts.sort(compareSensorAlertsDesc);
    sensors.sort(compareSensorsAsc);

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
    for(var i = 0; i < 10; i++) {
        if(i >= sensorAlerts.length) {
            break;
        }

        var timeReceived = sensorAlerts[i]["timeReceived"];
        var state = sensorAlerts[i]["state"];
        var description = sensorAlerts[i]["description"];
        var jsonData = sensorAlerts[i]["optionalData"];
        var optionalData = JSON.parse(jsonData);

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

        // check if a message was sent along with the sensor alert
        if(optionalData.hasOwnProperty("message")) {
            newTd.appendChild(document.createTextNode(" (" + optionalData["message"] + ")"));
        }
        newTd.appendChild(document.createElement("br"));

        if(state == 0) {
            newTd.className = "normalTd";
            newTd.appendChild(document.createTextNode("Normal"));
        }
        else {
            newTd.className = "triggeredTd";
            newTd.appendChild(document.createTextNode("Triggered"));
        }
        newTd.appendChild(document.createElement("br"));
        newTd.appendChild(document.createTextNode(timeReceivedString));
        newTr.appendChild(newTd);
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
        var state = sensors[i]["state"];
        var dataType = sensors[i]["dataType"];
        var data = sensors[i]["data"];
        var errorState = sensors[i]["error_state"];
        var errorMsg = sensors[i]["error_msg"];
        var connected = 0;
        var persistent = 0;

        // get connected information from corresponding node
        for(j = 0; j < nodes.length; j++) {
            if(nodes[j]["id"] == nodeId) {
                var connected = nodes[j]["connected"];
                var persistent = nodes[j]["persistent"];
                break;
            }
        }

        // output sensor descriptions according to state/connected/updated
        var newTr = document.createElement("tr");
        var newTd = document.createElement("td");
        newTd.appendChild(document.createTextNode(description));
        if(dataType != SensorDataType.NONE) {
            newTd.appendChild(document.createElement("br"));
            newTd.appendChild(document.createTextNode("Data: " + data));
        }

        if(connected == 0) {
            if(persistent == 1) {
                newTd.className = "failTd";
            }
            else {
                newTd.className = "neutralTd";
            }
            newTd.appendChild(document.createElement("br"));
            newTd.appendChild(document.createTextNode("(not connected)"));
        }
        else if(errorState != SensorErrorState.OK) {
            newTd.className = "errorTd";
            newTd.appendChild(document.createElement("br"));
            newTd.appendChild(document.createTextNode("(error)"));
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

    // get msg time
    for(var i = 0; i < internals.length; i++) {
        if(internals[i]["type"].toUpperCase() == "MSGTIME") {
            msgTime = internals[i]["value"]
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
        var jsonData = sensorAlerts[i]["optionalData"];
        var state = sensorAlerts[i]["state"];
        var description = sensorAlerts[i]["description"];
        var optionalData = JSON.parse(jsonData);
        var dataType = sensorAlerts[i]["dataType"];
        var data = sensorAlerts[i]["data"];
        var alertLevels = sensorAlerts[i]["alertLevels"];


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


        // Add data if sensor alert carries any.
        if(dataType != SensorDataType.NONE) {
            newTr = document.createElement("tr");
            newTd = document.createElement("td");
            newB = document.createElement("b");
            newB.textContent = "Data:";
            newTd.appendChild(newB);
            newTd.className = "boxEntryTd";
            newTr.appendChild(newTd);
            sensorAlertTable.appendChild(newTr);

            newTr = document.createElement("tr");
            newTd = document.createElement("td");
            newTd.textContent = data;
            newTd.className = "neutralTd";
            newTr.appendChild(newTd);
            sensorAlertTable.appendChild(newTr);
        }


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


        // check if a message was sent along with the sensor alert
        if(optionalData.hasOwnProperty("message")) {

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
            newTd.textContent = optionalData["message"];
            newTd.className = "neutralTd";
            newTr.appendChild(newTd);
            sensorAlertTable.appendChild(newTr);
        }

        // add alert levels to the sensor alert
        var newTr = document.createElement("tr");
        var newTd = document.createElement("td");
        var newB = document.createElement("b");
        newB.textContent = "Alert Levels:";
        newTd.appendChild(newB);
        newTd.className = "boxEntryTd";
        newTr.appendChild(newTd);
        sensorAlertTable.appendChild(newTr);

        var newTr = document.createElement("tr");
        var newTd = document.createElement("td");
        newTd.textContent = alertLevels.map(String).join(", ");
        newTd.className = "neutralTd";
        newTr.appendChild(newTd);
        sensorAlertTable.appendChild(newTr);

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

    // get msg time
    for(var i = 0; i < internals.length; i++) {
        if(internals[i]["type"].toUpperCase() == "MSGTIME") {
            msgTime = internals[i]["value"]
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
        var persistent = nodes[i]["persistent"];

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
            if(persistent == 1) {
                newTd.className = "failTd";
            }
            else {
                newTd.className = "neutralTd";
            }
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
            var state = relatedSensors[j]["state"];
            var relatedAlertLevels = relatedSensors[j]["alertLevels"];
            var dataType = relatedSensors[j]["dataType"];
            var data = relatedSensors[j]["data"];
            var errorState = relatedSensors[j]["error_state"];
            var errorMsg = relatedSensors[j]["error_msg"];


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


            // Add data to sensor.
            if(dataType != SensorDataType.NONE) {
                var newTr = document.createElement("tr");
                var newTd = document.createElement("td");
                var newB = document.createElement("b");
                newB.textContent = "Data:";
                newTd.appendChild(newB);
                newTd.className = "boxEntryTd";
                newTr.appendChild(newTd);
                sensorTable.appendChild(newTr);

                var newTr = document.createElement("tr");
                var newTd = document.createElement("td");
                newTd.textContent = data;
                newTd.className = "neutralTd";
                newTr.appendChild(newTd);
                sensorTable.appendChild(newTr);
            }


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


            // add sensor error state to the sensor
            var newTr = document.createElement("tr");
            var newTd = document.createElement("td");
            var newB = document.createElement("b");
            newB.textContent = "Error State:";
            newTd.appendChild(newB);
            newTd.className = "boxEntryTd";
            newTr.appendChild(newTd);
            sensorTable.appendChild(newTr);

            var newTr = document.createElement("tr");
            var newTd = document.createElement("td");
            // set color to red if the sensor has an error
            if(errorState != SensorErrorState.OK) {
                newTd.className = "errorTd";
                switch(errorState) {
                    case SensorErrorState.GenericError:
                        newTd.textContent = "Generic Error: " + errorMsg
                        break;
                    case SensorErrorState.ProcessingError:
                        newTd.textContent = "Processing Error: " + errorMsg
                        break;
                    case SensorErrorState.TimeoutError:
                        newTd.textContent = "Timeout Error: " + errorMsg
                        break;
                    case SensorErrorState.ConnectionError:
                        newTd.textContent = "Connection Error: " + errorMsg
                        break;
                    case SensorErrorState.ExecutionError:
                        newTd.textContent = "Execution Error: " + errorMsg
                        break;
                    case SensorErrorState.ValueError:
                        newTd.textContent = "Value Error: " + errorMsg
                        break;
                    default:
                        newTd.textContent = "Unknown Error: " + errorMsg
                        break;
                }
            }
            else {
                newTd.className = "neutralTd";
                newTd.textContent =  "OK";
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


// output selected view
var hashVar = window.location.hash;
if(hashVar) {
    var content = hashVar.substr(hashVar.indexOf('content='))
        .split("&")[0]
        .split("=")[1];
    changeOutput(content);
}
else {
    changeOutput("overview");
}

