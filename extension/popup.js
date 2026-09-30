const BACKEND_HEALTH_URL = "http://127.0.0.1:8000/health";
const CONNECT_ERROR = "Mamoru could not connect to the local safety service.";

const statusEl = document.getElementById("status");
const phraseEl = document.getElementById("phrase");
const messageEl = document.getElementById("message");
const protectButton = document.getElementById("protect-me");

function setInactive() {
  statusEl.textContent = "INACTIVE";
  statusEl.classList.remove("active");
  protectButton.disabled = false;
}

function setActive(phrase) {
  statusEl.textContent = "ACTIVE";
  statusEl.classList.add("active");
  phraseEl.textContent = phrase;
  protectButton.disabled = true;
}

function showMessage(text, isError) {
  messageEl.textContent = text;
  messageEl.classList.toggle("error", Boolean(isError));
}

async function checkBackend() {
  const response = await fetch(BACKEND_HEALTH_URL);

  if (!response.ok) {
    throw new Error("Backend returned an error.");
  }

  return response.json();
}

protectButton.addEventListener("click", async () => {
  // User-initiated only. This still does not read the webpage.
  setActive("任せて。");
  showMessage("Checking the local safety service...", false);

  try {
    const data = await checkBackend();
    phraseEl.textContent = "終わった。";
    showMessage(data.message || "Mamoru backend is running.", false);
  } catch (error) {
    phraseEl.textContent = "注意して。";
    showMessage(CONNECT_ERROR, true);
  }

  setInactive();
});

setInactive();
