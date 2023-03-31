var graphButton = 'local-stats-button'
var pluginButton = 'plugin-button'

var graphButtonEnabled = false
var pluginButtonEnabled = false

var statsDisplay = "flex"
var pluginDisplay = "flex"

var ramUsage = makeNewStat("ramUsage")
var cpuUsage = makeNewStat("cpuUsage")
var cpuTemp = makeNewStat("cpuTemp")


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

function showPlugin() {
    displayHandler()
    if (pluginButtonEnabled == false) { pluginButtonEnabled = true }
    else if (pluginButtonEnabled == true) { pluginButtonEnabled = false }
    turnCool(document.getElementById(pluginButton), pluginButtonEnabled)

    document.getElementById('plugins').style.display = pluginDisplay
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

function displayHandler() {
    graphButtonEnabled = false
    pluginButtonEnabled = false

    turnCool(document.getElementById(graphButton), false)
    turnCool(document.getElementById(pluginButton), false)

    document.getElementById('stats').style.display = 'none'
    document.getElementById('plugins').style.display = 'none'
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

function makePlugBox(scriptName, scriptDescription) {
    var a = document.getElementById("plugArea")

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

    buttonEle.addEventListener('click', function () {
        var xhr = new XMLHttpRequest();
        xhr.onreadystatechange = function() {
            if (xhr.readyState == XMLHttpRequest.DONE) {
                console.log(xhr.responseText);
            }
        }
        xhr.open("POST", "/api/plugins/run");
        xhr.send(JSON.stringify({"plugin":scriptName}));
        
    })

    divNode.appendChild(nameEle)
    divNode.appendChild(descEle)
    divNode.appendChild(document.createElement("br"))
    divNode.appendChild(buttonEle)

    divNode.className = "cool-box usbBox"

    a.appendChild(divNode)
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

        console.log(msg)

        if (msg.data == "no") {location.reload()}
        var sysInfo = msg.system

        document.getElementById("plugin-term").scrollTop = document.getElementById("plugin-term").scrollHeight
        document.getElementById("plugin-term").value = await makeRequest("GET", "/api/plugins/console")

        cpuUsage.setValueAnimated(sysInfo.cpuPercent, 1);
        cpuTemp.setValueAnimated(sysInfo.cpuTemp, 1);
        ramUsage.setValueAnimated(sysInfo.ramPercent, 1);

        await new Promise(r => setTimeout(r, 1000));
    }
}
window.addEventListener('load', async function () {

    if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
        location.href = "/mobile"
    }

    document.getElementById(graphButton).addEventListener('click', function () { showStats() });
    document.getElementById(pluginButton).addEventListener('click', function () { showPlugin() });

    displayHandler()
    graphButtonEnabled = !graphButtonEnabled
    turnCool(document.getElementById(graphButton), graphButtonEnabled)

    var msg = JSON.parse(await makeRequest("GET", "/api/plugins/show"))
    for (let i = 0; i < Object.keys(msg.plugins).length; i++) {
        console.log("abxcd")
        makePlugBox(Object.keys(msg.plugins)[i], "desc")
    }

    document.getElementById('stats').style.display = statsDisplay

    document.getElementById("pluginInput").addEventListener("keydown", (e)=>{
        if(e.key === "Enter"){
            var xhr = new XMLHttpRequest();
            xhr.onreadystatechange = function() {
                if (xhr.readyState == XMLHttpRequest.DONE) {
                    console.log(xhr.responseText);
                }
            }
            xhr.open("POST", "/api/plugins/input");
            xhr.send(JSON.stringify({"input":document.getElementById("pluginInput").value}));

            document.getElementById("pluginInput").value = ""
        }
    })

    updateInfov3()
})