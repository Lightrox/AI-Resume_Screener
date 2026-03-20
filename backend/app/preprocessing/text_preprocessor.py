import re
import spacy

nlp = spacy.load("en_core_web_sm")

def light_clean(text: str) -> str:
    # Aggressively remove punctuation and lowercase
    text = text.lower()
    text = text.replace("\n", " ")
    text = re.sub(r'[^a-z0-9#\+]', ' ', text)  # Keep C++ and C#
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def heavy_clean(text: str):
    text = text.lower()
    text = re.sub(r'\n', ' ', text)
    text = re.sub(r'[^a-z0-9\s#\+\-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    doc = nlp(text)
    lemmas = [
        token.lemma_
        for token in doc
        if not token.is_stop and token.is_alpha
    ]
    return lemmas

def preprocess_resume(text: str):
    return {
        "light_text": light_clean(text),
        "lemmas": heavy_clean(text)
    }
