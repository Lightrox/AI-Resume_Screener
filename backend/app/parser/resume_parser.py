import os
from .pdf_parser import extract_text_from_pdf
from .docx_parser import extract_text_from_docx
from .metadata_extractor import extract_email, extract_phone

def parse_resume(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        text = extract_text_from_pdf(file_path)
    elif ext == ".docx":
        text = extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file format")

    # 🔥 SAFETY CHECK
    if not text:
        text = ""

    email = extract_email(text)
    phone = extract_phone(text)

    cleaned_text = remove_header(text)

    return {
        "text": cleaned_text,
        "email": email,
        "phone": phone
    }

def remove_header(text: str):
    if not text:
        return ""

    lines = text.split("\n")

    if len(lines) <= 5:
        return text

    content_lines = lines[5:]
    return "\n".join(content_lines)

