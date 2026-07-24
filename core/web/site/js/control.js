const canvas = document.getElementById("displayCanvas")
let touchstartY = 0
let touchendY = 0
let touchstartX = 0
let touchendX = 0
let canvasInputActive = false

var sshIO = io("/")
var socket
var connectedToken = undefined
var sysinfoElementsCreated = false

const term = new Terminal();

const greetings = [
    "Welcome, #!",
    "Hey #!",
    "Good to see you, #.",
    "Good luck, #.",
    "Greetings, #.",
    "Good evening, #."
]

sshIO.on("sshtx", (msg) => {
    term.write(msg["byte"])
})

sshIO.on("tkn", (msg) => {
    console.warn(`token ${msg["token"]}`)
    connectedToken = msg["token"]
})

sshIO.on("authstatus", (msg) => {
    console.warn(`authstatus ${msg["reason"]}`)
    manageAuth(msg["status"])
})

sshIO.on("sshbuf", (msg) => {
    term.write(msg["buffer"])
})

sshIO.on("addons", (msg) => {
    console.log(msg)

    for (const addon of msg) {
        var sbItem = document.createElement("div")
        var img = document.createElement("img")
        var sbItemName = document.createElement("div")
        var p = document.createElement("p")

        sbItem.className = "sidebar-item"
        
        img.src = addon["manifest"]["icon"]
        img.width = 32
        img.height = 32

        sbItemName.className = "sidebar-item-name"

        p.innerHTML = addon["manifest"]["name"]

        sbItemName.appendChild(p)

        sbItem.appendChild(img)
        sbItem.appendChild(sbItemName)

        document.getElementById("sidebar").appendChild(sbItem)

        /* now add the iframe */
        var iframe = document.createElement("iframe")
        iframe.src = addon["path"]
        iframe.className = "addon-iframe"

        document.getElementById("inner-body").appendChild(iframe)

        sbItem.addEventListener("click", function(){
            iframe.scrollIntoView({behavior: 'smooth'})
        })
    }
})

sshIO.on("sysinfo", (msg) => {
    keys = Object.keys(msg)

    if (!sysinfoElementsCreated) {
        var alternate = false
        for (var i=0; i<keys.length; i++) { // create elements
            key = keys[i]
    
            var holder = document.createElement("div")
            var title = document.createElement("p")
            var value = document.createElement("p")
            
            holder.className = "sbs"

            title.innerHTML = key
            value.innerHTML = msg[key]
            value.id = key
    
            holder.appendChild(title)
            holder.appendChild(value)
            
            if (alternate) {
                document.getElementById("databox-l").appendChild(holder)
            } else {
                document.getElementById("databox-r").appendChild(holder)
            }
            alternate = !alternate
        }
        sysinfoElementsCreated = true
    }


    for (var i=0; i<keys.length; i++) {
        key = keys[i]

        document.getElementById(key).innerHTML = msg[key]
    }
})

function showIframe(path) {
    console.log(`do something with ${path}`)
}

function WSConnect() {
    socket = new WebSocket(`ws://${location.hostname}:8765`)

    socket.addEventListener("open", (event) => {
        document.getElementById("status").innerHTML = "CONNECTED."

        socket.send("R")
    })

    socket.addEventListener("message", (event) => {
        var json = JSON.parse(event.data)

        var frame = json["frame"]
        mergeDisplay(frame)
    })

    socket.addEventListener("close", function (e) {
        console.log('socket closed, reconnecting', e.reason)
        document.getElementById("status").innerHTML = "SOCKET CLOSED."

        canvasInputActive = false
        canvas.setAttribute("blurry", true)

        setTimeout(function () {
            WSConnect()
        }, 500)
    })
}

function mergeDisplay(base64) {
    var mergedBase64 = "data:image/png;base64, " + base64

    var context = canvas.getContext('2d')

    context.imageSmoothingEnabled = false

    var base = new Image()
    var vnc = new Image()

    var height = canvas.height
    var width = canvas.width

    //context.fillStyle = 'black'
    //context.fillRect(0, 0, canvas.width, canvas.height)

    base.src = "/oled2.png"
    base.onload = function () {

        vnc.src = mergedBase64
        vnc.onload = function () {
            context.drawImage(base, 0, 0, width, height)
            context.drawImage(vnc, 256 + 6, 128, 590, 322)
        }
    }
}

document.addEventListener("keydown", function (event) {
    if (!canvasInputActive) { return }

    switch (event.key) {

        case "ArrowUp":
            socket.send("up")
            break
        case "ArrowDown":
            socket.send('down')
            break
        case "ArrowRight":
            socket.send('right')
            break
        case "ArrowLeft":
            socket.send('left')
            break
        case "/":
        case "Shift":
            socket.send("press")
            break
        case "1":
        case "2":
        case "3":
            socket.send(event.key)
            break
        case "\\":
            socket.send("reload")
            break
        default:
            console.log(event.key)
    }
})

function handleGesture() {
    var yDelta = touchendY - touchstartY
    var ypDelta = 0
    if (0 > yDelta) { ypDelta = yDelta * -1 } else { ypDelta = yDelta } // must be positive delta

    var xDelta = touchendX - touchstartX
    var xpDelta = 0
    if (0 > xDelta) { xpDelta = xDelta * -1 } else { xpDelta = xDelta } // must be positive delta

    //console.log(`x delta: ${xDelta}`)
    //console.log(`xp delta: ${xpDelta}`)
    //console.log(`y delta: ${yDelta}`)
    //console.log(`yp delta: ${ypDelta}`)

    if ((10 > xpDelta && 10 > ypDelta) || ypDelta == 0 || xpDelta == 0) {
        return // this is a click, not a swipe
    }

    if (xpDelta > ypDelta) { // user moved more horizontally than vertically, so count it as a horizontal movement
        // to be honest a LOT more apps need to do this check and it genuinely PMO when they dont!!!!!!!

        if (0 > xDelta) { // movement to the left
            socket.send('left')
        } else { // movement to the right
            socket.send('right')
        }

    } else { // opposite, more vertically than horizontal
        if (0 > yDelta) { // movement up
            socket.send('up')
        } else { // movement down
            socket.send('down')
        }
    }
}

function authenticate(u,p) {
    document.getElementById("login").setAttribute("disabled", true)
    sshIO.emit("authenticate", {"user": u, "pasw": p})

    var greetingIndex = getRandomIntInclusive(0, greetings.length)
    document.getElementById("welcome").innerHTML = greetings[greetingIndex].replace("#", u)
}

function showPlugins() {
    var plugins
    var folder = ""
    var colored = false

    // load plugins
    fetch("/active-plugins").then((response) => {
        if (response.ok) {
            return response.text()
        }
    }).then((response) => {
        plugins = JSON.parse(response)

        for (var i = 0; i < plugins.length; i++) {
            var plugin = plugins[i].replace("./plugins", "")

            var fileFolder = plugin.split("/")[1]

            console.log(`folder: ${folder}`)

            if (fileFolder != folder) {
                colored = !colored
                folder = fileFolder
            }

            var holder = document.createElement("tr")
            var text = document.createElement("td")
            text.innerHTML = plugin

            holder.appendChild(text)

            if (colored) {
                holder.style.backgroundColor = "#141414"
            } else {
                holder.style.backgroundColor = "transparent"
            }

            text.style.padding = "8px"

            document.getElementById("pfb").appendChild(holder)
        }
    })
}

function killChildren(element) {
    while (element.firstChild) {
        element.removeChild(element.firstChild);
    }
}

function showPayloads() {
    var payloads

    killChildren(document.getElementById("payloads"))

    // load payloads
    fetch("/available-payloads").then((response) => {
        if (response.ok) {
            return response.text()
        }
    }).then((response) => {
        payloads = JSON.parse(response)

        for (var i = 0; i < Object.keys(payloads).length; i++) {
            var payloadName = Object.keys(payloads)[i]
            var payloadSz = payloads[payloadName]

            var tableContainer = document.createElement("tr")
            var pnElement = document.createElement("td")
            var szElement = document.createElement("td")
            var xElement = document.createElement("td")
            var execute = document.createElement("button")

            pnElement.innerHTML = payloadName
            szElement.innerHTML = `${payloadSz}kb`

            execute.setAttribute("payload", payloadName)
            execute.innerHTML = "Execute"
            xElement.appendChild(execute)

            tableContainer.appendChild( pnElement )
            tableContainer.appendChild( szElement )
            tableContainer.appendChild( xElement )

            document.getElementById("payloads").appendChild(tableContainer)
        }
    })
}

function initialize() {
    canvas.addEventListener('touchstart', e => {
        touchstartY = e.changedTouches[0].screenY
        touchstartX = e.changedTouches[0].screenX
    })

    canvas.addEventListener('touchend', e => {
        touchendY = e.changedTouches[0].screenY
        touchendX = e.changedTouches[0].screenX

        if (canvasInputActive) {
            handleGesture()
        }
    })

    canvas.addEventListener('click', e => {
        e.stopPropagation()
        if (canvasInputActive) {
            socket.send("press")
        } else {
            canvasInputActive = true // canvas was clicked - we're now directing our input there
            document.body.style.overflow = "hidden"
            canvas.removeAttribute("blurry")
        }
    })

    document.addEventListener('click', function () {
        canvasInputActive = false
        canvas.setAttribute("blurry", true)
        document.body.style.overflow = "visible"
    })

    term.open(document.getElementById('terminal'));

    term.onData(e => {
        canvasInputActive = false
        if (e == "\r") {
            sshIO.emit("sshrx", { "byte": "\n", })
            return
        }

        sshIO.emit("sshrx", { "byte": e, })
    })

    setInterval(function () {
        sshIO.emit("sshreqtx")
    }, 50)

    setInterval(function() {
        sshIO.emit("reqsysinfo")
    }, 1000)

    showPlugins()
    showPayloads()
}

function getRandomIntInclusive(min, max) {
    min = Math.ceil(min)
    max = Math.floor(max)
    return Math.floor(Math.random() * (max - min + 1)) + min
  }

function manageAuth(code) {
    document.getElementById("pass").value = ""

    if (code == 2) {
        console.warn("incorrect password")
        document.getElementById("login").removeAttribute("disabled")

        document.getElementById("login-status").style.display = "block"

        return false
    } else if (code == 0) {
        initialize()

        document.getElementById("cover").setAttribute("hidden", true)
        return true
    }
}

function addFileDropHover(element_id, upload_id) {
    var element = document.getElementById(element_id)
    element.addEventListener("dragenter", e => {
        e.preventDefault();
        console.log("dragover")
        element.removeAttribute("hidden")
    })

    element.addEventListener("dragover", e => {
        e.preventDefault();
    })
    
    element.addEventListener("mouseleave", e => {
        // fuck you chrome
        console.log("no more file over me")
        element.setAttribute("hidden", true)
    })

    element.addEventListener("drop", ev => {
        ev.preventDefault()

        const dt = ev.dataTransfer;
        const file = dt.files[0];

        const fname = file.name
        const reader = new FileReader()
        reader.onload = (e) => {
            const data = btoa(e.target.result)
            sshIO.emit("upload", {"id": upload_id, "filename": fname, "data": data})
        }
        reader.readAsText(file)
    });
}

document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("login").addEventListener("click", function(){
        authenticate(
            document.getElementById("user").value,
            document.getElementById("pass").value
        )
    })
    document.getElementById("pass").addEventListener("keypress", e => {
        if (e.key == "Enter") {
            authenticate(
                document.getElementById("user").value,
                document.getElementById("pass").value
            )
        }
    })

    addFileDropHover("payload-hover", "payloads")
    document.getElementById("payload-hover").addEventListener("drop", e=>{
        setTimeout(function() {
            showPayloads()
        }, 100)
    })

    if ("geolocation" in navigator) {
        const watchID = navigator.geolocation.watchPosition((position) => {
            console.log(`lat: ${position.coords.latitude}  long: ${position.coords.longitude}`)
        });
    } else {
        /* geolocation IS NOT available */
    }
})

WSConnect()