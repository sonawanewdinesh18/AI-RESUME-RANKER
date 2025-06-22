import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import os
import json
import datetime as dt
from dotenv import load_dotenv
import logging
from resume_parser import parse_resume
import datetime

load_dotenv()
logging.basicConfig(level=logging.INFO)

DB_HOST = os.getenv("DB_HOST", "your host name")
DB_NAME = os.getenv("DB_NAME", "your database name ")
DB_USER = os.getenv("DB_USER", "your user name ")
DB_PASSWORD = os.getenv("DB_PASSWORD", "your password name")
DB_PORT = os.getenv("DB_PORT", "your port")

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )

@contextmanager
def get_cursor(dict_cursor=False):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor if dict_cursor else None)
    try:
        yield cur
        conn.commit()
    except Exception as e:
        logging.error("Database error: %s", e)
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

# ------------------- General Queries -------------------

def run_query(query, params=None):
    with get_cursor() as cur:
        cur.execute(query, params)
        if query.strip().upper().startswith("SELECT"):
            return cur.fetchall()
        return None

def execute_query(query, params=None):
    try:
        with get_cursor() as cur:
            cur.execute(query, params)
    except Exception as e:
        logging.error("Execute query error: %s", e)

def fetch_one(query, params=None):
    try:
        with get_cursor(dict_cursor=True) as cur:
            cur.execute(query, params)
            return cur.fetchone()
    except Exception as e:
        logging.error("Fetch one error: %s", e)
        return None

def fetch_all(query, params=None):
    try:
        with get_cursor(dict_cursor=True) as cur:
            cur.execute(query, params)
            return cur.fetchall()
    except Exception as e:
        logging.error("Fetch all error: %s", e)
        return []

# ------------------- User Management -------------------

def get_user_id_by_email(email):
    try:
        with get_cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            result = cur.fetchone()
            return result[0] if result else None
    except Exception as e:
        logging.error("Error fetching user ID: %s", e)
        return None

# ------------------- Resume Handling -------------------

def save_resume(candidate_id, parsed_data, uploaded_file):
    try:
        file_data = uploaded_file.getvalue()
        file_name = uploaded_file.name
        file_size = len(file_data)
        with get_cursor() as cur:
            cur.execute("SELECT 1 FROM resumes WHERE candidate_id = %s", (candidate_id,))
            exists = cur.fetchone()
            if exists:
                cur.execute("""
                    UPDATE resumes SET file_data = %s, file_name = %s, file_size = %s,
                    parsed_data = %s, uploaded_at = %s
                    WHERE candidate_id = %s
                """, (
                    psycopg2.Binary(file_data), file_name, file_size, json.dumps(parsed_data), dt.datetime.now(), candidate_id
                ))
            else:
                cur.execute("""
                    INSERT INTO resumes (candidate_id, file_data, file_name, file_size, parsed_data, uploaded_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    candidate_id, psycopg2.Binary(file_data), file_name, file_size, json.dumps(parsed_data), dt.datetime.now()
                ))
    except Exception as e:
        logging.error("Error saving resume: %s", e)

def get_resume_file_by_candidate_id(candidate_id):
    try:
        with get_cursor() as cur:
            cur.execute("SELECT file_name, file_data FROM resumes WHERE candidate_id = %s", (candidate_id,))
            result = cur.fetchone()
            return {"file_name": result[0], "file_data": bytes(result[1])} if result else None
    except Exception as e:
        logging.error("Error fetching resume file: %s", e)
        return None

def fetch_resume_by_candidate(candidate_id):
    try:
        with get_cursor(dict_cursor=True) as cur:
            cur.execute("SELECT * FROM resumes WHERE candidate_id = %s", (candidate_id,))
            return cur.fetchone()
    except Exception as e:
        logging.error("Error fetching resume: %s", e)
        return None

def has_uploaded_resume(candidate_id):
    try:
        with get_cursor() as cur:
            cur.execute("SELECT file_name FROM resumes WHERE candidate_id = %s", (candidate_id,))
            row = cur.fetchone()
            return row is not None and row[0]
    except Exception as e:
        logging.error("Error checking uploaded resume: %s", e)
        return False

def fetch_resume_text_by_candidate(candidate_id):
    resume = fetch_resume_by_candidate(candidate_id)
    return resume['parsed_data'] if resume else None

def delete_resume_by_candidate(candidate_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM resumes WHERE candidate_id = %s", (candidate_id,))
                conn.commit()
                return True
    except Exception as e:
        print(f"Error deleting resume: {e}")
        return False

# ------------------- Job Handling -------------------

def insert_job(recruiter_id, job_title, job_description, description, company_name, salary, job_type,
               skills, experience_required, education, certifications, perks, num_positions, deadline,
               algorithm_choice, num_resumes_to_shortlist, created_at):

    try:
        with get_cursor() as cur:
            cur.execute("""
                INSERT INTO jobs (recruiter_id, job_title, description, company_name, salary, job_type, skills,
                experience_required, education, certifications, perks, num_positions, deadline,
                algorithm_choice, num_resumes_to_shortlist, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                recruiter_id, job_title, description, company_name, salary, job_type, skills,
                experience_required, education, certifications, perks, num_positions, deadline,
                algorithm_choice, num_resumes_to_shortlist, created_at
            ))
    except Exception as e:
        logging.error("Error inserting job: %s", e)

def fetch_jobs_by_recruiter(recruiter_id):
    try:
        with get_cursor(dict_cursor=True) as cur:
            cur.execute("SELECT * FROM jobs WHERE recruiter_id = %s ORDER BY created_at DESC", (recruiter_id,))
            return cur.fetchall()
    except Exception as e:
        logging.error("Error fetching recruiter jobs: %s", e)
        return []

def get_all_active_jobs():
    try:
        with get_cursor(dict_cursor=True) as cur:
            cur.execute("SELECT * FROM jobs ORDER BY created_at DESC")
            return cur.fetchall()
    except Exception as e:
        logging.error("Error fetching active jobs: %s", e)
        return []
        
# ------------------- Applications -------------------

def apply_to_job(candidate_id, job_id):
    try:
        with get_cursor(dict_cursor=True) as cur:
            cur.execute("SELECT id FROM resumes WHERE candidate_id = %s ORDER BY uploaded_at DESC LIMIT 1", (candidate_id,))
            resume_row = cur.fetchone()
            if not resume_row:
                raise Exception("No resume found for this candidate.")
            resume_id = resume_row['id']
            cur.execute("SELECT 1 FROM applications WHERE candidate_id = %s AND job_id = %s", (candidate_id, job_id))
            if cur.fetchone():
                raise Exception("You have already applied for this job.")
            cur.execute("""
                INSERT INTO applications (candidate_id, job_id, resume_id, applied_at)
                VALUES (%s, %s, %s, %s)
            """, (candidate_id, job_id, resume_id, dt.datetime.now()))
    except Exception as e:
        logging.error("Error applying to job: %s", e)
        raise

def has_candidate_applied(candidate_id, job_id):
    try:
        with get_cursor() as cur:
            cur.execute("SELECT 1 FROM applications WHERE candidate_id = %s AND job_id = %s", (candidate_id, job_id))
            return cur.fetchone() is not None
    except Exception as e:
        logging.error("Error checking application: %s", e)
        return False

def fetch_applications_by_job(job_id):
    try:
        with get_cursor(dict_cursor=True) as cur:
            cur.execute("""
                SELECT 
                    a.*, 
                    u.username AS name, 
                    u.email, 
                    u.phone,  -- ✅ add this
                    r.file_name, 
                    r.file_data, 
                    r.parsed_data
                FROM applications a
                JOIN users u ON a.candidate_id = u.id
                JOIN resumes r ON a.resume_id = r.id
                WHERE a.job_id = %s
                ORDER BY a.applied_at DESC
            """, (job_id,))
            return cur.fetchall()
    except Exception as e:
        logging.error("Error fetching applications with resume: %s", e)
        return []


def get_applied_jobs_by_candidate(candidate_id):
    try:
        with get_cursor(dict_cursor=True) as cur:
            cur.execute("""
                SELECT j.job_title, j.company_name, a.applied_at
                FROM applications a
                JOIN jobs j ON a.job_id = j.id
                WHERE a.candidate_id = %s
                ORDER BY a.applied_at DESC
            """, (candidate_id,))
            return cur.fetchall()
    except Exception as e:
        logging.error("Error fetching applied jobs: %s", e)
        return []

def store_uploaded_resume(candidate_id, uploaded_file):
    if uploaded_file is None:
        logging.warning("📂 No file uploaded for candidate_id=%s", candidate_id)
        return False  # or return None
    try:
        file_data = uploaded_file.getvalue()
        file_name = uploaded_file.name
        file_size = len(file_data)
        uploaded_at = dt.datetime.now()
        parsed_data = parse_resume(uploaded_file)
        uploaded_file.seek(0)
        with get_cursor() as cur:
            cur.execute("SELECT id FROM resumes WHERE candidate_id = %s", (candidate_id,))
            existing = cur.fetchone()
            if existing:
                cur.execute("""
                    UPDATE resumes SET file_data = %s, file_name = %s, file_size = %s,
                    parsed_data = %s, uploaded_at = %s
                    WHERE candidate_id = %s
                """, (
                    psycopg2.Binary(file_data), file_name, file_size,
                    json.dumps(parsed_data), uploaded_at, candidate_id
                ))
            else:
                cur.execute("""
                    INSERT INTO resumes (candidate_id, file_data, file_name, file_size, parsed_data, uploaded_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    candidate_id, psycopg2.Binary(file_data), file_name,
                    file_size, json.dumps(parsed_data), uploaded_at
                ))
    except Exception as e:
        logging.error("Error in store_uploaded_resume: %s", e)
def soft_delete_job(job_id):
    try:
        with get_cursor() as cur:
            cur.execute("UPDATE jobs SET status = 'archived' WHERE id = %s", (job_id,))
        return True
    except Exception as e:
        logging.error(f"Soft delete failed for job {job_id}: {e}")
        return False
def fetch_active_jobs_by_recruiter(recruiter_id):
    return fetch_all("SELECT * FROM jobs WHERE recruiter_id = %s AND status = 'active' ORDER BY created_at DESC", (recruiter_id,))

def fetch_archived_jobs_by_recruiter(recruiter_id):
    return fetch_all("SELECT * FROM jobs WHERE recruiter_id = %s AND status = 'archived' ORDER BY created_at DESC", (recruiter_id,))
def update_job(job_id, job_data):
    try:
        query = """
        UPDATE jobs SET
            job_title = %s,
            company_name = %s,
            salary = %s,
            job_type = %s,
            skills = %s,
            experience_required = %s,
            education = %s,
            certifications = %s,
            perks = %s,
            description = %s,
            num_positions = %s,
            deadline = %s
        WHERE id = %s
        """
        values = (
            job_data['job_title'],
            job_data['company_name'],
            job_data['salary'],
            job_data['job_type'],
            job_data['skills'],
            job_data['experience_required'],
            job_data['education'],
            job_data['certifications'],
            job_data['perks'],
            job_data['description'],
            job_data['num_positions'],
            job_data['deadline'],
            job_id
        )

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(query, values)
            conn.commit()
            return True
        finally:
            cur.close()
            conn.close()

    except Exception as e:
        print("Update Job Error:", e)
        return False
def save_ranking_result(application_id, score):
    query = """
        INSERT INTO rankings (application_id, score, created_at)
        VALUES (%s, %s, %s)
        ON CONFLICT (application_id) DO UPDATE
        SET score = EXCLUDED.score,
            created_at = EXCLUDED.created_at;
    """
    values = (application_id, score, datetime.datetime.now())
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(query, values)
            conn.commit()
        return True
    except Exception as e:
        print(f"[❌ Ranking Save Error] {e}")
        return False    
def count_applications_for_job(job_id):
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM applications WHERE job_id = %s", (job_id,))
            result = cur.fetchone()
            return result[0] if result else 0
    except Exception as e:
        print("Error counting applications:", e)
        return 0
def update_parsed_resume_data(candidate_id, parsed_json):
    """
    Updates the parsed_data field in the resumes table for a given candidate.
    Used by resume_parser.save_resume().
    """
    try:
        with get_cursor() as cur:
            cur.execute("""
                UPDATE resumes
                SET parsed_data = %s, uploaded_at = %s
                WHERE candidate_id = %s
            """, (json.dumps(parsed_json), dt.datetime.now(), candidate_id))
    except Exception as e:
        logging.error(f"[❌ update_parsed_resume_data] Failed for candidate_id={candidate_id}: {e}")
    
