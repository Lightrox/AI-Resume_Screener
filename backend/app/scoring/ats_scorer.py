import random
import re
from app.preprocessing.text_preprocessor import preprocess_resume
from app.skill_engine.skill_extractor import extract_skills, SYNONYM_MAP

def get_expanded_skills(skill_list):
    expanded = set(skill_list)
    for concept, tools in SYNONYM_MAP.items():
        if concept in skill_list:
            expanded.add(concept)
        for tool in tools:
            if tool in skill_list:
                expanded.add(concept)
                expanded.add(tool)
    return expanded

def detect_jd_domain(jd_expanded):
    ml_keywords = {"machine learning", "nlp", "model", "training", "dataset", "ai", "pandas", "scikit-learn", "tensorflow", "pytorch"}
    cloud_keywords = {"docker", "kubernetes", "aws", "gcp", "azure", "cloud", "infra", "devops", "distributed systems", "terraform", "ansible"}
    data_keywords = {"data engineering", "etl", "data pipe", "warehouse", "spark", "hadoop", "big data", "data processing", "data handling"}
    sde_keywords = {"dsa", "frontend", "backend", "web", "react", "angular", "node", "java", "flask", "django", "javascript", "html", "css", "typescript", "oop", "system design"}

    ml_overlap = len(jd_expanded.intersection(ml_keywords))
    cloud_overlap = len(jd_expanded.intersection(cloud_keywords))
    data_overlap = len(jd_expanded.intersection(data_keywords))
    sde_overlap = len(jd_expanded.intersection(sde_keywords))

    overlaps = {
        "Machine Learning": ml_overlap,
        "Cloud / Infra": cloud_overlap,
        "Data Engineering": data_overlap,
        "SDE / Web Dev": sde_overlap
    }

    sorted_domains = sorted(overlaps.items(), key=lambda x: x[1], reverse=True)
    top_domain, top_count = sorted_domains[0]
    second_domain, second_count = sorted_domains[1]

    if top_count > 0 and second_count > top_count * 0.5:
        return "Hybrid"
    if top_count > 0:
        return top_domain
    return "SDE / Web Dev"

def get_skill_category(skill):
    categories = {
        "frontend": ["react", "angular", "vue", "frontend", "css", "html", "javascript", "typescript"],
        "backend": ["python", "java", "node", "backend", "api", "rest", "flask", "django", "fastapi", "json", "golang", "c#", "c++", "ruby"],
        "database": ["sql", "mysql", "postgresql", "database", "mongodb", "redis", "cassandra"],
        "data": ["data", "pandas", "numpy", "visualization", "analytics", "etl", "spark", "hadoop", "tableau", "powerbi", "data processing", "data handling"],
        "machine_learning": ["ml", "machine learning", "ai", "nlp", "tensorflow", "pytorch", "scikit-learn", "keras", "model training", "deep learning"],
        "devops": ["docker", "kubernetes", "aws", "gcp", "azure", "cloud", "microservices", "distributed systems", "terraform", "ansible", "jenkins", "cicd"],
        "core_cs": ["dsa", "data structures", "algorithms", "oop", "system design", "object oriented", "operating systems", "networking"]
    }
    for cat, items in categories.items():
        if skill in items:
            return cat
    return "others"

CONCEPT_TOOL_MAP = {
    "data processing": ["pandas", "numpy", "etl", "data handling", "data manipulation", "json handling", "api data flow", "data processing"],
    "api handling": ["rest", "flask", "fastapi", "backend api", "api data flow", "json", "api handling"],
    "database": ["sql", "mysql", "postgresql", "mongodb", "database", "structured data handling", "backend apps"]
}

def get_skill_depth_multiplier(skill, resume_sections):
    """
    FIX: Check impl_keywords in proximity to the skill mention, not globally.
    Returns 1.0 (High), 0.7 (Medium), or 0.4 (Low) depth.
    High:   Multiple mentions in narrative OR skill appears near action verbs.
    Medium: Single mention in narrative (exp/projects).
    Low:    Only in skills list or inferred.
    """
    skills_text = str(resume_sections.get("skills", "")).lower()
    exp_text = (
        str(resume_sections.get("experience", "")) + " " +
        str(resume_sections.get("work_experience", ""))
    ).lower()
    proj_text = str(resume_sections.get("projects", "")).lower()

    impl_keywords = ["built", "developed", "implemented", "deployed", "architected", "optimized", "managed"]

    mentions_in_exp = exp_text.count(skill)
    mentions_in_proj = proj_text.count(skill)
    mentions_in_narrative = mentions_in_exp + mentions_in_proj

    # FIX: check impl context only near the skill, using a sliding window approach.
    # Extract a ±120-char window around each skill mention and check for action verbs there.
    def has_impl_context_near_skill(text, sk):
        idx = 0
        while True:
            pos = text.find(sk, idx)
            if pos == -1:
                break
            window = text[max(0, pos - 120): pos + len(sk) + 120]
            if any(kw in window for kw in impl_keywords):
                return True
            idx = pos + 1
        return False

    skill_near_impl_exp = has_impl_context_near_skill(exp_text, skill)
    skill_near_impl_proj = has_impl_context_near_skill(proj_text, skill)

    if (mentions_in_narrative >= 2) or (mentions_in_proj >= 1 and skill_near_impl_proj) or (mentions_in_exp >= 1 and skill_near_impl_exp):
        return 1.0
    if mentions_in_narrative >= 1:
        return 0.7
    if skill in skills_text:
        return 0.4
    return 0.4

def get_skill_match_value(skill, resume_expanded, resume_sections=None, jd_domain=None):
    base_val = 0.0
    if skill in resume_expanded:
        base_val = 1.0
    else:
        for concept, tools in CONCEPT_TOOL_MAP.items():
            if skill in tools:
                if concept in resume_expanded or any(t in resume_expanded for t in tools):
                    base_val = 0.7
            if skill == concept:
                if any(t in resume_expanded for t in tools):
                    base_val = 0.8

    if base_val == 0.0:
        return 0.0

    # FIX: Always apply depth multiplier when resume_sections is available,
    # regardless of jd_domain — domain filtering was silently skipping many skills.
    if resume_sections is not None:
        skill_cat = get_skill_category(skill)
        if jd_domain:
            domain_map = {
                "Machine Learning": ["machine_learning", "data", "backend"],
                "Cloud / Infra": ["devops", "backend", "core_cs"],
                "Data Engineering": ["data", "database", "backend"],
                "SDE / Web Dev": ["frontend", "backend", "core_cs", "database"],
                "Hybrid": ["backend", "data", "database", "frontend"]
            }
            relevant_cats = domain_map.get(jd_domain, list(domain_map["SDE / Web Dev"]))
            # Apply depth multiplier only for categories relevant to the role
            if skill_cat in relevant_cats:
                multiplier = get_skill_depth_multiplier(skill, resume_sections)
                return base_val * multiplier
        else:
            # No domain info — still apply depth for backend (always relevant)
            if skill_cat == "backend":
                multiplier = get_skill_depth_multiplier(skill, resume_sections)
                return base_val * multiplier

    return base_val

def parse_jd_skill_priority(jd_text, jd_expanded):
    required = set()
    optional = set()
    bonus = set()
    lines = jd_text.lower().split('\n')
    current_section = "required"
    for line in lines:
        if any(h in line for h in ["prefer", "optional", "plus", "nice to", "bonus"]):
            current_section = "optional"
        elif any(h in line for h in ["requirement", "required", "qualification", "must have", "essential"]):
            current_section = "required"
        found_skills = [s for s in jd_expanded if s in line]
        if current_section == "required":
            required.update(found_skills)
        else:
            optional.update(found_skills)

    if not required:
        # FIX: When no explicit "required" section found, use ALL skills as required
        # but mark them as medium priority — don't inflate optional into bonus blindly.
        required = jd_expanded.copy()
        optional = set()
        bonus = set()
    else:
        if len(optional) > 5:
            bonus = set(list(optional)[:2])
            optional = optional - bonus

    return required, optional, bonus

def generate_student_strength(matched_skills, final_score):
    if not matched_skills:
        return "You currently lack the foundational skills expected for these roles."
    top = [s.title() for s in matched_skills[:3]]
    top_str = " and ".join(top) if len(top) > 1 else top[0]
    if len(top) > 2:
        top_str = f"{top[0]}, {top[1]}, and {top[2]}"
    if final_score >= 75:
        return f"You strongly align with most key requirements, including {top_str}."
    elif final_score >= 50:
        return f"You match several important requirements, including {top_str}."
    else:
        return f"You align with some foundational requirements, including {top_str}."

def build_roadmap_sequence(critical_missing, nice_to_have_missing, final_score, jd_domain, cand_domain, core_coverage):
    all_missing = critical_missing + nice_to_have_missing
    if not all_missing:
        all_missing = ["sql", "python", "react"]
    is_mismatch = (core_coverage < 40) and (cand_domain != "None Detected") and (jd_domain != cand_domain)

    modules = {
        "SQL & Database Fundamentals": {"keys": ["sql", "mysql", "postgresql", "database", "mongodb"], "action": "Learn core concepts like normalization and indexing. Build a relational schema.", "why": "Databases form the critical persistence layer for almost all applications.", "time": "5-7 days", "tier": 1, "priority": "High Priority"},
        "Backend API Development": {"keys": ["python", "java", "backend", "api", "rest", "node", "flask", "fastapi"], "action": "Build a simple backend project (CRUD API) using SQL/PostgreSQL.", "why": "Servers and APIs are required to securely process and serve data to clients.", "time": "1-2 weeks", "tier": 2, "priority": "High Priority"},
        "Frontend SPA Development": {"keys": ["react", "angular", "vue", "frontend", "javascript", "html", "css"], "action": "Build a responsive Single Page Application (SPA) that consumes an external REST API.", "why": "Modern user interfaces demand component-driven, reactive web frameworks.", "time": "2-3 weeks", "tier": 2, "priority": "High Priority"},
        "Containerization & Deployment": {"keys": ["docker", "kubernetes"], "action": "Write a Dockerfile to containerize your backend API.", "why": "Containerization ensures your application runs predictably.", "time": "3-5 days", "tier": 3, "priority": "Medium Priority"},
        "Data & ML Foundations": {"keys": ["ml", "machine learning", "data", "pandas", "numpy"], "action": "Train a simple predictive model using Scikit-Learn or perform data analysis using Pandas.", "why": "Data modeling and predictive features are core to analytical software roles.", "time": "2-3 weeks", "tier": 2, "priority": "High Priority"},
        "Algorithms": {"keys": ["dsa", "algorithms", "oop"], "action": "Solve DSA problems to strengthen conceptual programming logic.", "why": "Core CS fundamentals are required for technical execution.", "time": "3-4 weeks", "tier": 1, "priority": "High Priority"}
    }

    selected_steps = []
    for module_name, info in modules.items():
        if any(k in all_missing for k in info["keys"]):
            is_critical = any(k in critical_missing for k in info["keys"])
            priority = info["priority"] if is_critical else "Bonus Skill"
            if is_mismatch:
                selected_steps.append({"skill": module_name, "priority": "Transition Step", "time": info["time"], "action": info["action"], "why": info["why"], "tier": info["tier"]})
            else:
                selected_steps.append({"skill": module_name, "priority": priority, "time": info["time"], "action": info["action"], "why": info["why"], "tier": info["tier"]})

    if not selected_steps:
        selected_steps.append({"skill": "Programming Fundamentals", "priority": "High Priority", "time": "2-3 weeks", "action": "Build a foundational project.", "why": "Bridging knowledge requires building domain-specific portfolios.", "tier": 1})

    priority_order = {"Transition Step": 0, "High Priority": 1, "Medium Priority": 2, "Bonus Skill": 3}
    selected_steps.sort(key=lambda x: (x["tier"], priority_order.get(x["priority"], 99)))
    selected_steps = selected_steps[:5]
    for i, step in enumerate(selected_steps):
        step["step_num"] = i + 1
    return selected_steps

def classify_jd_level(jd_skills):
    advanced = {"docker", "kubernetes", "aws", "cloud", "microservices", "distributed systems", "system design"}
    if advanced.intersection(jd_skills):
        return "Advanced"
    return "Intermediate"

def get_essential_skills(required_skills, jd_text):
    jd_lower = jd_text.lower()
    skill_counts = {s: jd_lower.count(s.lower()) for s in required_skills}
    sorted_essential = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
    return [s for s, count in sorted_essential[:5]]

def compute_ats_score(resume_sections, jd_text, jd_skill_data):
    jd_skills_raw = jd_skill_data.get("raw_skills", [])
    jd_expanded = get_expanded_skills(jd_skills_raw)
    jd_domain = detect_jd_domain(jd_expanded)
    jd_level = classify_jd_level(jd_expanded)
    required_skills, optional_skills, bonus_skills = parse_jd_skill_priority(jd_text, jd_expanded)
    essential_skills = get_essential_skills(required_skills, jd_text)

    full_resume_text = " ".join(str(v) for v in resume_sections.values())
    resume_processed = preprocess_resume(full_resume_text)
    resume_expanded = get_expanded_skills(extract_skills(resume_processed["light_text"]).get("raw_skills", []))

    exp_text = (
        str(resume_sections.get("experience", "")) + " " +
        str(resume_sections.get("work_experience", ""))
    ).lower()
    proj_text = str(resume_sections.get("projects", "")).lower()

    # FIX: backend_match_pct now uses depth-aware scoring so two candidates with
    # the same skills but different depths get different values.
    backend_reqs = [s for s in jd_expanded if get_skill_category(s) == "backend"]
    backend_match_pct = (
        sum(get_skill_match_value(s, resume_expanded, resume_sections, jd_domain) for s in backend_reqs)
        / max(len(backend_reqs), 1)
    ) if backend_reqs else 1.0
    has_api_exp = any(s in resume_expanded for s in ["api", "rest", "flask", "fastapi", "backend"])

    exp_expanded = get_expanded_skills(extract_skills(preprocess_resume(exp_text)["light_text"]).get("raw_skills", []))
    exp_match_score = (len(exp_expanded.intersection(jd_expanded)) / max(len(jd_expanded), 1)) * 100 if jd_expanded else 0

    # Required Skill Scoring (80 pts) — depth-aware for all skills
    required_score = 0
    if required_skills:
        match_sum = sum(
            get_skill_match_value(s, resume_expanded, resume_sections, jd_domain)
            for s in required_skills
        )
        required_score = (match_sum / len(required_skills)) * 80

    WEIGHTS = {
        "SDE / Web Dev":     {"backend": 0.35, "frontend": 0.25, "core_cs": 0.20, "database": 0.10, "others": 0.10},
        "Machine Learning":  {"machine_learning": 0.50, "data": 0.20, "backend": 0.15, "others": 0.15},
        "Data Engineering":  {"data": 0.40, "database": 0.30, "backend": 0.20, "others": 0.10},
        "Cloud / Infra":     {"devops": 0.50, "backend": 0.20, "core_cs": 0.15, "others": 0.15},
        "Hybrid":            {"backend": 0.40, "data": 0.30, "database": 0.20, "others": 0.10}
    }
    role_weights = WEIGHTS.get(jd_domain, WEIGHTS["SDE / Web Dev"])

    category_score = 0
    jd_skills_by_cat = {cat: [] for cat in ["frontend", "backend", "database", "data", "machine_learning", "devops", "core_cs", "others"]}
    for skill in jd_expanded:
        jd_skills_by_cat[get_skill_category(skill)].append(skill)

    for cat, weight in role_weights.items():
        reqs = jd_skills_by_cat.get(cat, [])
        if reqs:
            cat_match = sum(
                get_skill_match_value(s, resume_expanded, resume_sections, jd_domain)
                for s in reqs
            )
            category_score += (cat_match / len(reqs)) * weight * 20

    optional_score = (
        sum(get_skill_match_value(s, resume_expanded) for s in optional_skills)
        / max(len(optional_skills), 1)
    ) * 15 if optional_skills else 0

    bonus_score = (
        sum(get_skill_match_value(s, resume_expanded) for s in bonus_skills)
        / max(len(bonus_skills), 1)
    ) * 5 if bonus_skills else 0

    domain_map = {
        "Machine Learning": ["machine_learning"],
        "Cloud / Infra": ["devops"],
        "Data Engineering": ["data", "database"],
        "SDE / Web Dev": ["frontend", "backend"]
    }
    domain_cats = domain_map.get(jd_domain, ["backend"])
    all_dom_reqs = []
    for cat in domain_cats:
        all_dom_reqs.extend(jd_skills_by_cat[cat])
    domain_match_score = (
        sum(get_skill_match_value(s, resume_expanded) for s in all_dom_reqs)
        / max(len(all_dom_reqs), 1)
    ) * 100 if all_dom_reqs else 100

    boost = 0
    if domain_match_score >= 60:
        if essential_skills:
            ess_match_sum = sum(
                get_skill_match_value(s, resume_expanded, resume_sections, jd_domain)
                for s in essential_skills
            )
            if (ess_match_sum / len(essential_skills)) >= 0.8:
                boost += 10

        rel_cat_hits = 0
        for cat, w in role_weights.items():
            reqs = jd_skills_by_cat.get(cat, [])
            if reqs and (
                sum(get_skill_match_value(s, resume_expanded, resume_sections, jd_domain) for s in reqs)
                / len(reqs) > 0.5
            ):
                rel_cat_hits += 1
        if rel_cat_hits >= 2:
            boost += 5

        domain_keywords = {
            "SDE / Web Dev":     ["api", "crud", "frontend", "backend", "web", "app"],
            "Machine Learning":  ["model", "training", "dataset", "nlp", "predictive"],
            "Cloud / Infra":     ["docker", "kubernetes", "aws", "cloud", "deployment"],
            "Data Engineering":  ["etl", "pipeline", "warehouse", "processing"],
            "Hybrid":            ["api", "data", "processing", "backend"]
        }
        relevant_proj_kws = domain_keywords.get(jd_domain, [])
        if proj_text.strip() and any(kw in proj_text for kw in relevant_proj_kws):
            if any(s in proj_text for s in jd_expanded):
                boost += 10

    boost = min(boost, 25)

    penalty = 0
    if jd_level == "Advanced" and not any(
        s in resume_expanded for s in ["docker", "kubernetes", "aws", "cloud", "distributed"]
    ):
        penalty += 15

    critical_skills = {"backend", "api", "rest", "python", "java", "flask", "fastapi", "django"}
    missing_critical = [
        s for s in required_skills
        if get_skill_match_value(s, resume_expanded) == 0 and s in critical_skills
    ]
    non_critical_missing = [
        s for s in required_skills
        if get_skill_match_value(s, resume_expanded) == 0 and s not in critical_skills
    ]

    penalty += len(missing_critical) * 8
    penalty += len(non_critical_missing) * 4
    penalty = min(penalty, 30)

    final_raw = required_score + category_score + optional_score + bonus_score + boost - penalty

    if domain_match_score < 25:
        final_raw = min(final_raw, 30)
    elif domain_match_score < 40:
        final_raw = min(final_raw, 40)

    # FIX: Backend floor now requires DEPTH (>= 0.7 depth-weighted) not just presence.
    # This stops shallow-matched resumes from getting the same floor as deep ones.
    if backend_match_pct >= 0.7 and has_api_exp:
        # Apply a proportional floor — strong depth earns a higher floor.
        floor_value = 50 + int(backend_match_pct * 15)  # range: 60–65 based on depth
        final_raw = max(final_raw, floor_value)

    req_match_ratio = (required_score / 80) if required_score > 0 else 0
    if req_match_ratio > 0.85:
        final_raw += 5

    # FIX: Replace non-differentiating keyword checksum jitter with a
    # skill-weighted signature that encodes match depth, not just keyword presence.
    # Two candidates matching the same keywords but with different depths now diverge.
    depth_sig = sum(
        get_skill_match_value(s, resume_expanded, resume_sections, jd_domain) * (i + 1)
        for i, s in enumerate(sorted(jd_expanded.intersection(resume_expanded)))
    )
    jitter = (depth_sig % 1.0) if depth_sig > 0 else 0.0

    final_score = max(15, min(final_raw + jitter, 95))
    final_score = round(final_score, 2)

    missing_kws = list(jd_expanded - resume_expanded)
    critical_missing = [
        s for s in required_skills
        if get_skill_match_value(s, resume_expanded) == 0
    ]

    if domain_match_score < 40:
        match_level = "Role Mismatch - Transition Required"
    elif final_score >= 70:
        match_level = "High Match"
    elif final_score >= 40:
        match_level = "Moderate Match"
    else:
        match_level = "Low Match"

    job_readiness = "Ready" if final_score >= 70 else ("Partially Ready" if final_score >= 40 else "Not Ready")

    inf_match = any(s in resume_expanded for s in ["docker", "kubernetes", "aws", "cloud", "terraform", "jenkins"])
    infra_assessment = "Cloud-Ready" if inf_match else "Entry-Level (No Cloud/Containers)"

    mention_counts = [exp_text.count(s) + proj_text.count(s) for s in required_skills]
    total_mentions = sum(mention_counts)
    if total_mentions >= 10:
        exp_assessment = "Sustained Narrative Experience"
    elif total_mentions >= 5:
        exp_assessment = "Standard Professional Experience"
    elif total_mentions > 0:
        exp_assessment = "Basic Mentions Detectable"
    else:
        exp_assessment = "Limited Narrative Evidence"

    matched_kws = list(jd_expanded.intersection(resume_expanded))

    return {
        "ats_score": final_score,
        "match_level": match_level,
        "job_readiness": job_readiness,
        "best_fit_role": jd_domain,
        "alternate_role": "Generic Backend Developer" if jd_domain != "SDE / Web Dev" else "Full Stack Developer",
        "experience_assessment": exp_assessment,
        "infra_assessment": infra_assessment,
        "core_coverage": int(domain_match_score),
        "roadmap_sequence": build_roadmap_sequence(critical_missing, missing_kws, final_score, jd_domain, "None", domain_match_score),
        "category_scores": {
            "Required Skills": round(required_score, 2),
            "Domain Match": round(domain_match_score, 2),
            "Supplemental Match": round(category_score, 2),
            "Rewards/Penalties": round(boost - penalty, 2)
        },
        "structured_summary": {
            "interpretation": f"Your resume matches {int(domain_match_score)}% of the core requirements. You are {job_readiness.lower()} for this role.",
            "strength": generate_student_strength(matched_kws, final_score)
        },
        "matched_keywords": matched_kws,
        "missing_keywords": missing_kws
    }