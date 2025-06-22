import streamlit as st
from PIL import Image
import os
import time

# Custom Modules
from auth import login_user, register_user, forgot_password
from recruiter_dashboard import recruiter_panel
from candidate_dashboard import candidate_panel

# ------------------- PAGE CONFIG -------------------
st.set_page_config(page_title="AI Resume Ranker", layout="wide")

# ------------------- LOAD CUSTOM CSS -------------------
def load_css(file_path):
    if os.path.exists(file_path):
        with open(file_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("styles.css")

# ------------------- SESSION INIT -------------------
if "page" not in st.session_state:
    st.session_state.page = "login"
if "user" not in st.session_state:
    st.session_state.user = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ------------------- HEADER -------------------
st.markdown('<h1 class="main-heading">🧠 AI Resume Screener & Ranker</h1>', unsafe_allow_html=True)

# ------------------- MODAL -------------------
def show_success_modal(message="Success!", sub="Redirecting..."):
    modal_html = f"""
    <div class="modal-overlay">
      <div class="modal">
        <h2>🎉 {message}</h2>
        <p>{sub}</p>
      </div>
    </div>
    <style>
        .modal-overlay {{
            position: fixed;
            top: 0; left: 0;
            width: 100vw; height: 100vh;
            background: rgba(0, 0, 0, 0.6);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        }}
        .modal {{
            background: white;
            padding: 2rem 3rem;
            border-radius: 12px;
            text-align: center;
            font-family: sans-serif;
            box-shadow: 0 8px 16px rgba(0,0,0,0.25);
            animation: fadeIn 0.5s ease-in-out;
        }}
        @keyframes fadeIn {{
            from {{ transform: scale(0.8); opacity: 0; }}
            to {{ transform: scale(1); opacity: 1; }}
        }}
    </style>
    """
    st.markdown(modal_html, unsafe_allow_html=True)

# ------------------- SIDEBAR MENU -------------------
with st.sidebar:
    logo_path = os.path.join("static", "LOGO.png")
    if os.path.exists(logo_path):
        st.image(Image.open(logo_path), use_container_width=True)

    st.markdown("<h2 style='text-align:center; color:#0077b6;'>MENU</h2><hr>", unsafe_allow_html=True)

    if st.session_state.user:
        st.markdown(f"**👤 Logged in as:** `{st.session_state.user['username']}`")
        if st.button("🚪 Logout", key="logout-btn"):
            st.session_state.page = "login"
            st.session_state.user = None
            st.session_state.logged_in = False
            st.rerun()
    else:
        menu = st.selectbox("🔐 Select Option", ["Login", "Register", "Forgot Password"])
        st.session_state.page = menu.lower().replace(" ", "_")

# ------------------- AUTH ROUTES -------------------
if not st.session_state.logged_in:
    page = st.session_state.page

    if page == "login":
        user = login_user()
        if user:
            st.session_state.user = user
            st.session_state.logged_in = True
            st.session_state.page = user['role']
            show_success_modal("Login Successful", "Redirecting to dashboard...")
            time.sleep(2)
            st.rerun()

    elif page == "register":
        registered = register_user()
        if registered:
            show_success_modal("Registration Successful!", "Redirecting to login...")
            time.sleep(2)
            st.session_state.page = "login"
            st.rerun()

    elif page == "forgot_password":
        reset_successful = forgot_password()
        if reset_successful:
            show_success_modal("Password Reset Successful!", "Redirecting to login...")
            time.sleep(2)
            st.session_state.page = "login"
            st.rerun()

# ------------------- DASHBOARDS -------------------
elif st.session_state.logged_in and st.session_state.user:
    role = st.session_state.user.get("role")
    user_id = st.session_state.user.get("id")
    username = st.session_state.user.get("username")

    if role == "candidate":
        candidate_panel(candidate_id=user_id, candidate_name=username)
    elif role == "recruiter":
        recruiter_panel()
    else:
        st.error("❌ Invalid role detected. Please contact support.")

# ------------------- FALLBACK -------------------
else:
    st.warning("⚠️ Something went wrong with the page routing. Try refreshing.")
