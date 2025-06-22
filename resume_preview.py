# resume_preview.py

import streamlit as st
import pdfplumber
import io

def show_resume_preview(file_bytes, file_name):
    # Show download option
    st.download_button("📥 Download Resume", file_bytes, file_name, mime="application/pdf")

    # Show extracted text
    st.markdown("👁️ **Resume Text Preview:**")
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            text = "\n\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        if not text.strip():
            st.warning("⚠️ No text could be extracted from the resume PDF.")
        else:
            st.text_area("Parsed Text", text, height=400)
    except Exception as e:
        st.error("❌ Failed to extract text from PDF.")
        st.exception(e)
