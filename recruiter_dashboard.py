import streamlit as st
import pandas as pd
import datetime
from database import (
    insert_job, fetch_active_jobs_by_recruiter, fetch_archived_jobs_by_recruiter,
    soft_delete_job, update_job, count_applications_for_job
)
from auth import get_logged_in_user
from ml_ranking import rank_resumes
from report_generator import generate_pdf_report_with_explanations, generate_csv_report_with_explanations
from resume_preview import show_resume_preview

# ------------------- Constants -------------------
JOB_TYPES = ["Internship", "Full Time", "Part Time", "Work From Home"]
PERKS_OPTIONS = ["Certificate", "Letter of recommendation", "Flexible work hours", "5 days a week"]
SALARY_RANGES = ["< ₹10,000", "₹10,000 - ₹25,000", "₹25,000 - ₹50,000", "₹50,000 - ₹1,00,000", "> ₹1,00,000"]
CERTIFICATE_SUGGESTIONS = [
    "Adobe Certified Professional",
    "AI For Everyone - Coursera",
    "AWS Certified Cloud Practitioner",
    "AWS Certified Machine Learning – Specialty",
    "Basic C Programming Certificate",
    "Basic Java Programming Certificate",
    "Beginner Python Certificate",
    "CEH (Certified Ethical Hacker)",
    "Cloudera Certified Associate (CCA)",
    "CompTIA Security+",
    "Coursera Introduction to Machine Learning",
    "Coursera Machine Learning",
    "Coursera Python for Everybody",
    "Coursera UI Design Fundamentals",
    "DataCamp Data Analyst with Python",
    "DataCamp Data Scientist",
    "DataCamp Introduction to SQL",
    "DataCamp SQL",
    "DeepLearning.AI Specialization",
    "DevOps Foundation Certification",
    "Docker Essentials",
    "edX Python Basics for Data Science",
    "Figma Design Basics",
    "Fortinet NSE 1",
    "GitHub Git Essentials",
    "Google Android Developer",
    "Google BigQuery Certification",
    "Google Cloud Digital Leader",
    "Google Cybersecurity Certificate",
    "Google Data Analytics",
    "Google UX Design Certificate",
    "Harvard CS50",
    "IBM AI Engineering Certificate",
    "IBM Cybersecurity Analyst",
    "IBM Data Science Professional",
    "LinkedIn Learning: SQL Essential Training",
    "LinkedIn Time Management",
    "Meta Front-End Developer",
    "Microsoft Azure Fundamentals",
    "Microsoft C# Certification",
    "MongoDB Developer Certification",
    "NPTEL Artificial Intelligence",
    "NPTEL Cyber Security",
    "NPTEL Introduction to C Programming",
    "NPTEL Introduction to Java Programming",
    "NPTEL Machine Learning",
    "NPTEL Python",
    "NPTEL Soft Skills",
    "Oracle Database SQL Certified Associate",
    "Oracle Java Certified",
    "Project Management Professional (PMP)",
    "Scrum Master Certification",
    "Simplilearn AI for Beginners",
    "Simplilearn Introduction to Python",
    "SoloLearn C Programming",
    "SoloLearn Java",
    "SoloLearn Python",
    "TensorFlow Developer Certificate",
    "Terraform Associate",
    "Udacity AI Programming with Python",
    "Udemy Graphic Design Masterclass",
    "Udemy Introduction to SQL",
    "Udemy Leadership Mastery",
    "Udemy Machine Learning A-Z",
    "Udemy Web Development Bootcamp"
]

EDUCATION_LEVELS = [
    "High School", "Diploma", "Bachelor's", "B.Tech", "B.E", "BCA", "BSc", "BBA",
    "Master's", "M.Tech", "MCA", "MSc", "MBA", "PhD"
]
ALL_SKILLS = sorted(set([
    # --- Technical Skills ---
    "AI", "Android Development", "Angular", "Artificial Intelligence", "AWS", "Azure",
    "Backend", "Canva", "C", "C#", "C++", "Cloud", "CSS", "CV", "Data Science",
    "Deep Learning", "DevOps", "Django", "Docker", "Excel", "Express", "Firebase",
    "Flask", "Figma", "Frontend", "Full Stack", "GCP", "Git", "GitHub", "GitLab",
    "Heroku", "HTML", "iOS Development", "Java", "JavaScript", "Jira", "Keras",
    "Kubernetes", "Linux", "Machine Learning", "Matplotlib", "ML", "MongoDB", "MySQL",
    "Natural Language Processing", "Node.js", "NLP", "NumPy", "OpenCV", "Pandas",
    "PostgreSQL", "Power BI", "Python", "PyTorch", "React", "Scikit-learn", "Seaborn",
    "Spacy", "SQL", "Tableau", "TensorFlow", "TreIIo", "TypeScript", "Vue", "Web Development",

    # --- Soft Skills ---
    "Adaptability", "Attention to Detail", "Communication", "Creativity", "Critical Thinking",
    "Decision Making", "Emotional Intelligence", "Leadership", "Multi-tasking", "Negotiation",
    "Organizational Skills", "Problem Solving", "Public Speaking", "Self-Motivation",
    "Strategic Thinking", "Teamwork", "Time Management", "Work Ethic"
]))


# ------------------- Recruiter Panel -------------------
def recruiter_panel():
    user = get_logged_in_user()
    if not user:
        st.warning("Please login to access recruiter dashboard.")
        return

    st.title(f"🧑‍💼 Welcome, {user['username']}")
    with st.expander("📜 POST A NEW JOB"):
        col1, col2 = st.columns(2)
        with col1:
            job_title = st.text_input("Job Title")
        with col2:
            company_name = st.text_input("Company Name")

        salary = st.selectbox("Salary Range", SALARY_RANGES)
        job_type = st.selectbox("Job Type", JOB_TYPES)
        skills = st.multiselect("Skills Required", ALL_SKILLS)
        experience_required = st.selectbox("Experience Required", ["Fresher", "0-1 Years", "1-3 Years", "3+ Years"])
        education = st.multiselect("Minimum Education", EDUCATION_LEVELS)
        certifications = st.multiselect("Preferred Certifications", CERTIFICATE_SUGGESTIONS)
        perks = st.multiselect("Perks", PERKS_OPTIONS)
        job_description = st.text_area("📝 Job Description", placeholder="Describe responsibilities, tech stack, etc.")
        about_company = st.text_area("About Company")
        num_hiring = st.number_input("Number of Positions", min_value=1, step=1)
        deadline = st.date_input("Application Deadline", min_value=datetime.date.today())

        if st.button("📄 Post Job"):
            if not all([job_title, company_name, salary, job_type, skills, experience_required,
                        education, about_company, num_hiring, deadline, job_description.strip()
     ]):
                st.error("❗ Please fill all required fields.")
            else:
                insert_job(
                    recruiter_id=user['id'],
                    job_title=job_title,
                    job_description=job_description.strip(),
                    description=about_company,
                    company_name=company_name,
                    salary=salary,
                    job_type=job_type,
                    skills=", ".join(skills),
                    experience_required=experience_required,
                    education=education,
                    certifications=", ".join(certifications),
                    perks=", ".join(perks),
                    num_positions=num_hiring,
                    deadline=deadline,
                    algorithm_choice="",
                    num_resumes_to_shortlist=0, 
                    created_at=datetime.datetime.now()
                )
                st.success("✅ Job posted successfully!")
                st.rerun()

    active_jobs = fetch_active_jobs_by_recruiter(user['id'])
    archived_jobs = fetch_archived_jobs_by_recruiter(user['id'])

    toggle = st.radio("📂 View Jobs", ["Active", "Archived"], horizontal=True)
    jobs_to_show = active_jobs if toggle == "Active" else archived_jobs

    if not jobs_to_show:
        st.info(f"No {toggle.lower()} jobs found.")
        return

    for job in jobs_to_show:
        with st.container(border=True):
            st.markdown(f"### 📄 {job['job_title']} at {job['company_name']}")
            application_count = count_applications_for_job(job['id'])
            st.markdown(f"👥 <b>Total Applicants Applying To Job:</b> {application_count}", unsafe_allow_html=True)
            st.markdown(f"📝 <i>{job['description'][:200]}</i>", unsafe_allow_html=True)
            st.markdown(f"🎯 <b>Skills:</b> {job['skills']} | 💰 <b>Salary:</b> {job['salary']} | 📅 Deadline: {job['deadline']}", unsafe_allow_html=True)

            with st.expander("🔍 Rank Candidates", expanded=True):
                job_skills_list = job['skills'].split(", ") if isinstance(job['skills'], str) else job['skills']
                dynamic_skills = sorted(list(set(ALL_SKILLS + job_skills_list)))

                required_skills = st.multiselect("Required Skills", dynamic_skills, default=job_skills_list, key=f"skills_{job['id']}")
                required_certifications = st.multiselect("Required Certifications", CERTIFICATE_SUGGESTIONS, key=f"certs_{job['id']}")
                project_domains = st.multiselect("Relevant Project Domains", dynamic_skills, key=f"proj_{job['id']}")
                min_experience = st.number_input("Minimum Experience (Years)", min_value=0, max_value=20, value=0, step=1, key=f"exp_{job['id']}")
                num_shortlist = st.number_input("Number of Candidates to Shortlist", min_value=1, max_value=100, value=5, step=1, key=f"shortlist_{job['id']}")

                if st.button(f"⚙️ Rank Resumes - {job['job_title']}", key=f"rank_btn_{job['id']}"):
                    with st.spinner("Processing resumes using Hybrid Model..."):
                        filters = {
    "required_skills": ["python", "sql"],
    "certifications": ["nptel python", "machine learning"],
    "project_domains": ["data science"],
    "education": "btech",
    "min_experience": 1,
    "job_description": job.get("description", ""),    "num_shortlist": num_shortlist,
    "weight_rule": 0.6,     # Optional
    "weight_bert": 0.4      # Optional
}
 


                        ranked_candidates = rank_resumes(job_id=job['id'], filters=filters)

                        if ranked_candidates:
                            st.success("✅ Resumes ranked using Hybrid model successfully!")
                            for idx, candidate in enumerate(ranked_candidates, 1):
                                skills = ', '.join(candidate.get('parsed_data', {}).get('skills', []))
                                file_name = candidate.get("file_name", f"resume_{candidate.get('id', idx)}.pdf")
                                file_data = candidate.get("file_data")
                                file_bytes = bytes(file_data)
                                email = candidate.get('email', '')
                                phone = candidate.get('phone', '')
                                name = candidate.get('name', '')
                                match_score = f"{candidate.get('match_score', 0)}%"
                                explanation = candidate.get("explanation", "No explanation available.")

                                st.markdown(f"**Rank {idx}: {name}**")
                                col1, col2, col3, col4 = st.columns([3, 3, 2, 2])
                                col1.markdown(f"**Email:** {email}")
                                col2.markdown(f"**Phone:** {phone}")
                                col3.markdown(f"**Score:** {match_score}")
                                col4.download_button("📅 Download", data=file_bytes, file_name=file_name, mime="application/pdf", key=f"download_{candidate['id']}")
                                st.markdown(f"**Skills:** {skills}")
                                with st.expander(f"📓 Preview Resume - {name}"):
                                    show_resume_preview(file_bytes, file_name)
                                with st.expander(f"📒 Explanation - Why Ranked {idx}"):
                                    st.markdown(explanation)

                            col1, col2 = st.columns(2)
                            col1.download_button("📄 Download PDF Report", generate_pdf_report_with_explanations(job['job_title'], ranked_candidates), file_name=f"{job['job_title'].replace(' ', '_')}_Ranking_Report.pdf", mime="application/pdf")
                            col2.download_button("📄 Download CSV Report", generate_csv_report_with_explanations(job['job_title'], ranked_candidates), file_name=f"{job['job_title'].replace(' ', '_')}_Ranking_Report.csv", mime="text/csv")
                        else:
                            st.warning("❗ No applications or matching resumes found.")


            with st.expander("✏️ Edit Job"):
                col1, col2 = st.columns(2)
                with col1:
                    title = st.text_input("Job Title", value=job['job_title'], key=f"edit_title_{job['id']}")
                    company = st.text_input("Company Name", value=job['company_name'], key=f"edit_company_{job['id']}")
                    salary = st.selectbox("Salary Range", SALARY_RANGES, index=SALARY_RANGES.index(job['salary']), key=f"edit_salary_{job['id']}")
                    job_type = st.selectbox("Job Type", JOB_TYPES, index=JOB_TYPES.index(job['job_type']), key=f"edit_type_{job['id']}")
                    experience = st.selectbox("Experience Required", ["Fresher", "0-1 Years", "1-3 Years", "3+ Years"], index=["Fresher", "0-1 Years", "1-3 Years", "3+ Years"].index(job['experience_required']), key=f"edit_exp_{job['id']}")
                    education = st.selectbox("Education", EDUCATION_LEVELS, index=EDUCATION_LEVELS.index(job['education']), key=f"edit_edu_{job['id']}")
                with col2:
                    skills = st.multiselect("Skills", ALL_SKILLS, default=job['skills'].split(', '), key=f"edit_skills_{job['id']}")
                    certs = st.multiselect("Certifications", CERTIFICATE_SUGGESTIONS, default=job['certifications'].split(', ') if job['certifications'] else [], key=f"edit_certs_{job['id']}")
                    perks = st.multiselect("Perks", PERKS_OPTIONS, default=job['perks'].split(', ') if job['perks'] else [], key=f"edit_perks_{job['id']}")
                    desc = st.text_area("About Company", value=job['description'], key=f"edit_desc_{job['id']}")
                    num = st.number_input("Number of Positions", min_value=1, value=job['num_positions'], key=f"edit_num_{job['id']}")
                    deadline = st.date_input("Deadline", value=job['deadline'], key=f"edit_deadline_{job['id']}")
                if st.button("💾 Save Changes", key=f"save_{job['id']}"):
                    updated = {
                        "job_title": title,
                        "company_name": company,
                        "salary": salary,
                        "job_type": job_type,
                        "skills": ", ".join(skills),
                        "experience_required": experience,
                        "education": education,
                        "certifications": ", ".join(certs),
                        "perks": ", ".join(perks),
                        "description": desc,
                        "num_positions": num,
                        "deadline": deadline
                    }
                    if update_job(job['id'], updated):
                        st.success("✅ Job updated successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update job.")

            if toggle == "Active":
                with st.popover("🗑️ Archive Job", use_container_width=True):
                    st.warning("This job will be moved to archived list.")
                    if st.button("✅ Confirm Archive", key=f"confirm_{job['id']}"):
                        if soft_delete_job(job['id']):
                            st.success("✅ Job archived.")
                            st.rerun()
                        else:
                            st.error("❌ Failed to archive.")
            else:
                st.info("🗃️ Archived")
