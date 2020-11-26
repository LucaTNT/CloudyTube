function submitForm(form) {
    let use_env_credentials = document.getElementById("username").checked
    let username = document.getElementById("username").value
    let password = document.getElementById("password").value
    let video_url = document.getElementById("video_url").value
    
    document.getElementById("form").style.display = "none"
    
    setStatusText("🚀 Sending data…")
    var request = new XMLHttpRequest()
    request.open("POST", "/api/v1/job")

    request.onreadystatechange = function() {
        console.log(request.readyState)
        if(request.readyState == XMLHttpRequest.DONE && [200, 400].includes(request.status)) {
            data = JSON.parse(request.responseText)
            if (data["status"] == "created") {
                startPolling(data);
            }
            if (data["status"] == "error") {
                setError(data["error"])
            }
        }
    }

    request.send(new FormData(form))

    return false
}

function setError(error_text) {
    document.getElementById("form").style.display = "block"
    setStatusText(`❌ Error: ${error_text}`)
}

function resetForm() {
    document.getElementById("form").style.display = "block"
    document.getElementById("video_url").value = ""
}

function getStatus() {
    var request = new XMLHttpRequest()
    request.open("GET", `/api/v1/status/${data["status_id"]}`)

    request.onreadystatechange = function() {
        if(request.readyState == 4 && [200, 400].includes(request.status)) {
            response = JSON.parse(request.responseText)
            console.log(request.responseText);
            switch (response["status"]) {
                case "downloading":
                    setStatusText("⏬ Download in progress… " + response["progress"])
                    break;
                case "converting":
                    setStatusText("🔄 Converting audio…")
                    break;
                case "uploading":
                    setStatusText("⏫ Uploading audio…")
                    break;
                case "error":
                    setError(response["error_text"])
                    clearInterval(pollingProcess)
                    break;
                case "done":
                    setStatusText("Done ✅")
                    resetForm()
                    clearInterval(pollingProcess)
                    break;
            }
        }
    }

    request.send()
}

function setStatusText(text) {
    document.getElementById("status").innerText = text;
}

function startPolling(data) {
    try {
        pollingProcess = setInterval(getStatus, 250)
    } catch (e) {
        console.log(e)
    }
}

function setCredentialsField(enabled) {
    document.getElementById("username").disabled = !enabled
    document.getElementById("password").disabled = !enabled
}

document.getElementById("use_env_credentials").addEventListener('change', function() {
    setCredentialsField(!this.checked)
  });