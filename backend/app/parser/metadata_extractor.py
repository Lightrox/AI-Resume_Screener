import re

def extract_email(text):
    match = re.search(r'\S+@\S+', text)
    return match.group(0) if match else None

def extract_phone(text):
    match = re.search(r'\+?\d[\d -]{8,}\d', text)
    return match.group(0) if match else None
