var graphButton = 'local-stats-button'
var deauthButton = 'deauth-button'
var nmapButton = 'nmap-button'
var badUSBButton = 'usb-button'

var graphButtonEnabled = false
var deauthButtonEnabled = false
var nmapButtonEnabled = false
var usbButtonEnabled = false

var statsDisplay = "flex"
var deauthDisplay = "flex"
var nmapDisplay = "flex"
var usbDisplay = "flex"

var ramUsage = makeNewStat("ramUsage")
var cpuUsage = makeNewStat("cpuUsage")
var cpuTemp = makeNewStat("cpuTemp")
var usbPercent = makeNewStat("usbPercent")

let badusbScripts = []

String.prototype.formatUnicorn = String.prototype.formatUnicorn ||
function () {
    "use strict";
    var str = this.toString();
    if (arguments.length) {
        var t = typeof arguments[0];
        var key;
        var args = ("string" === t || "number" === t) ?
            Array.prototype.slice.call(arguments)
            : arguments[0];

        for (key in args) {
            str = str.replace(new RegExp("\\{" + key + "\\}", "gi"), args[key]);
        }
    }

    return str;
};

function showStats() {
    displayHandler()
    if (graphButtonEnabled == false) { graphButtonEnabled = true }
    else if (graphButtonEnabled == true) { graphButtonEnabled = false }
    turnCool(document.getElementById(graphButton), graphButtonEnabled)

    document.getElementById('stats').style.display = statsDisplay
}

function showDeauth() {
    displayHandler()
    if (deauthButtonEnabled == false) { deauthButtonEnabled = true }
    else if (deauthButtonEnabled == true) { deauthButtonEnabled = false }
    turnCool(document.getElementById(deauthButton), deauthButtonEnabled)

    document.getElementById('deauth-term').style.display = deauthDisplay
}

function showNMAP() {
    displayHandler()
    if (nmapButtonEnabled == false) { nmapButtonEnabled = true }
    else if (nmapButtonEnabled == true) { nmapButtonEnabled = false }
    turnCool(document.getElementById(nmapButton), nmapButtonEnabled)

    document.getElementById('nmap-term').style.display = nmapDisplay
}

function showUSB() {
    displayHandler()
    if (usbButtonEnabled == false) { usbButtonEnabled = true }
    else if (usbButtonEnabled == true) { usbButtonEnabled = false }
    turnCool(document.getElementById(badUSBButton), usbButtonEnabled)

    document.getElementById('badUSB').style.display = usbDisplay
}

function showSuccessToast(one, two) {
    toastr["success"](one, two)

    toastr.options = {
        "closeButton": true,
        "debug": false,
        "newestOnTop": false,
        "progressBar": true,
        "positionClass": "toast-top-right",
        "preventDuplicates": true,
        "onclick": null,
        "showDuration": "300",
        "hideDuration": "1000",
        "timeOut": "5000",
        "extendedTimeOut": "1000",
        "showEasing": "swing",
        "hideEasing": "linear",
        "showMethod": "fadeIn",
        "hideMethod": "fadeOut"
    }
}

function showInfoToast(one, two) {
    toastr["info"](one, two)

    toastr.options = {
        "closeButton": true,
        "debug": false,
        "newestOnTop": false,
        "progressBar": true,
        "positionClass": "toast-top-right",
        "preventDuplicates": true,
        "onclick": null,
        "showDuration": "300",
        "hideDuration": "1000",
        "timeOut": "5000",
        "extendedTimeOut": "1000",
        "showEasing": "swing",
        "hideEasing": "linear",
        "showMethod": "fadeIn",
        "hideMethod": "fadeOut"
    }
}

function showWarningToast(one, two) {
    toastr.options = {
        "closeButton": true,
        "debug": false,
        "newestOnTop": false,
        "progressBar": true,
        "positionClass": "toast-top-right",
        "preventDuplicates": true,
        "onclick": null,
        "showDuration": "300",
        "hideDuration": "1000",
        "timeOut": "5000",
        "extendedTimeOut": "1000",
        "showEasing": "swing",
        "hideEasing": "linear",
        "showMethod": "fadeIn",
        "hideMethod": "fadeOut"
    }

    toastr["warning"](one, two)
}

function showErrorToast(one, two) {
    toastr.options = {
        "closeButton": true,
        "debug": false,
        "newestOnTop": false,
        "progressBar": true,
        "positionClass": "toast-top-right",
        "preventDuplicates": true,
        "onclick": null,
        "showDuration": "0",
        "hideDuration": "0",
        "timeOut": "0",
        "extendedTimeOut": "0",
        "showEasing": "swing",
        "hideEasing": "linear",
        "showMethod": "fadeIn",
        "hideMethod": "fadeOut"
    }

    toastr["error"](one, two)
}

function makeUSBBox(scriptName, scriptDescription) {
    var a = document.getElementById("usbBoxArea")

    var divNode = document.createElement("div")

    var nameNode = document.createTextNode(scriptName)
    var descNode = document.createTextNode(scriptDescription)
    var buttonNode = document.createTextNode("execute")

    var nameEle = document.createElement("h2")
    var descEle = document.createElement("span")
    var buttonEle = document.createElement("button")

    nameEle.appendChild(nameNode)
    descEle.appendChild(descNode)
    buttonEle.appendChild(buttonNode)

    buttonEle.addEventListener('click', function () {usbRun(scriptName)})

    divNode.appendChild(nameEle)
    divNode.appendChild(descEle)
    divNode.appendChild(document.createElement("br"))
    divNode.appendChild(buttonEle)

    divNode.className = "cool-box usbBox"

    a.appendChild(divNode)
}

async function usbRun(name) {

    var xmlHttp = new XMLHttpRequest();
    var xmlHttp2 = new XMLHttpRequest();

    xmlHttp.open("POST", "/api/badusb/run", true); // false for synchronous request
    xmlHttp.send('{"script":"{0}"}'.formatUnicorn(name));

    while (1) {
        xmlHttp2.open("GET", "/api/badusb/dumpInfo", false); // false for synchronous request
        xmlHttp2.send(null)

        var jsond = JSON.parse(xmlHttp2.responseText)

        var percentage = parseInt(jsond.percentageDone)

        usbPercent.setValueAnimated(percentage, 1)
        document.getElementById("usb-term-output").value = jsond.console
        document.getElementById("usb-term-output").scrollTop = document.getElementById("usb-term-output").scrollHeight

        if (percentage >= 100) {return}
        else {
            await new Promise(r => setTimeout(r, 1000));
        }
    }
}

function displayHandler() {
    graphButtonEnabled = false
    deauthButtonEnabled = false
    nmapButtonEnabled = false
    usbButtonEnabled = false

    turnCool(document.getElementById(graphButton), false)
    turnCool(document.getElementById(deauthButton), false)
    turnCool(document.getElementById(nmapButton), false)
    turnCool(document.getElementById(badUSBButton), false)

    document.getElementById('stats').style.display = 'none'
    document.getElementById('deauth-term').style.display = 'none'
    document.getElementById('nmap-term').style.display = 'none'
    document.getElementById('badUSB').style.display = 'none'
}

function makeNewStat(divID) {
    return Gauge(
        document.getElementById(divID), {
        max: 100,
        dialStartAngle: 90,
        dialEndAngle: 0,
        value: 50
    }
    );
}

function turnCool(object, enable) {
    if (enable == true) {
        object.style.borderLeftWidth = "4px"
        object.style.borderLeftColor = "#290c6e"
        object.style.borderStyle = "solid"
    }
    else {
        object.style.borderLeftWidth = "4px"
        object.style.borderStyle = "none"
    }
}

function makeRequest(method, url) {
    return new Promise(function (resolve, reject) {
        let xhr = new XMLHttpRequest();
        xhr.open(method, url);
        xhr.onload = function () {
            if (this.status >= 200 && this.status < 300) {
                resolve(xhr.response);
            } else {
                reject({
                    status: this.status,
                    statusText: xhr.statusText
                });
            }
        };
        xhr.onerror = function () {
            reject({
                status: this.status,
                statusText: xhr.statusText
            });
        };
        xhr.send();
    });
}

async function updateInfov3() {
    while (1) {
        try {
            var msg = await makeRequest("GET", "/api/dumpInfo")
        } catch {
            showErrorToast("will try every 5 seconds; you are likely to be logged out once host comes back", "lost connection to host")
            await new Promise(r => setTimeout(r, 5000))
            continue
        }

        msg = JSON.parse(msg)

        console.log(JSON.parse(msg.deauth))

        if (msg.data == "no") {location.reload()}
        var pools = msg.pools
        var sysInfo = msg.system

        document.getElementById("deauth-term-output").scrollTop = document.getElementById("deauth-term-output").scrollHeight

        cpuUsage.setValueAnimated(sysInfo.cpuPercent, 1);
        cpuTemp.setValueAnimated(sysInfo.cpuTemp, 1);
        ramUsage.setValueAnimated(sysInfo.ramPercent, 1);


        document.getElementById("pwnface").innerHTML = JSON.parse(msg.deauth).face
        document.getElementById("deauth-term-output").value = pools.deauth

        await new Promise(r => setTimeout(r, 1000));
    }
}
window.addEventListener('load', async function () {

    if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
        location.href = "/mobile"
    }

    document.getElementById(graphButton).addEventListener('click', function () { showStats() });
    document.getElementById(deauthButton).addEventListener('click', function () { showDeauth() });
    document.getElementById(nmapButton).addEventListener('click', function () { showNMAP() });
    document.getElementById(badUSBButton).addEventListener('click', function () { showUSB() });

    document.getElementById("deauthStart").addEventListener('click', function () {
        makeRequest("GET", "/api/commands/pwnagotchiStart")
    });

    document.getElementById("deauthStop").addEventListener('click', function () {
        makeRequest("GET", "/api/commands/pwnagotchiStop")
    });

    //NMAP

    document.getElementById("nmapStart").addEventListener('click', function () {
        var socket = io();
        var args = ""
        var host = document.getElementById("nmapTarget").value

        if (document.getElementById("nmapVerbose").checked) { args += "-vv " }
        if (document.getElementById("nmapOS").checked) { args += "-O " }
        if (document.getElementById("nmapVerFind").checked) { args += "-sV " }
        if (document.getElementById("nmapFastMode").checked) { args += "-F " }
        if (document.getElementById("nmapHostDiscovery").checked) { args += "-Pn " }
        if (document.getElementById("nmapSpoofSource").checked) { args += "-S (regexRandIP) " }
        if (document.getElementById("nmapBadsum").checked) { args += "--badsum " }
        if (document.getElementById("nmapPortRange").checked) { args += "-p" + document.getElementById("nmapPort1").value + "-" + document.getElementById("nmapPort2").value + " " }

        var full = args + host

        showSuccessToast("nmap " + full, "started nmap scanning")

        document.getElementById("nmap-term-output").value = "> nmap " + full + "\n\n"

        socket.on('data', function (msg, cb) {
            document.getElementById("nmap-term-output").value += msg.data

            if (msg.data == "\nnmap scan finished") { showSuccessToast("go to NMAP terminal to view results", "NMAP scan finished") }
        });

        socket.emit('nmapRun', { args: full });
    });

    displayHandler()
    graphButtonEnabled = !graphButtonEnabled
    turnCool(document.getElementById(graphButton), graphButtonEnabled)

    document.getElementById('stats').style.display = statsDisplay

    var msg = JSON.parse(await makeRequest("GET", "/api/badusb/scripts"))
    for (let i = 0; i < msg.scripts.length; i++) {
        makeUSBBox(msg.scripts[i], "desc")
    }

    usbPercent.setValueAnimated(0, 0)

    updateInfov3()
})