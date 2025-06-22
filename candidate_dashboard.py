import streamlit as st

from database import (
    store_uploaded_resume,
    get_resume_file_by_candidate_id,
    get_applied_jobs_by_candidate,
    get_all_active_jobs,
    has_candidate_applied,
    apply_to_job,
    fetch_resume_by_candidate,
    has_uploaded_resume,
    delete_resume_by_candidate
)
from resume_parser import save_resume
from resume_preview import show_resume_preview


def candidate_panel(candidate_id, candidate_name):
    st.title(f"👤 Welcome, {candidate_name}")
    st.subheader("📄 Upload, View or Delete Resume")

    # Upload Section
    with st.expander("📤 Upload or Replace Resume", expanded=True):
        resume_already_uploaded = has_uploaded_resume(candidate_id)
        if resume_already_uploaded:
            st.info("📌 Resume already uploaded. You can replace it below.")
        else:
            st.info("🔄 Upload your resume (PDF Only).")

        uploaded_file = st.file_uploader("Upload Resume (PDF only, Max 100MB)", type=["pdf"])

        if uploaded_file:
            with st.spinner("⏳ Uploading and parsing resume... Please wait."):
                uploaded_file.seek(0)
                store_uploaded_resume(candidate_id, uploaded_file)
                uploaded_file.seek(0)
                success = save_resume(candidate_id, uploaded_file)

            if success:
                st.success("✅ Resume uploaded and parsed successfully.")
                st.rerun()
            else:
                st.error("❌ Failed to parse resume. Please try again.")



    # Resume Preview Section
    with st.expander("📂 View or Manage Uploaded Resume", expanded=True):
        resume_data = get_resume_file_by_candidate_id(candidate_id)
        if resume_data and resume_data["file_data"] and resume_data["file_name"]:
            try:
                file_bytes = bytes(resume_data["file_data"])
                file_name = resume_data["file_name"]
                show_resume_preview(file_bytes, file_name)
                st.markdown("---")
                if st.button("🗑️ Delete Uploaded Resume", use_container_width=True):
                    deleted = delete_resume_by_candidate(candidate_id)
                    if deleted:
                        st.success("🗑️ Resume deleted successfully.")
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete resume. Please try again.")
            except Exception as e:
                st.error("⚠️ Error rendering resume preview.")
                st.exception(e)
        else:
            st.warning("⚠️ No resume found. Please upload one.")

    # Applied Jobs Section
    st.markdown("## 🧾 <u><b>Jobs You've Applied For</b></u>", unsafe_allow_html=True)
    applied_jobs = get_applied_jobs_by_candidate(candidate_id)
    if applied_jobs:
        for job in applied_jobs:
            st.markdown(f"""
                <div style='padding: 5px 10px; border: 1px solid #ccc; border-radius: 6px; margin-bottom: 10px;'>
                🏢 <b>{job['job_title']}</b> at <b>{job['company_name']}</b><br>
                📅 <i>Applied on:</i> <b>{job['applied_at'].strftime('%d %b %Y')}</b>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("ℹ️ You haven't applied to any jobs yet.")

    # Job Listings
    st.subheader("💼 Browse Available Jobs")
    jobs = get_all_active_jobs()
    if jobs:
        for job in jobs:
            with st.container():
                st.markdown(f"### <b>🔹 {job['job_title']} at {job['company_name']}</b>", unsafe_allow_html=True)
                st.markdown(f"""
                    <ul style="margin-top:0">
                        <li><b>💰 Salary:</b> {job['salary']}</li>
                        <li><b>🎯 Skills:</b> {job['skills']}</li>
                        <li><b>🎓 Education:</b> {job['education']}</li>
                        <li><b>👥 Positions:</b> {job['num_positions']}</li>
                        <li><b>📅 Deadline:</b> {job['deadline']}</li>
                    </ul>
                """, unsafe_allow_html=True)

                # Align More Details (left) and Apply button (right)
                col1, col2 = st.columns([5, 1])
                with col1:
                    with st.expander("📄 More Details", expanded=False):
                        st.markdown(f"### 📌 {job.get('job_title', 'N/A')} at {job.get('company_name', 'N/A')}", unsafe_allow_html=True)
                        st.markdown(f"**📝 Description:** {job.get('description', 'N/A')}")
                        st.markdown(f"**🧠 Experience Required:** {job.get('experience_required', 'N/A')}")
                        st.markdown(f"**🎓 Education Level:** {job.get('education', 'N/A')}")
                        st.markdown(f"**🧾 Skills Required:** {job.get('skills', 'N/A')}")
                        st.markdown(f"**📜 Preferred Certifications:** {job.get('certifications', 'N/A')}")
                        st.markdown(f"**🎁 Perks:** {job.get('perks', 'N/A')}")
                        st.markdown(f"**👥 Positions Available:** {job.get('num_positions', 'N/A')}")
                        st.markdown(f"**💰 Salary Offered:** {job.get('salary', 'N/A')}")
                        st.markdown(f"**⏳ Application Deadline:** {job.get('deadline', 'N/A')}")

                with col2:
                    already_applied = has_candidate_applied(candidate_id, job['id'])
                    if already_applied:
                        st.success("✅ Already Applied")
                    else:
                        if not fetch_resume_by_candidate(candidate_id):
                            st.warning("⚠️ Upload your resume to apply.")
                        else:
                            if st.button("🚀 Apply", key=f"apply_{job['id']}"):
                                try:
                                    apply_to_job(candidate_id, job['id'])
                                    st.success("✅ Application submitted!")
                                    st.rerun()
                                except Exception as e:
                                    st.error("❌ Failed to apply.")
                                    st.exception(e)
    else:
        st.info("ℹ️ No jobs currently available.")
