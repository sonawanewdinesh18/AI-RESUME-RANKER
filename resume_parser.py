import re
import spacy
import fitz  # PyMuPDF
import logging
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from textblob import TextBlob
from difflib import get_close_matches
from dotenv import load_dotenv
import datetime as dt

# Load spaCy model and environment variables
nlp = spacy.load("en_core_web_sm")
load_dotenv()

# Constants
TECH_DOMAINS = [
    "machine learning", "artificial intelligence", "ai", "ml", "deep learning",
    "data science", "web development", "full stack", "frontend", "backend",
    "android development", "ios development", "cloud", "devops",
    "html", "css", "react", "node", "python", "java", "sql", "nlp", "cv"
]

SKILL_SET = [
    "python", "java", "c", "c++", "c#", "html", "css", "javascript", "typescript",
    "react", "angular", "vue", "node.js", "express", "django", "flask",
    "sql", "mysql", "postgresql", "mongodb", "oracle", "firebase",
    "git", "github", "gitlab", "linux", "bash", "docker", "kubernetes",
    "aws", "azure", "gcp", "google cloud", "heroku",
    "tensorflow", "keras", "pytorch", "scikit-learn", "opencv", "nltk", "spacy",
    "pandas", "numpy", "matplotlib", "seaborn", "power bi", "tableau", "excel",
    "jira", "trello", "figma", "canva"
]

EDUCATION_KEYWORDS = [
    "bachelor", "master", "btech", "mtech", "be", "b.e", "m.e", "phd",
    "msc", "bsc", "ba", "ma", "bca", "mca", "diploma", "graduate", "undergraduate"
]

SOFT_SKILLS = [
    "teamwork", "communication", "leadership", "critical thinking",
    "problem solving", "adaptability", "creativity", "collaboration",
    "time management", "decision making", "emotional intelligence",
    "negotiation", "public speaking", "self-motivation"
]

# ===================== DB Save Function =====================
def update_parsed_resume_data(candidate_id, parsed_json):
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        cur = conn.cursor()
        cur.execute("""
            UPDATE resumes
            SET parsed_data = %s, uploaded_at = %s
            WHERE candidate_id = %s
        """, (json.dumps(parsed_json), dt.datetime.now(), candidate_id))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logging.error(f"[❌ update_parsed_resume_data] DB error for candidate_id={candidate_id}: {e}")

# ===================== PDF Text Extraction =====================
def extract_text_from_pdf_bytes(pdf_bytes):
    text = ""
    try:
        with fitz.open("pdf", pdf_bytes) as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        logging.error(f"Error reading PDF: {e}")
    return text

# ===================== Resume Field Extractors =====================
def extract_skills(text):
    found_skills = set()
    words = re.findall(r'\w+', text.lower())
    for skill in SKILL_SET:
        matches = get_close_matches(skill, words, n=1, cutoff=0.8)
        if matches:
            found_skills.add(skill.title())
    return list(found_skills)

def extract_experience(text):
    matches = re.findall(r"(\d+)\s*(\+)?\s*(years|yrs)[\s\w]*experience", text, re.IGNORECASE)
    years = [int(m[0]) for m in matches if m[0].isdigit()]
    return max(years) if years else 0

def extract_education(text):
    return list({k.title() for k in EDUCATION_KEYWORDS if re.search(rf"\b{k}\b", text, re.IGNORECASE)})

def extract_certifications(text):
    certs = re.findall(r"(Certified in [A-Za-z0-9\s&]+|[A-Za-z0-9\s]+(?:Certification|Certified))", text, re.IGNORECASE)
    return list({c.strip() for c in certs})

def extract_project_domains(text):
    return list({d.title() for d in TECH_DOMAINS if re.search(rf"\b{re.escape(d)}\b", text, re.IGNORECASE)})

def extract_email(text):
    match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    return match.group(0) if match else ""

def extract_name(text):
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "PERSON" and len(ent.text.split()) <= 3:
            return ent.text
    return ""

def extract_soft_skills(text):
    return list({s.title() for s in SOFT_SKILLS if s in text.lower()})

def estimate_grammar_score(text):
    blob = TextBlob(text)
    sentences = blob.sentences
    errors = sum(1 for s in sentences if s.correct() != s)
    return round(((len(sentences) - errors) / len(sentences)) * 100, 2) if sentences else 0

# ===================== Main Parse Function =====================
def parse_resume(uploaded_file):
    text = extract_text_from_pdf_bytes(uploaded_file.read())

    parsed = {
        "name": extract_name(text),
        "email": extract_email(text),
        "skills": extract_skills(text),
        "experience": extract_experience(text),
        "education": extract_education(text),
        "certifications": extract_certifications(text),
        "project_domains": extract_project_domains(text),
        "soft_skills": extract_soft_skills(text),
        "grammar_score": estimate_grammar_score(text),
        "text": text.lower()
    }

    return parsed

# ===================== Save & Store Resume =====================
def save_resume(candidate_id, uploaded_file):
    try:
        uploaded_file.seek(0)  # rewind before reading
        parsed = parse_resume(uploaded_file)
        update_parsed_resume_data(candidate_id, parsed)
        logging.info(f"✅ Resume parsed and stored for candidate_id={candidate_id}")
        return True
    except Exception as e:
        logging.error(f"[❌ save_resume] Resume parse error for candidate_id={candidate_id}: {e}")
        return False
