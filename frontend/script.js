async function analyzeResume() {
    const fileInput = document.getElementById("resumeFile");
    const jdText = document.getElementById("jdText").value;
    const resultsDiv = document.getElementById("results");

    if (!fileInput.files[0] || !jdText) {
        alert("Upload resume and paste JD");
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    formData.append("jd", jdText);

    if (resultsDiv) {
        resultsDiv.innerText = "Analyzing resume...";
    }

    try {
        const response = await fetch("http://127.0.0.1:8000/score-resume/", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            const text = await response.text();
            if (resultsDiv) {
                resultsDiv.innerText = "Server error (" + response.status + "):\n" + text;
            } else {
                alert("Server error (" + response.status + "). Check backend logs.");
            }
            return;
        }

        const data = await response.json();

        // Store result and go to results page
        sessionStorage.setItem("analysisResult", JSON.stringify(data));
        window.location.href = "results.html";
    } catch (err) {
        if (resultsDiv) {
            resultsDiv.innerText = "Network error: " + err.message;
        } else {
            alert("Network error: " + err.message);
        }
    }
}

function displayResults(data) {

    const resultsDiv = document.getElementById("results");

    const matchedSkills = data.matched_skills
        .map(skill => `<span class="skill-tag">${skill}</span>`)
        .join("");

    const criticalGaps = data.critical_gaps
        .map(skill => `<span class="skill-tag gap-critical">${skill}</span>`)
        .join("");

    const importantGaps = data.important_gaps
        .map(skill => `<span class="skill-tag gap-important">${skill}</span>`)
        .join("");

    resultsDiv.innerHTML = `
        <div class="results-card">
            <div class="score">Overall Match: ${data.overall_match}%</div>
            <div class="progress-bar">
                <div class="progress-fill" 
                     style="width:${data.overall_match}%">
                </div>
            </div>

            <br>

            <div class="score">Confidence: ${data.confidence_score}%</div>
            <div class="progress-bar">
                <div class="progress-fill" 
                     style="width:${data.confidence_score}%">
                </div>
            </div>

            <br>

            <h4>Matched Skills</h4>
            ${matchedSkills}

            <h4>Critical Gaps</h4>
            ${criticalGaps}

            <h4>Important Gaps</h4>
            ${importantGaps}
        </div>
    `;
}