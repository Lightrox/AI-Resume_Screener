# AI-Powered Resume Screening & Job Matching System

## Overview
This project automates resume screening and job matching using Natural Language Processing (NLP).
It parses resumes, extracts relevant skills and experience, and compares them against job
descriptions to compute ATS and overall fit scores.

## Problem Statement
Manual resume screening is time-consuming, inconsistent, and prone to bias.
This system provides an explainable, scalable, and automated approach to resume evaluation.

## Tech Stack
- Backend: FastAPI
- NLP: spaCy, NLTK
- ML: scikit-learn (TF-IDF, cosine similarity)
- Parsing: pdfplumber, python-docx
- Database: SQLite
- Frontend: HTML, CSS, JavaScript

## System Architecture
Resume / JD
↓
Text Parsing
↓
Text Preprocessing
↓
Skill Extraction
↓
ATS & Fit Scoring
↓
API Response (JSON)

## Key Features
- Resume parsing (PDF/DOCX)
- Skill extraction using taxonomy-based matching
- ATS score calculation
- Skill gap analysis
- Explainable scoring logic

## Project Structure
ai-resume-screener/
│
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── api/
│   │   │   └── routes.py
│   │   ├── core/
│   │   │   └── config.py
│   │   ├── services/
│   │   │   ├── parser.py        # PDF/DOCX parsing
│   │   │   ├── preprocessing.py
│   │   │   ├── skill_extractor.py
│   │   │   └── scorer.py
│   │   ├── models/
│   │   │   └── schemas.py
│   │   └── utils/
│   │       └── file_utils.py
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── data/
│   ├── resumes/
│   ├── job_descriptions/
│   └── skill_taxonomy.json
│
├── tests/
│
└── README.md

## Future Enhancements
- Job recommendation ranking
- Semantic skill matching
- Dashboard-based analytics