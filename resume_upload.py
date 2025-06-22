import streamlit as st
import tempfile
from resume_parser import parse_resume
from database import (
    save_resume,
    fetch_resume_by_candidate,
    apply_to_job,
    resume_exists_for_candidate,
    has_applied_to_job,
)

# ===========================
# Resume Upload + Apply Page
# ===========================
def upload_resume_ui(candidate_id, candidate_name=None, job_id=None, job_title=None):
    st.subheader("📄 Upload Your Resume")

    # ✅ Check if a resume already exists
    existing = fetch_resume_by_candidate(candidate_id)
    if existing:
        st.info("✅ You have already uploaded a resume. Uploading again will **replace** the previous one.")
        # Hidden: No preview of parsed data

    # --- Upload Resume Section (PDF Only) ---
    uploaded_file = st.file_uploader("Upload Resume (PDF only, Max 100MB)", type=["pdf"])

    if uploaded_file:
        if uploaded_file.size > 100 * 1024 * 1024:
            st.error("❌ File too large. Maximum allowed is 100MB.")
            return

        # ✅ Save to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name

        # ✅ Parse the resume
        with st.spinner("⏳ Parsing your resume..."):
            parsed_data = parse_resume(tmp_path)

            if parsed_data:
                # ✅ Save parsed data in DB
                save_resume(candidate_id, parsed_data)
                st.success("✅ Resume uploaded and parsed successfully!")
                # st.json(parsed_data)  ✅ Commented out to keep parsing hidden

                # --- Apply to job (if job info provided) ---
                if job_id and candidate_name:
                    if has_applied_to_job(candidate_id, job_id):
                        st.info(f"✅ You have already applied for **{job_title}**.")
                    else:
                        apply_to_job(candidate_id, candidate_name, job_id)
                        st.success(f"🎉 Successfully applied for **{job_title}**!")
            else:
                st.error("❌ Failed to parse the resume. Please check the file.")
