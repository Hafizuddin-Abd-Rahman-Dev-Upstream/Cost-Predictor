import streamlit as st

# Inject custom CSS for professional look and dominant color #00B1A9
st.markdown("""
<style>
/* Main page background and card effect */
section.main > div {background: #FFFFFF; border-radius: 10px; padding: 2rem; box-shadow: 0 2px 8px #00b1a930;}
h1, h2, h3 {color: #00B1A9;}

/* Header animations */
@keyframes fadeInSlideRotate {
    0% { opacity: 0; transform: translateY(-20px) translateX(-100px) rotate(-10deg); }
    100% { opacity: 1; transform: translateY(0) translateX(0) rotate(0deg); }
}

.animated-header {
    animation: fadeInSlideRotate 1.5s ease-out;
}

/* Button styling */
.stButton>button {
    background-color: #00B1A9 !important;
    color: white !important;
    border-radius: 8px !important;
    border: none;
    font-weight: 600;
    padding: 0.6em 2em;
    transition: filter 0.2s;
}
.stButton>button:hover {
    filter: brightness(0.90);
}
/* Text input styling */
.stTextInput>div>input {
    border: 1.5px solid #00B1A9 !important;
    border-radius: 8px !important;
    padding: 0.5em;
}
/* Form background */
.stForm {
    background-color: #E4F9F8 !important;
    padding: 1.5rem !important;
    border-radius: 12px !important;
    box-shadow: 0 1px 4px #00b1a930;
}
/* Alert styling */
.stAlert {
    border-radius: 8px !important;
}
/* Footer */
.footer-div {
    text-align: center;
    color: #555;
    font-size: 0.95em;
    margin-top: 2em;
}
/* Sidebar logo placeholder (optional) */
.sidebar-logo {
    display: flex;
    justify-content: center;
    margin-bottom: 1em;
}
</style>
""", unsafe_allow_html=True)

# Set page config
st.set_page_config(
    page_title="CE AI Tools",
    page_icon="💲",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Password protection
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Graceful handling if password is not set
correct_password = st.secrets.get("password", None)

if not st.session_state.authenticated:
    with st.form("login_form"):
        st.markdown("#### 🔐 Access Required", unsafe_allow_html=True)
        password = st.text_input("Enter Access Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if correct_password is None:
                st.error("🚫 Password not configured. Please contact admin.")
            elif password == correct_password:
                st.session_state.authenticated = True
                st.success("✅ Access granted")
                st.rerun()
            else:
                st.error("❌ Incorrect password")
    st.stop()

# Animated Header with Navy Blue Color (no glow)
st.markdown("""
<div style="text-align: center; margin: 2rem 0;" class="animated-header">
    <h1 style="
        font-family: 'Segoe UI', 'Roboto', sans-serif;
        font-size: 3.5rem;
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 1rem;
        letter-spacing: -1px;
    ">
        💲 CE AI Tools
    </h1>
</div>
""", unsafe_allow_html=True)

# Display logo from GitHub repository
logo_url = "https://raw.githubusercontent.com/apizrahman24/Cost-Predictor/main/logo.png"
st.markdown(
    f"""
    <div style="display: flex; justify-content: center; align-items: center;">
        <img src="{logo_url}" width="300">
    </div>
    """,
    unsafe_allow_html=True
)

# Catchphrase
st.markdown("""
<div style="text-align: center; margin: 1.5rem 0;">
    <p style="font-size: 1.4rem; font-weight: bold; color: #1e3a8a; margin-bottom: 1rem;">
        "Smart Cost Estimation Made Simple"
    </p>
    <p style="font-size: 1.1rem; color: #555; line-height: 1.6;">
        Welcome to the AI-Powered Estimation Tool – streamline your project cost estimation with smart, data-driven predictions.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
---
<p style="font-size: 0.9rem; color: #666; text-align: center;">
    <span style="color:#00B1A9;">🔐 Access Control:</span> Password-protected pages available. Contact administrator for access.
</p>
---
""", unsafe_allow_html=True)

# Footer
st.markdown(
    "<div class='footer-div'>"
    "Developed for internal project cost analysis – <b style='color:#00B1A9;'>RT2025</b>"
    "</div>",
    unsafe_allow_html=True
)
