
window.addEventListener("DOMContentLoaded", () => {
    const tokensTBody = document.querySelector("#tokens_tbody");
    const sharedTBody = document.querySelector("#shared_tbody");

    window.setInterval(() => {
        fetch("/board", {
            method: "POST"
        }).then(response => {
            response.json().then(data => {
                var tokens_html = "";
                for (var row of data["token_list"]) {
                    tokens_html += `<tr><td>${row[0]}</td><td>${row[1]}</td></tr>`;
                }
                tokensTBody.innerHTML = tokens_html;

                var shared_html = "";
                for (var row of data["shared_list"]) {
                    shared_html += `<tr><td>${row[0]}</td><td>${row[1]}</td><td>${row[2]}</td><td>${row[3]}</td><td>**********</td></tr>`;
                }
                sharedTBody.innerHTML = shared_html;
            });
        });
    }, 100);
});
