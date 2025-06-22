import streamlit as st
import hashlib
import time
from database import fetch_one, execute_query

# ------------------- PASSWORD HASHING -------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ------------------- MODAL POPUP -------------------
def show_success_modal(message="Success!"):
    modal_html = f"""
    <div class="modal-overlay">
      <div class="modal">
        <h2>🎉 {message}</h2>
        <p>Redirecting...</p>
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

# ------------------- REGISTER -------------------
def register_user():
    st.markdown('<h2 class="form-heading">📝 Register</h2>', unsafe_allow_html=True)
    username = st.text_input("Username", placeholder="Enter full name (e.g., DINESH SONAWANE)", help="Use your real name for better identification")
    email = st.text_input("Email", placeholder="example@email.com")   
    password = st.text_input("Password", type="password")
    phone = st.text_input("Phone Number")
    role = st.selectbox("Role", ["recruiter", "candidate"])

    if st.button("Register", key="register_btn"):
        if username and email and password and phone:
            if fetch_one("SELECT * FROM users WHERE email=%s", (email,)):
                st.error("❌ User with this email already exists.")
                return False

            password_hash = hash_password(password)
            execute_query(
                "INSERT INTO users (username, email, password_hash, phone, role) VALUES (%s, %s, %s, %s, %s)",
                (username, email, password_hash, phone, role)
            )
            return True  # Registration success
        else:
            st.error("⚠️ Please fill all fields.")
    return False

# ------------------- LOGIN -------------------
def login_user():
    st.markdown('<h2 class="form-heading">🔐 Login</h2>', unsafe_allow_html=True)
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login", key="login_btn"):
        with st.spinner("Authenticating..."):
            password_hash = hash_password(password)
            user = fetch_one("SELECT * FROM users WHERE email=%s AND password_hash=%s", (email, password_hash))

            if user:
                return user  # Login success
            else:
                st.error("❌ Invalid credentials!")
    return None

# ------------------- LOGOUT -------------------
def logout_user():
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.page = "login"
    st.rerun()

# ------------------- FORGOT PASSWORD -------------------
def forgot_password():
    st.markdown('<h2 class="form-heading">🔒 Forgot Password</h2>', unsafe_allow_html=True)
    email = st.text_input("Registered Email", key="reset_email")
    new_pass = st.text_input("New Password", type="password", key="reset_pass")
    confirm_pass = st.text_input("Confirm New Password", type="password", key="confirm_pass")

    if st.button("Reset Password"):
        if not (email and new_pass and confirm_pass):
            st.warning("⚠️ Please fill in all fields.")
            return False

        if new_pass != confirm_pass:
            st.warning("❌ Passwords do not match.")
            return False

        user = fetch_one("SELECT * FROM users WHERE email=%s", (email,))
        if user:
            new_hash = hash_password(new_pass)
            execute_query("UPDATE users SET password_hash=%s WHERE email=%s", (new_hash, email))
            return True  # Reset successful
        else:
            st.error("⚠️ Email not found.")
            return False
    return False

# ------------------- UTILITY -------------------
def get_logged_in_user():
    return st.session_state.get("user")
