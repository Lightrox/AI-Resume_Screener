import spacy
from collections import Counter

nlp = spacy.load("en_core_web_sm")

TECH_TERMS = {
    "python", "java", "c++", "c#", "javascript", "typescript",
    "html", "css", "react", "angular", "vue",
    "flask", "django", "fastapi", "spring",
    "node", "express", "sql", "mysql", "postgresql",
    "mongodb", "firebase", "redis",
    "machine learning", "deep learning", "nlp",
    "computer vision", "ai", "ml",
    "tensorflow", "pytorch", "scikit-learn",
    "numpy", "pandas",
    "docker", "kubernetes", "aws", "azure",
    "git", "linux", "rest", "api", "json"
}

CANONICAL_MAP = {
    # Frontend
    "html5": "html",
    "css3": "css",
    "vanilla javascript": "javascript",
    "js": "javascript",

    # Backend
    "python scripts": "python",
    "developed python scripts": "python",
    "restful api": "rest",
    "restful apis": "rest",
    "rest api": "rest",
    "rest apis": "rest",

    # Cloud / DevOps
    "amazon web services": "aws",
    "node.js": "node",
    "nodejs": "node",

    # ML
    "ml": "machine learning",
    "deep learning models": "deep learning"
}


def normalize_skill(phrase: str):
    phrase = phrase.strip().lower()

    # Exact canonical mapping
    if phrase in CANONICAL_MAP:
        return CANONICAL_MAP[phrase]

    # Partial canonical mapping
    for key in CANONICAL_MAP:
        if key in phrase:
            return CANONICAL_MAP[key]

    return phrase


def is_valid_skill(phrase: str):
    if len(phrase.split()) > 3:
        return False

    if phrase in TECH_TERMS:
        return True

    for tech in TECH_TERMS:
        if tech in phrase:
            return True

    return False


def extract_skills(text: str):
    text = text.lower().replace("\n", " ")
    doc = nlp(text)

    detected = []

    # 1️⃣ Token-level matching (most reliable)
    for token in doc:
        word = token.text.strip()

        if word in TECH_TERMS:
            normalized = normalize_skill(word)
            detected.append(normalized)

        if word in CANONICAL_MAP:
            detected.append(CANONICAL_MAP[word])

    # 2️⃣ Multi-word phrase matching
    for phrase in TECH_TERMS:
        if " " in phrase and phrase in text:
            detected.append(normalize_skill(phrase))

    # Count frequency
    skill_counts = Counter(detected)

    structured_skills = [
        {"skill": skill, "count": count}
        for skill, count in skill_counts.items()
    ]

    structured_skills.sort(key=lambda x: x["count"], reverse=True)
    total_mentions = sum(skill_counts.values())

    return {
        "skills": structured_skills,
        "total_skill_mentions": total_mentions
    }
