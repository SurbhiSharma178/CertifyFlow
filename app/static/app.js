const form = document.getElementById("job-form");
const csvInput = document.getElementById("csv-file");
const dropZone = document.getElementById("drop-zone");
const fileMeta = document.getElementById("file-meta");
const formError = document.getElementById("form-error");
const generateBtn = document.getElementById("generate-btn");
const downloadSampleBtn = document.getElementById("download-sample");
const jobPanel = document.getElementById("job-panel");
const downloadZip = document.getElementById("download-zip");
const newJobBtn = document.getElementById("new-job-btn");

let selectedFile = null;
let activeJobId = null;
let polling = false;

function showError(message) {
  formError.textContent = message;
  formError.hidden = false;
}
function clearError() {
  formError.textContent = "";
  formError.hidden = true;
}
function setBusy(isBusy) {
  generateBtn.disabled = isBusy;
  generateBtn.querySelector(".button-label").textContent = isBusy ? "Creating generation job…" : "Generate certificates";
}
function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
function useFile(file) {
  clearError();
  if (!file) return;
  if (!file.name.toLowerCase().endsWith(".csv")) {
    selectedFile = null;
    csvInput.value = "";
    fileMeta.hidden = true;
    showError("Please choose a .csv file. Excel files are not supported yet.");
    return;
  }
  selectedFile = file;
  fileMeta.textContent = `${file.name} · ${formatBytes(file.size)}`;
  fileMeta.hidden = false;
}
csvInput.addEventListener("change", () => useFile(csvInput.files[0]));

["dragenter", "dragover"].forEach((name) => dropZone.addEventListener(name, (event) => {
  event.preventDefault();
  dropZone.classList.add("drag-over");
}));
["dragleave", "drop"].forEach((name) => dropZone.addEventListener(name, (event) => {
  event.preventDefault();
  dropZone.classList.remove("drag-over");
}));
dropZone.addEventListener("drop", (event) => {
  const file = event.dataTransfer?.files?.[0];
  if (!file) return;
  useFile(file);
  if (selectedFile) {
    try {
      const transfer = new DataTransfer();
      transfer.items.add(file);
      csvInput.files = transfer.files;
    } catch (_) { /* selectedFile remains available */ }
  }
});

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  const input = text.replace(/^\uFEFF/, "");

  for (let i = 0; i < input.length; i += 1) {
    const char = input[i];
    if (char === '"') {
      if (quoted && input[i + 1] === '"') {
        field += '"';
        i += 1;
      } else {
        quoted = !quoted;
      }
    } else if (char === "," && !quoted) {
      row.push(field.trim());
      field = "";
    } else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && input[i + 1] === "\n") i += 1;
      row.push(field.trim());
      if (row.some((cell) => cell !== "")) rows.push(row);
      row = [];
      field = "";
    } else {
      field += char;
    }
  }
  if (field.length || row.length) {
    row.push(field.trim());
    if (row.some((cell) => cell !== "")) rows.push(row);
  }
  if (quoted) throw new Error("The CSV contains an unclosed quoted field.");
  if (rows.length < 2) throw new Error("The CSV must contain a header row and at least one recipient.");

  const headers = rows[0].map((header) => header.trim().toLowerCase());
  const nameIndex = headers.indexOf("recipient_name");
  if (nameIndex === -1) throw new Error('The CSV header must include a column named "recipient_name".');

  const recipients = rows.slice(1)
    .map((cells) => ({ recipient_name: (cells[nameIndex] || "").trim() }))
    .filter((recipient) => recipient.recipient_name);
  if (!recipients.length) throw new Error("No recipient names were found in the CSV.");
  return recipients;
}

function setStatus(status) {
  const normalized = String(status || "Pending").toLowerCase();
  const label = normalized.charAt(0).toUpperCase() + normalized.slice(1);
  const pill = document.getElementById("job-status");
  pill.textContent = label;
  pill.className = `status-pill status-${normalized}`;
}
function renderProgress(data) {
  const total = Number(data.total ?? data.total_count ?? 0);
  const success = Number(data.success ?? 0);
  const failed = Number(data.failed ?? data.failure ?? 0);
  const processing = Number(data.processing ?? 0);
  const pending = Number(data.pending ?? 0);
  const progress = Math.max(0, Math.min(100, Number(data.progress_percentage ?? 0)));
  const processed = success + failed;

  document.getElementById("progress-value").textContent = `${progress}%`;
  document.getElementById("processed-count").textContent = `${processed} of ${total} processed`;
  document.getElementById("progress-fill").style.width = `${progress}%`;
  document.getElementById("progress-track").setAttribute("aria-valuenow", String(progress));
  document.getElementById("total-count").textContent = String(total);
  document.getElementById("success-count").textContent = String(success);
  document.getElementById("failed-count").textContent = String(failed);
  setStatus(data.status);

  const status = String(data.status || "").toLowerCase();
  const message = document.getElementById("job-message");
  if (status === "completed") {
    message.textContent = failed > 0
      ? `Finished with ${success} successful certificate(s) and ${failed} failure(s). Download the successful certificates below.`
      : `All ${success} certificate(s) generated successfully. Your ZIP is ready.`;
    downloadZip.hidden = success === 0;
  } else if (status === "failed") {
    message.textContent = "The job failed before completion. Check the server logs for details.";
    downloadZip.hidden = true;
  } else {
    message.textContent = `Generation is running. ${processing} processing and ${pending} waiting.`;
    downloadZip.hidden = true;
  }
  return status === "completed" || status === "failed";
}
async function pollJob(jobId) {
  if (polling) return;
  polling = true;
  try {
    while (activeJobId === jobId) {
      const response = await fetch(`/jobs/${jobId}/status`, { cache: "no-store" });
      if (!response.ok) {
        const detail = await response.text();
        throw new Error(`Could not get job status (${response.status}). ${detail}`);
      }
      const data = await response.json();
      if (renderProgress(data)) break;
      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
  } catch (error) {
    document.getElementById("job-message").textContent = error.message || "Unable to check generation status.";
  } finally {
    polling = false;
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();
  const file = selectedFile || csvInput.files[0];
  if (!file) return showError("Please select a CSV file first.");

  setBusy(true);
  downloadZip.hidden = true;
  try {
    const recipients = parseCsv(await file.text());
    const payload = {
      certificate_title: document.getElementById("certificate-title").value.trim(),
      event_name: document.getElementById("event-name").value.trim(),
      event_date: document.getElementById("event-date").value,
      issuer: document.getElementById("issuer").value.trim(),
      recipients
    };
    if (!payload.certificate_title || !payload.event_name || !payload.event_date || !payload.issuer) {
      throw new Error("Please complete all required certificate details.");
    }

    const response = await fetch("/jobs/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = result.detail;
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail || `Request failed (${response.status})`));
    }

    activeJobId = result.id ?? result.job_id;
    if (activeJobId == null) throw new Error("The server response did not include a job ID. Check JobResponseSchema.");

    document.getElementById("job-title").textContent = payload.event_name;
    document.getElementById("job-subtitle").textContent = `Job #${activeJobId} · ${recipients.length} recipient(s)`;
    document.getElementById("job-message").textContent = "Your generation job has been created.";
    document.getElementById("progress-value").textContent = "0%";
    document.getElementById("progress-fill").style.width = "0%";
    document.getElementById("progress-track").setAttribute("aria-valuenow", "0");
    document.getElementById("processed-count").textContent = `0 of ${recipients.length} processed`;
    document.getElementById("total-count").textContent = String(recipients.length);
    document.getElementById("success-count").textContent = "0";
    document.getElementById("failed-count").textContent = "0";
    setStatus(result.status || "Pending");
    downloadZip.href = `/jobs/${activeJobId}/download-all`;
    downloadZip.hidden = true;
    jobPanel.hidden = false;
    jobPanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
    pollJob(activeJobId);
  } catch (error) {
    showError(error.message || "Something went wrong while creating the job.");
  } finally {
    setBusy(false);
  }
});

downloadSampleBtn.addEventListener("click", () => {
  const blob = new Blob(["recipient_name\nAarav Sharma\nMeera Patel\nKabir Singh\n"], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "recipients_sample.csv";
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
});

newJobBtn.addEventListener("click", () => {
  activeJobId = null;
  form.reset();
  selectedFile = null;
  fileMeta.hidden = true;
  jobPanel.hidden = true;
  downloadZip.hidden = true;
  clearError();
  window.scrollTo({ top: 0, behavior: "smooth" });
});
