const form = document.getElementById("bpm-form");
const audioInput = document.getElementById("audio");
const fileName = document.getElementById("file-name");
const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const variationsEl = document.getElementById("variations");
const dropzone = document.getElementById("dropzone");
const submitBtn = document.getElementById("submit");

function setFileName(name) {
  fileName.textContent = name || "Aucun fichier selectionne";
}

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.style.color = isError ? "#c0392b" : "";
}

function setResult(message) {
  resultEl.textContent = message;
}

function renderVariations(segments) {
  variationsEl.innerHTML = "";
  if (!segments || segments.length === 0) {
    return;
  }

  if (segments.length === 1) {
    variationsEl.textContent = "Tempo stable sur toute la duree.";
    return;
  }

  const title = document.createElement("div");
  title.textContent = "Variations detectees:";
  const list = document.createElement("ul");

  segments.forEach((seg) => {
    const item = document.createElement("li");
    item.textContent = `${seg.start}s - ${seg.end}s : ${seg.bpm} BPM`;
    list.appendChild(item);
  });

  variationsEl.appendChild(title);
  variationsEl.appendChild(list);
}

function setLoading(isLoading) {
  submitBtn.disabled = isLoading;
  submitBtn.querySelector(".btn-text").textContent = isLoading
    ? "Analyse en cours..."
    : "Analyser le BPM";
}

audioInput.addEventListener("change", (event) => {
  const file = event.target.files?.[0];
  setFileName(file ? file.name : "");
  setResult("");
  variationsEl.textContent = "";
  setStatus("");
});

dropzone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropzone.classList.add("is-dragover");
});

dropzone.addEventListener("dragleave", () => {
  dropzone.classList.remove("is-dragover");
});

dropzone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropzone.classList.remove("is-dragover");
  const file = event.dataTransfer.files?.[0];
  if (!file) {
    return;
  }
  const transfer = new DataTransfer();
  transfer.items.add(file);
  audioInput.files = transfer.files;
  setFileName(file.name);
  setResult("");
  variationsEl.textContent = "";
  setStatus("");
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  setResult("");
  variationsEl.textContent = "";

  const file = audioInput.files?.[0];
  if (!file) {
    setStatus("Ajoute un fichier audio pour lancer l'analyse.", true);
    return;
  }

  setLoading(true);
  setStatus("Analyse du tempo en cours...");

  try {
    const formData = new FormData(form);
    const response = await fetch("/api/analyze", {
      method: "POST",
      body: formData,
    });
    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.error || "Erreur inconnue");
    }

    setStatus("Analyse terminee.");
    setResult(`BPM estime : ${payload.bpm} (SR ${payload.sample_rate} Hz)`);
    renderVariations(payload.segments);
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    setLoading(false);
  }
});
