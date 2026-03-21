from fastapi import FastAPI, UploadFile, File, Form
import shutil
import os
import uuid
from collections import defaultdict
from .preprocessing.text_preprocessor import preprocess_resume
from .skill_engine.skill_extractor import extract_skills
from .scoring.ats_scorer import compute_ats_score
from .parser.resume_parser import parse_resume
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

class JDInput(BaseModel):
    job_description: str

app = FastAPI(title="AI Resume Screener")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # We don't rely on cookies/auth for this frontend request, so avoid
    # credentialed CORS headers (makes behavior more predictable).
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.post("/upload-resume/")
def upload_resume(file: UploadFile = File(...)):
    if not file.filename.endswith((".pdf", ".docx")):
        return {"error": "Only PDF and DOCX files are allowed"}
    unique_name = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_name)
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Parse resume
    try:
        result = parse_resume(file_path)
    except Exception as e:
        return {"error": str(e)}
    processed = preprocess_resume(result["text"])
    skill_data = extract_skills(processed["light_text"])

    return {
        "email": result["email"],
        "phone": result["phone"],
        "skills": skill_data["skills"],     
        "total_skill_mentions": skill_data["total_skill_mentions"]
    }
@app.post("/score-resume/")
def score_resume(
    file: UploadFile = File(...),
    jd: str = Form(...)
):

    if not file.filename.endswith((".pdf", ".docx")):
        return {"error": "Only PDF and DOCX files are allowed"}

    unique_name = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = parse_resume(file_path)
    # print("\n===== SECTION DEBUG START =====")
    # print(result["sections"])
    # print("===== SECTION DEBUG END =====\n")

    sections = result["sections"]

    # Extract JD skills
    jd_processed = preprocess_resume(jd)
    jd_skill_data = extract_skills(jd_processed["light_text"])

    ats_result = compute_ats_score(
        sections,
        jd,
        jd_skill_data
    )

    return ats_result


