import spacy
from collections import Counter

nlp = spacy.load("en_core_web_sm")

# Map over-arching concepts to concrete technologies
SYNONYM_MAP = {
    "backend": ["flask", "django", "fastapi", "spring", "node", "express", "java", "python"],
    "frontend": ["html", "css", "javascript", "react", "angular", "vue"],
    "database": ["sql", "mysql", "postgresql", "mongodb", "redis"],
    "cloud": ["aws", "gcp", "azure", "docker", "kubernetes"],
    "api": ["rest", "fastapi", "flask", "express", "graphql"],
    "ml": ["machine learning", "deep learning", "nlp", "tensorflow", "pytorch", "scikit-learn", "ai"],
    "programming": ["python", "java", "c++", "c#", "javascript", "typescript"]
}

TECH_TERMS = {
    "python", "java", "c++", "c#", "javascript", "typescript",
    "html", "css", "react", "angular", "vue",
    "flask", "django", "fastapi", "spring",
    "node", "express", "sql", "mysql", "postgresql",
    "mongodb", "firebase", "redis",
    "machine learning", "deep learning", "nlp",
    "computer vision", "ai", "ml", "backend", "frontend", "database", "cloud", "api", "programming",
    "tensorflow", "pytorch", "scikit-learn",
    "numpy", "pandas",
    "docker", "kubernetes", "aws", "azure", "gcp",
    "git", "linux", "rest", "graphql", "json"
}

CANONICAL_MAP = {
    "html5": "html",
    "css3": "css",
    "vanilla javascript": "javascript",
    "js": "javascript",
    "python scripts": "python",
    "restful api": "rest",
    "restful apis": "rest",
    "rest api": "rest",
    "rest apis": "rest",
    "amazon web services": "aws",
    "node.js": "node",
    "nodejs": "node"
}

def normalize_skill(phrase: str):
    phrase = phrase.strip().lower()
    
    if phrase in CANONICAL_MAP:
        return CANONICAL_MAP[phrase]

    for key in CANONICAL_MAP:
        if key in phrase:
            return CANONICAL_MAP[key]

    return phrase

def extract_skills(text: str):
    text = text.lower().replace("\n", " ")
    doc = nlp(text)

    detected = []

    # 1. Token-level matching
    for token in doc:
        word = token.text.strip()

        if word in TECH_TERMS:
            detected.append(normalize_skill(word))

        if word in CANONICAL_MAP:
            detected.append(CANONICAL_MAP[word])

    # 2. Multi-word phrases
    for phrase in TECH_TERMS:
        if " " in phrase and phrase in text:
            detected.append(normalize_skill(phrase))

    skill_counts = Counter(detected)

    # 3. Add synonym expansion capabilities 
    # E.g. if we detect 'flask', we can implicitly credit 'backend'
    # This happens in ats_scorer, but returning distinct skills here
    structured_skills = [
        {"skill": skill, "count": count}
        for skill, count in skill_counts.items()
    ]
    structured_skills.sort(key=lambda x: x["count"], reverse=True)

    return {
        "skills": structured_skills,
        "raw_skills": list(skill_counts.keys())
    }
