/* MedScribe AI — Frontend Application Logic */

const SAMPLE_PATIENT = `Patient ID: PT-20241115
Name: James Okonkwo
Age: 58, Male
Attending: Dr. Adaeze Nwosu
Ward: Cardiology, Bed 4B
Admission: 2024-11-10
Discharge: 2024-11-15

CHIEF COMPLAINT:
Chest pain and shortness of breath for 6 hours prior to admission.

HISTORY OF PRESENTING ILLNESS:
58-year-old male with known hypertension and type 2 diabetes mellitus presented to A&E with
sudden onset crushing central chest pain radiating to the left arm, diaphoresis, and dyspnoea.
ECG showed ST-elevation in leads V2–V5. Troponin I elevated at 4.2 ng/mL.
Patient was thrombolysed with alteplase and transferred to cathlab.

PAST MEDICAL HISTORY:
- Hypertension (10 years)
- Type 2 Diabetes Mellitus (7 years)
- Hyperlipidaemia

ALLERGIES: Penicillin (rash), NSAIDs (GI bleed)

VITAL SIGNS ON ADMISSION:
BP: 162/98 mmHg, HR: 102 bpm, Temp: 37.2°C, SpO2: 94% on room air, RR: 22/min

INVESTIGATIONS:
- Troponin I: 4.2 ng/mL (elevated)
- ECG: ST elevation V2–V5
- Echo: EF 42%, anterior wall hypokinesia
- FBC: Hb 12.8, WBC 11.2, Plt 210
- RFT: Creatinine 98 umol/L, eGFR 68
- HbA1c: 8.4%
- LFTs: Normal
- CXR: Mild pulmonary congestion

PROCEDURES:
- Primary PCI with drug-eluting stent to LAD (2024-11-10)
- Continuous cardiac monitoring throughout admission
- Echocardiography (2024-11-12)

MEDICATIONS ADMINISTERED DURING ADMISSION:
- Aspirin 300mg loading, then 75mg daily
- Clopidogrel 600mg loading, then 75mg daily
- Atorvastatin 80mg nocte
- Metoprolol 25mg BD
- Ramipril 2.5mg OD (started day 3)
- Enoxaparin 80mg SC BD (for 48 hours)
- Insulin sliding scale
- Metformin held during admission

HOSPITAL COURSE:
Patient underwent successful primary PCI. Post-procedure troponin peaked at 18.6 ng/mL.
Cardiac monitoring showed occasional PVCs, no sustained arrhythmia. Echo on day 3 showed
EF of 42% with mild anterior hypokinesia. Cardiac rehab team reviewed. Patient clinically
improved, chest pain resolved, haemodynamically stable by day 4. Diabetes team adjusted
insulin regimen. Patient discharged day 5 in stable condition.`;

let currentJobId = null;
let pollInterval = null;

// ── DOM references ─────────────────────────────────────────────────────────

const inputSection    = document.getElementById("input-section");
const progressSection = document.getElementById("progress-section");
const resultsSection  = document.getElementById("results-section");
const errorSection    = document.getElementById("error-section");

const btnSubmit    = document.getElementById("btn-submit");
const btnLoadSample= document.getElementById("btn-load-sample");
const btnNew       = document.getElementById("btn-new");
const btnCopy      = document.getElementById("btn-copy");
const btnRetry     = document.getElementById("btn-retry");

const patientDataEl = document.getElementById("patient-data");
const patientIdEl   = document.getElementById("patient-id");
const progressBar   = document.getElementById("progress-bar");
const progressLabel = document.getElementById("progress-label");
const summaryText   = document.getElementById("summary-text");
const reportText    = document.getElementById("report-text");
const filesList     = document.getElementById("files-list");
const errorMessage  = document.getElementById("error-message");
const qaBadge       = document.getElementById("qa-badge");

// ── Event listeners ────────────────────────────────────────────────────────

btnLoadSample.addEventListener("click", () => {
  patientDataEl.value = SAMPLE_PATIENT;
  patientIdEl.value   = "PT-20241115";
});

btnSubmit.addEventListener("click", submitJob);

btnNew.addEventListener("click", resetToInput);
btnRetry.addEventListener("click", resetToInput);

btnCopy.addEventListener("click", () => {
  navigator.clipboard.writeText(summaryText.textContent)
    .then(() => { btnCopy.textContent = "Copied!"; setTimeout(() => { btnCopy.textContent = "Copy Summary"; }, 2000); })
    .catch(() => alert("Could not copy to clipboard."));
});

document.querySelectorAll(".tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => { c.classList.remove("active"); c.classList.add("hidden"); });
    tab.classList.add("active");
    const target = document.getElementById("tab-" + tab.dataset.tab);
    target.classList.add("active");
    target.classList.remove("hidden");
  });
});

// ── Core functions ─────────────────────────────────────────────────────────

async function submitJob() {
  const patientData = patientDataEl.value.trim();
  const patientId   = patientIdEl.value.trim() || "PATIENT";

  if (!patientData) { alert("Please paste patient clinical notes before submitting."); return; }
  if (patientData.length < 50) { alert("Notes are too short. Please provide complete clinical notes."); return; }

  btnSubmit.disabled = true;
  showSection(progressSection);

  try {
    const res = await fetch("/api/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ patient_data: patientData, patient_id: patientId }),
    });
    const data = await res.json();
    if (!res.ok) { throw new Error(data.error || "Submission failed"); }
    currentJobId = data.job_id;
    startPolling();
  } catch (err) {
    showError(err.message);
  }
}

function startPolling() {
  let elapsed = 0;
  setProgress(5, "Clinical Analyst extracting structured data...");
  setStepActive(1);

  pollInterval = setInterval(async () => {
    elapsed += 3;
    // Animate progress steps based on elapsed time (each task ~30s avg)
    animateProgress(elapsed);

    try {
      const res = await fetch(`/api/status/${currentJobId}`);
      const data = await res.json();
      if (!res.ok) { throw new Error(data.error || "Status check failed"); }

      if (data.status === "complete") {
        clearInterval(pollInterval);
        if (data.result.success) {
          setProgress(100, "Complete!");
          markAllDone(data.result.tasks);
          setTimeout(() => showResults(data.result), 600);
        } else {
          showError(data.result.report || "Pipeline failed.");
        }
      }
    } catch (err) {
      clearInterval(pollInterval);
      showError(err.message);
    }
  }, 3000);
}

function animateProgress(elapsed) {
  // Roughly 30s per agent step; animate UI accordingly
  const step = Math.min(Math.floor(elapsed / 28) + 1, 5);
  const pct   = Math.min(5 + elapsed * 1.6, 92);
  const labels = [
    "Clinical Analyst extracting structured data...",
    "Discharge Planner building care plan...",
    "Medical Writer composing summary...",
    "QA Reviewer auditing documentation...",
    "Code Engineer generating implementation...",
  ];
  for (let i = 1; i <= step; i++) {
    if (i < step) setStepDone(i);
    else setStepActive(i);
  }
  setProgress(pct, labels[step - 1] || "Finalising...");
}

function markAllDone(tasks) {
  tasks.forEach((t, i) => {
    if (t.success) setStepDone(i + 1);
    else setStepFailed(i + 1);
  });
}

function showResults(result) {
  showSection(resultsSection);

  summaryText.textContent = result.discharge_summary || "(no summary generated)";
  reportText.textContent  = result.report || "";

  // QA badge
  if (result.qa_approved) {
    qaBadge.textContent  = `QA Approved — Score ${result.qa_score}/100`;
    qaBadge.className    = "qa-badge approved";
  } else {
    qaBadge.textContent  = `QA Score ${result.qa_score}/100 — Review Required`;
    qaBadge.className    = "qa-badge rejected";
  }

  // Files list
  filesList.innerHTML = "";
  (result.files || []).forEach(f => {
    const li  = document.createElement("li");
    const ext = f.split(".").pop();
    const icon = ext === "json" ? "{ }" : ext === "py" ? "Py" : ext === "txt" ? "TXT" : "FILE";
    li.innerHTML = `<span class="file-icon">${icon}</span><code>${f}</code>`;
    filesList.appendChild(li);
  });
}

function showError(message) {
  showSection(errorSection);
  errorMessage.textContent = message;
  btnSubmit.disabled = false;
}

function resetToInput() {
  clearInterval(pollInterval);
  currentJobId = null;
  btnSubmit.disabled = false;
  resetSteps();
  setProgress(0, "");
  showSection(inputSection);
}

// ── UI helpers ─────────────────────────────────────────────────────────────

function showSection(el) {
  [inputSection, progressSection, resultsSection, errorSection].forEach(s => s.classList.add("hidden"));
  el.classList.remove("hidden");
}

function setProgress(pct, label) {
  progressBar.style.width = pct + "%";
  if (label) progressLabel.textContent = label;
}

function setStepActive(n) { setStepClass(n, "active", "Running..."); }
function setStepDone(n)   { setStepClass(n, "done",   "Done"); }
function setStepFailed(n) { setStepClass(n, "failed", "Failed"); }

function setStepClass(n, cls, statusText) {
  const step   = document.getElementById(`step-${n}`);
  const status = document.getElementById(`status-${n}`);
  if (!step) return;
  step.className = `pipeline-step ${cls}`;
  status.textContent = statusText;
}

function resetSteps() {
  for (let i = 1; i <= 5; i++) {
    const step   = document.getElementById(`step-${i}`);
    const status = document.getElementById(`status-${i}`);
    if (step)   step.className = "pipeline-step";
    if (status) status.textContent = "Waiting...";
  }
}
