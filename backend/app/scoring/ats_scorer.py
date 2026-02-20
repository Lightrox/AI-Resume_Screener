import difflib
SKILL_CATEGORIES = {
    "backend": ["python", "flask", "java", "sql", "rest"],
    "frontend": ["html", "css", "javascript", "react", "vue", "angular"],
    "devops": ["docker", "aws", "kubernetes", "linux"],
    "ml": ["machine learning", "tensorflow", "pytorch", "nlp"]
}
def find_similar_skill(target_skill, resume_skill_keys):
    for r_skill in resume_skill_keys:
        similarity = difflib.SequenceMatcher(
            None, target_skill, r_skill
        ).ratio()

        if similarity > 0.85:   # threshold
            return r_skill

    return None
def compute_ats_score(resume_skills, jd_skill_data):
    resume_dict = {item["skill"]: item["count"] for item in resume_skills}
    jd_dict = {item["skill"]: item["count"] for item in jd_skill_data}

    matched = []
    missing = []

    weighted_score = 0
    max_possible_score = 0

    # ---------- Overall Weighted Score ----------
    for skill, jd_weight in jd_dict.items():
        importance_weight = min(jd_weight, 3)
        max_possible_score += importance_weight * 3

        similar_match = find_similar_skill(skill, resume_dict.keys())

        if skill in resume_dict or similar_match:
            actual_skill = skill if skill in resume_dict else similar_match

            matched.append(skill)
            resume_strength = min(resume_dict[actual_skill], 3)
            weighted_score += resume_strength * importance_weight
        else:
            missing.append(skill)

    if max_possible_score == 0:
        overall_match = 0
    else:
        overall_match = round(
            (weighted_score / max_possible_score) * 100,
            2
        )

    # ---------- Domain Breakdown ----------
    domain_breakdown = {}

    for domain, skills in SKILL_CATEGORIES.items():
        jd_domain_skills = [s for s in jd_dict if s in skills]

        if not jd_domain_skills:
            domain_breakdown[domain] = 0
            continue

        matched_count = sum(1 for s in jd_domain_skills if s in resume_dict)
        domain_score = round(
            (matched_count / len(jd_domain_skills)) * 100,
            2
        )

        domain_breakdown[domain] = domain_score

    # ---------- Gap Ranking ----------
    critical_gaps = []
    important_gaps = []
    minor_gaps = []

    for skill in missing:
        jd_importance = jd_dict.get(skill, 1)

        if jd_importance >= 2:
            critical_gaps.append(skill)
        elif skill in SKILL_CATEGORIES.get("devops", []):
            critical_gaps.append(skill)
        elif skill in SKILL_CATEGORIES.get("backend", []):
            important_gaps.append(skill)
        else:
            minor_gaps.append(skill)
    # ---------- Confidence Score ----------
    jd_skill_count = len(jd_dict)
    resume_skill_count = len(resume_dict)
    matched_count = len(matched)

    if jd_skill_count == 0:
        confidence = 0
    else:
        overlap_ratio = matched_count / jd_skill_count

        data_density = min(
            (jd_skill_count + resume_skill_count) / 20,
            1
        )  # cap at 1

        confidence = round(
            (overlap_ratio * 0.6 + data_density * 0.4) * 100,
            2
        )

    return {
        "overall_match": overall_match,
        "confidence_score": confidence,
        "domain_breakdown": domain_breakdown,
        "matched_skills": matched,
        "critical_gaps": critical_gaps,
        "important_gaps": important_gaps,
        "minor_gaps": minor_gaps,
        "extra_skills": [
            skill for skill in resume_dict.keys()
            if skill not in jd_dict
        ]
    }