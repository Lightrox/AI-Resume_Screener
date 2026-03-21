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
    analyzeButton.textContent = "Analyzing...";

    showToast("Running AI analysis...", "info");

    try {
        const response = await fetch("https://ai-resume-screener-9cbi.onrender.com/score-resume/", {
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

        showToast("Analysis complete. Loading dashboard...", "success");
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

    const stored = sessionStorage.getItem("analysisResult") || localStorage.getItem("analysisResult");

    if (!stored) {
        if (loading) loading.classList.add("hidden");
        if (content) {
            content.classList.remove("hidden");
            content.style.display = "block";
            content.innerHTML = '<div style="grid-column: 1 / -1; text-align: center; padding: 6rem 2rem;"><p class="text-muted" style="margin-bottom: 1.5rem;">No active analysis found. Run a new scan from the landing page.</p><a href="index.html#upload" class="btn btn-primary">Go to Upload</a></div>';
        }
        return;
    }

    let data;
    try {
        data = JSON.parse(stored);
    } catch {
        return;
    }

    if (loading) loading.classList.add("hidden");
    if (content) content.classList.remove("hidden");

    // Populate Mentorship Panel (Top)
    const rec = data.match_level || "Moderate Match";
    const readiness = data.job_readiness || "Partially Ready";

    let statusCls = "status-consider";
    let badgeCls = "badge-consider";
    let icon = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>';

    if (rec === "Low Match") {
        statusCls = "status-reject";
        badgeCls = "badge-reject";
        icon = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>';
    } else if (rec === "High Match") {
        statusCls = "status-strong";
        badgeCls = "badge-strong";
        icon = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>';
    }

    const panel = document.getElementById("decisionPanelCard");
    const badge = document.getElementById("decisionBadge");
    const readinessBadge = document.getElementById("jobReadinessBadge");

    if (panel) panel.className = `card decision-panel ${statusCls}`;
    if (badge) {
        badge.className = `decision-badge ${badgeCls}`;
        badge.innerHTML = `${icon} ${rec}`;
    }
    if (readinessBadge) {
        readinessBadge.textContent = readiness;
        if (readiness === "Not Ready") readinessBadge.style.color = "var(--error)";
        else if (readiness === "Ready") readinessBadge.style.color = "var(--success)";
        else readinessBadge.style.color = "var(--warning)";
    }

    // Intelligence mapping
    const structuredSum = data.structured_summary || {};
    if (document.getElementById("studentStrength")) document.getElementById("studentStrength").textContent = structuredSum.strength || "N/A";
    if (document.getElementById("matchInterpretation")) document.getElementById("matchInterpretation").textContent = structuredSum.interpretation || "N/A";
    if (document.getElementById("motivationalFeedbackText")) document.getElementById("motivationalFeedbackText").textContent = structuredSum.motivational_feedback || "";

    if (document.getElementById("progressFeel")) {
        const pf = structuredSum.progress_feel || "";
        document.getElementById("progressFeel").textContent = pf;
        if (pf.includes("excellent") || pf.includes("fantastic")) document.getElementById("progressFeel").classList.add("text-success");
        else document.getElementById("progressFeel").classList.add("text-muted");
    }

    if (document.getElementById("bestFitRole")) document.getElementById("bestFitRole").textContent = data.best_fit_role || "N/A";
    if (document.getElementById("altFitRole")) document.getElementById("altFitRole").textContent = data.alternate_role || "N/A";
    if (document.getElementById("expAssessment")) document.getElementById("expAssessment").textContent = data.experience_assessment || "N/A";

    if (document.getElementById("infraAssessment")) {
        document.getElementById("infraAssessment").textContent = data.infra_assessment || "Adequate";
        if (data.infra_assessment === "Very Low" || data.infra_assessment === "Low") {
            document.getElementById("infraAssessment").style.color = "var(--error)";
        } else if (data.infra_assessment === "Entry-Level (No Cloud/Containers)") {
            document.getElementById("infraAssessment").style.color = "var(--warning)";
        } else {
            document.getElementById("infraAssessment").style.color = "var(--success)";
        }
    }

    if (document.getElementById("coreCoverage")) {
        document.getElementById("coreCoverage").textContent = (data.core_coverage ?? "0") + "%";
    }

    // Populate Secondary Component Scores
    const atsScore = Math.round(data.ats_score || data.overall_match || 0);
    const circle = document.querySelector(".circle-score-fill");
    const valueEl = document.getElementById("atsScoreValue");

    if (circle && valueEl) {
        const radius = 48;
        const circumference = 2 * Math.PI * radius;
        const offset = circumference - (atsScore / 100) * circumference;
        circle.style.strokeDasharray = `${circumference} ${circumference}`;
        circle.style.strokeDashoffset = `${circumference}`;

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
        requestAnimationFrame(() => circle.style.strokeDashoffset = `${offset}`);
    }

    const breakdownContainer = document.getElementById("categoryBreakdown");
    if (breakdownContainer && data.category_scores) {
        let html = "";
        for (const [catName, score] of Object.entries(data.category_scores)) {
            html += `
            <div class="cat-row">
                <div class="cat-header">
                    <span>${catName}</span>
                    <span>${score}%</span>
                </div>
                <div class="cat-bar-bg">
                    <div class="cat-bar-fill" style="width: ${score}%;"></div>
                </div>
            </div>`;
        }
        breakdownContainer.innerHTML = html;
    }

    // Missing Skill Impacts & Improvements (List Format)
    const impactContainer = document.getElementById("educationalImpactsContainer");
    if (impactContainer) {
        const roadmap = data.roadmap_sequence || [];

        if (!roadmap.length) {
            impactContainer.innerHTML = '<span class="empty-state-text" style="font-size:0.875rem;">Your resume meets the key foundational skills for this role!</span>';
        } else {
            let html = "";
            for (let i = 0; i < roadmap.length; i++) {
                const step = roadmap[i];
                let priorityColor = "var(--text-secondary)";
                if (step.priority === "High Priority") priorityColor = "var(--error)";
                else if (step.priority === "Medium Priority") priorityColor = "var(--warning)";
                else priorityColor = "var(--primary)"; // Bonus

                html += `
                <li style="border-left: 4px solid ${priorityColor}; padding: 1rem; margin-bottom: 0.75rem; border-radius:4px; background: rgba(30,41,59,0.02);">
                    <div style="display:flex; flex-direction:column; gap:0.75rem;">
                        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem;">
                            <span class="font-bold text-xs" style="color: ${priorityColor}; text-transform:uppercase;">Step ${step.step_num}: ${step.skill}</span>
                            <span class="text-xs" style="background:var(--surface); border: 1px solid var(--border); padding:3px 8px; border-radius:4px; color:var(--text-muted); font-weight:500;">${step.time} - ${step.priority}</span>
                        </div>
                        <p class="font-bold text-sm" style="color: var(--text-primary); margin:0; line-height:1.5;"><span style="color:var(--primary);">Action:</span> ${step.action}</p>
                        <p class="text-xs" style="color: var(--text-secondary); margin:0; line-height: 1.5;"><strong>Why:</strong> ${step.why}</p>
                    </div>
                </li>`;
            }
            impactContainer.innerHTML = html;
        }
    }

    const quickWinsList = document.getElementById("quickWinsList");
    const quickWinsContainer = document.getElementById("quickWinsContainer");
    const wins = data.quick_wins || [];
    if (quickWinsList && quickWinsContainer) {
        if (wins.length > 0) {
            quickWinsContainer.style.display = "block";
            quickWinsList.innerHTML = wins.map(w => `<li style="margin-bottom:0.5rem; line-height: 1.4;">${w}</li>`).join("");
        } else {
            quickWinsContainer.style.display = "none";
        }
    }

    const matchedContainer = document.getElementById("matchedSkillsContainer");
    if (matchedContainer) {
        const skills = data.matched_keywords || data.matched_skills || [];
        if (!skills.length) {
            matchedContainer.innerHTML = '<span class="empty-state-text" style="grid-column: 1 / -1; font-size:0.875rem;">No foundational keywords successfully detected.</span>';
        } else {
            matchedContainer.innerHTML = skills.map(skill => `<span class="chip chip-success" style="background:rgba(34,197,94,0.1); color:var(--success); border-color:rgba(34,197,94,0.2);">${skill}</span>`).join("");
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