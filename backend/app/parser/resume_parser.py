import os
from .pdf_parser import extract_text_from_pdf
from .docx_parser import extract_text_from_docx
from .metadata_extractor import extract_email, extract_phone
import re

SECTION_HEADERS = {
    "skills": ["skills", "technical skills", "core competencies"],
    "projects": ["projects", "academic projects", "personal projects"],
    "summary": ["summary", "profile", "professional summary"],
    "experience": ["experience", "work experience", "employment"],
    "education": ["education"],
    "links": ["links"]
}
def parse_resume(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        text = extract_text_from_pdf(file_path)
    elif ext == ".docx":
        text = extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file format")

    if not text:
        text = ""

    email = extract_email(text)
    phone = extract_phone(text)

    sections = extract_sections(text)

    return {
        "email": email,
        "phone": phone,
        "sections": sections
    }
def extract_sections(text: str):
    sections = {
        "skills": "",
        "projects": "",
        "summary": "",
        "experience": "",
        "education": "",
        "links": "",
        "other": ""
    }

    lines = text.split("\n")
    current_section = "other"

    for line in lines:
        clean_line = line.strip()
        line_lower = clean_line.lower()

        # Skip empty lines
        if not clean_line:
            continue

        # Detect header (exact match or close match)
        detected = False
        for section, header_variants in SECTION_HEADERS.items():
            for header in header_variants:
                # strict header detection
                if re.fullmatch(rf"{header}", line_lower):
                    current_section = section
                    detected = True
                    break
            if detected:
                break

        if detected:
            continue

        sections[current_section] += clean_line + " "

    return sections
