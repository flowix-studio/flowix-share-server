
function register() {
    fetch("/register", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            "id": document.querySelector("#username").value,
            "pw": document.querySelector("#password").value
        })
    }).then(resp => {
        resp.json().then(data => {
            if (data["state"] == "success") {
                window.location.href = "/login";
            }
            else {
                window.alert(data["message"]);
            }
        });
    });
}
