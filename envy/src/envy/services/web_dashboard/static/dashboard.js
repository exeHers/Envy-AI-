const SECRET_HEADER = "x-envy-secret";
const SECRET_VALUE = window.ENVY_SECRET || "change-me-envy";

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      ...(options.headers || {}),
      [SECRET_HEADER]: SECRET_VALUE,
      "Content-Type": "application/json",
    },
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

async function refreshStatus() {
  try {
    const status = await fetchJson("/api/status");
    const container = document.getElementById("status-grid");
    container.innerHTML = "";
    Object.entries(status).forEach(([name, info]) => {
      const card = document.createElement("div");
      card.className = `status-card ${info.status === "up" ? "status-up" : "status-down"}`;
      card.innerHTML = `
        <h3>${name}</h3>
        <p>Status: ${info.status}</p>
        <pre>${JSON.stringify(info.details, null, 2)}</pre>
      `;
      container.appendChild(card);
    });
  } catch (error) {
    console.error("Status fetch failed", error);
  }
}

async function refreshSessions() {
  try {
    const data = await fetchJson("/api/sessions");
    const tbody = document.getElementById("sessions-body");
    tbody.innerHTML = "";
    (data.sessions || []).slice(-10).reverse().forEach((session) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${session.session_id}</td>
        <td>${session.intent || "—"}</td>
        <td>${session.skill || "—"}</td>
        <td>${session.transcript || ""}</td>
        <td>${session.status}</td>
      `;
      tbody.appendChild(row);
    });
  } catch (error) {
    console.error("Sessions fetch failed", error);
  }
}

async function refreshLogs() {
  try {
    const logs = await fetchJson("/api/logs");
    const target = document.getElementById("logs-output");
    target.textContent = (logs.entries || []).join("\n");
  } catch (error) {
    console.error("Log fetch failed", error);
  }
}

async function submitConfirmation(event) {
  event.preventDefault();
  const actionId = document.getElementById("action-id").value;
  const channel = document.getElementById("channel").value;
  const resultBox = document.getElementById("confirm-result");
  try {
    const result = await fetchJson("/api/confirm", {
      method: "POST",
      body: JSON.stringify({ action_id: actionId, channel }),
    });
    resultBox.textContent = JSON.stringify(result, null, 2);
  } catch (error) {
    resultBox.textContent = `Error: ${error.message}`;
  }
}

document.getElementById("confirm-form").addEventListener("submit", submitConfirmation);

refreshStatus();
refreshSessions();
refreshLogs();

setInterval(refreshStatus, 5000);
setInterval(refreshSessions, 7000);
setInterval(refreshLogs, 10000);
