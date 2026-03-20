// script.js
// Vanilla JS handling API connectivity and DOM modifications.

function showToast(message, type = "success") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast toast--${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    // Trigger visual pop in
    requestAnimationFrame(() => {
        toast.classList.add("toast--visible");
    });

    // Remove neatly after delay
    setTimeout(() => {
        toast.classList.remove("toast--visible");
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Upload Handling & Analysis Fetch
async function analyzeResume(e) {
    if (e) e.preventDefault();
    const fileInput = document.getElementById("resumeFile");
    const jdEl = document.getElementById("jdText");
    const analyzeButton = document.getElementById("analyzeButton");

    if (!fileInput || !jdEl || !analyzeButton) return;
    if (analyzeButton.disabled || analyzeButton.classList.contains("is-loading")) return;

    const jdText = jdEl.value.trim();
    if (!fileInput.files[0] || !jdText) {
        showToast("Please upload a resume and paste the job description.", "error");
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    formData.append("jd", jdText);

    // Visual locking
    analyzeButton.disabled = true;
    analyzeButton.classList.add("is-loading");
    analyzeButton.textContent = "Analyzing…";

    showToast("Running AI analysis...", "info");

    try {
        const response = await fetch("http://127.0.0.1:8000/score-resume/", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Server error (${response.status})`);
        }

        const data = await response.json();
        
        // Cache to Session
        sessionStorage.setItem("analysisResult", JSON.stringify(data));
        localStorage.setItem("analysisResult", JSON.stringify(data));
        
        showToast("Analysis complete. Loading dashboard…", "success");
        setTimeout(() => {
            window.location.href = "dashboard.html";
        }, 500);
    } catch (err) {
        console.error(err);
        showToast("Error connecting to backend: " + err.message, "error");
    } finally {
        analyzeButton.disabled = false;
        analyzeButton.classList.remove("is-loading");
        analyzeButton.textContent = "Run Analysis";
    }
}

// Init Landing Drag/drop UI setup
function initLandingPage() {
    const fileInput = document.getElementById("resumeFile");
    const fileNameDisplay = document.getElementById("resumeFileName");
    const dropZone = document.getElementById("fileDropZone");
    const analyzeButton = document.getElementById("analyzeButton");

    if (analyzeButton) {
        analyzeButton.addEventListener("click", analyzeResume);
    }

    if (fileInput && fileNameDisplay) {
        fileInput.addEventListener("change", () => {
            const file = fileInput.files[0];
            if (file) {
                fileNameDisplay.textContent = file.name;
                fileNameDisplay.classList.add("has-file");
            } else {
                fileNameDisplay.textContent = "No file selected yet";
                fileNameDisplay.classList.remove("has-file");
            }
        });
    }

    if (dropZone && fileInput) {
        ["dragenter", "dragover"].forEach(evt =>
            dropZone.addEventListener(evt, e => {
                e.preventDefault();
                dropZone.classList.add("is-dragging");
            })
        );

        ["dragleave", "drop"].forEach(evt =>
            dropZone.addEventListener(evt, e => {
                e.preventDefault();
                dropZone.classList.remove("is-dragging");
            })
        );

        dropZone.addEventListener("drop", e => {
            const files = e.dataTransfer?.files;
            if (files && files[0]) {
                const dt = new DataTransfer();
                dt.items.add(files[0]);
                fileInput.files = dt.files;
                fileInput.dispatchEvent(new Event("change"));
            }
        });

        dropZone.addEventListener("click", () => fileInput.click());
    }
}

// Populating Dashboard UI with session cache metrics
function initDashboardPage() {
    const loading = document.getElementById("dashboardLoading");
    const content = document.getElementById("dashboardContent");
    const sessionInfo = document.getElementById("sidebarSessionInfo");

    const stored = sessionStorage.getItem("analysisResult") || localStorage.getItem("analysisResult");
    
    if (!stored) {
        if (loading) loading.classList.add("hidden");
        if (content) {
            content.classList.remove("hidden");
            content.innerHTML = '<div style="grid-column: 1 / -1; text-align: center; padding: 6rem 2rem;"><p class="text-muted" style="margin-bottom: 1.5rem;">No active analysis found. Run a new scan from the landing page.</p><a href="index.html#upload" class="btn btn-primary">Go to Upload</a></div>';
        }
        if (sessionInfo) sessionInfo.textContent = "No session active";
        return;
    }

    let data;
    try {
        data = JSON.parse(stored);
    } catch {
        if (sessionInfo) sessionInfo.textContent = "Format error in memory";
        return;
    }

    if (sessionInfo) {
        sessionInfo.textContent = "Session: Active";
    }

    if (loading) loading.classList.add("hidden");
    if (content) content.classList.remove("hidden");

    // Populate Score
    const atsScore = Math.round(data.overall_match ?? 0);
    const confidence = Math.round(data.confidence_score ?? 0);

    const circle = document.querySelector(".circle-score-fill");
    const valueEl = document.getElementById("atsScoreValue");
    
    if (circle && valueEl) {
        const radius = 48;
        const circumference = 2 * Math.PI * radius;
        const offset = circumference - (atsScore / 100) * circumference;
        circle.style.strokeDasharray = `${circumference} ${circumference}`;
        circle.style.strokeDashoffset = `${circumference}`; // start hidden
        
        let currentScore = 0;
        const step = atsScore > 0 ? Math.max(1, Math.floor(atsScore / 30)) : 1;
        const timer = setInterval(() => {
            currentScore += step;
            if (currentScore >= atsScore) {
                currentScore = atsScore;
                clearInterval(timer);
            }
            valueEl.textContent = currentScore;
        }, 30);

        // Animate stroke smoothly
        requestAnimationFrame(() => {
            circle.style.strokeDashoffset = `${offset}`;
        });
    }

    // Set Level indicators
    const matchLevel = document.getElementById("pillMatchLevel");
    const confidencePill = document.getElementById("pillConfidence");
    if (matchLevel) {
        let label = "Low Match";
        let cls = "text-muted";
        
        if (atsScore >= 80) { label = "Strong Match"; cls = "text-success"; }
        else if (atsScore >= 60) { label = "Avg Match"; cls = "text-warning"; }
        
        matchLevel.textContent = label;
        matchLevel.className = `tag tag-soft ${cls}`;
    }
    if (confidencePill) {
        confidencePill.textContent = `Conf: ${confidence}%`;
    }

    // Insert Candidate Summary text
    const summaryEl = document.getElementById("candidateSummaryText");
    if (summaryEl) {
        summaryEl.textContent = data.summary || "No specific summary provided from AI engine.";
    }

    // Insert Skills
    const skillsContainer = document.getElementById("skillsContainer");
    if (skillsContainer) {
        const skills = data.matched_skills || [];
        if (!skills.length) {
            skillsContainer.innerHTML = '<span class="empty-state-text">No skills successfully detected.</span>';
        } else {
            skillsContainer.innerHTML = skills
                .map(skill => `<span class="chip">${skill}</span>`)
                .join("");
        }
    }

    // Split Keywords Matched and Missing
    const matched = document.getElementById("keywordsMatched");
    const missing = document.getElementById("keywordsMissing");
    if (matched) {
        const arr = data.matched_keywords || data.matched_skills || [];
        matched.innerHTML = arr.length
            ? arr.map(k => `<span class="chip chip-soft">${k}</span>`).join("")
            : '<span class="empty-state-text">None detected.</span>';
    }
    if (missing) {
        const arr = data.missing_keywords || data.critical_gaps || [];
        missing.innerHTML = arr.length
            ? arr.map(k => `<span class="chip chip-warning">${k}</span>`).join("")
            : '<span class="empty-state-text">None indicated.</span>';
    }

    // Alternative Job Matches rendering
    const jobsEl = document.getElementById("jobMatches");
    if (jobsEl) {
        const roles = data.job_matches || [];
        if (!roles.length) {
            jobsEl.innerHTML = '<p class="empty-state-text">No alternative roles found.</p>';
        } else {
            jobsEl.innerHTML = roles
                .slice(0, 3)
                .map(
                    r => `
                <article class="job-card">
                    <div>
                        <h4>${r.title}</h4>
                        <p class="text-muted">${r.location || "Flexible / Remote"}</p>
                    </div>
                    <div class="job-card-score">
                        <span>${Math.round(r.match || 0)}%</span>
                    </div>
                </article>`
                )
                .join("");
        }
    }
}

function initResultsPage() {
    const resultsContainer = document.getElementById("results");
    const stored = sessionStorage.getItem("analysisResult") || localStorage.getItem("analysisResult");
    
    if (!stored) {
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="card" style="text-align: center; padding: 4rem 2rem;">
                    <h3 class="text-muted" style="margin-bottom: 0.5rem;">No analysis found</h3>
                    <p class="text-muted" style="margin-bottom: 1.5rem;">Please go back and analyze a resume to see the detailed JSON results here.</p>
                    <a href="index.html#upload" class="btn btn-primary">Go to Upload</a>
                </div>
            `;
        }
        return;
    }

    try {
        const data = JSON.parse(stored);
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="card" style="margin-bottom: 1.5rem;">
                    <h3>Latest Analysis Data</h3>
                    <div style="background: var(--surface-soft); padding: 1.5rem; border-radius: var(--radius-md); font-family: monospace; font-size: 0.875rem; overflow-x: auto; white-space: pre-wrap; color: var(--text-secondary); border: 1px solid var(--border);">
${JSON.stringify(data, null, 2)}
                    </div>
                </div>
            `;
        }
    } catch (e) {
        if (resultsContainer) {
            resultsContainer.innerHTML = `<p class="text-error">Could not load analysis results.</p>`;
        }
    }
}

// Router trigger based on embedded data-page attribute
document.addEventListener("DOMContentLoaded", () => {
    const page = document.body.getAttribute("data-page");
    if (page === "landing") {
        initLandingPage();
    } else if (page === "dashboard") {
        initDashboardPage();
    } else if (page === "results") {
        initResultsPage();
    }
});