SKILL_CATEGORIES = {
    "backend": ["python", "flask", "java", "sql", "rest"],
    "frontend": ["html", "css", "javascript", "react", "vue", "angular"],
    "devops": ["docker", "aws", "kubernetes", "linux"],
    "ml": ["machine learning", "tensorflow", "pytorch", "nlp"]
}
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

        if skill in resume_dict:
            matched.append(skill)
            resume_strength = min(resume_dict[skill], 3)
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

    return {
        "overall_match": overall_match,
        "domain_breakdown": domain_breakdown,
        "matched_skills": matched,
        "missing_skills": missing,
        "extra_skills": [
            skill for skill in resume_dict.keys()
            if skill not in jd_dict
        ]
    }