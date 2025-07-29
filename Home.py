import streamlit as st

# Inject custom CSS for professional look and dominant color #00B1A9
st.markdown("""
<style>
/* Main page background and card effect */
section.main > div {background: #FFFFFF; border-radius: 10px; padding: 2rem; box-shadow: 0 2px 8px #00b1a930;}
h1, h2, h3 {color: #00B1A9;}
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

# Optional: Show logo in sidebar if you have 'logo.png'
# st.sidebar.markdown('<div class="sidebar-logo"><img src="logo.png" width="140"></div>', unsafe_allow_html=True)

# Password protection
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Graceful handling if password is not set
correct_password = st.secrets.get("password", None)

if not st.session_state.authenticated:
    with st.form("login_form"):
        st.markdown("#### 🔐 <span style='color:#00B1A9;'>Access Required</span>", unsafe_allow_html=True)
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

# Enhanced Title with animations
st.markdown("""
<style>
@keyframes slideRotate {
    0% { opacity: 0; transform: translateX(-100px) rotate(-10deg); }
    100% { opacity: 1; transform: translateX(0) rotate(0deg); }
}

@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

@keyframes underlineGrow {
    0% { width: 0; opacity: 0; }
    100% { width: 80px; opacity: 1; }
}

@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}

.animated-title {
    animation: slideRotate 1.5s ease-out;
}

.gradient-text {
    background: linear-gradient(135deg, #00B1A9 0%, #00E5D6 50%, #00B1A9 100%);
    background-size: 200% 200%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: gradientShift 3s ease-in-out infinite;
}

.animated-underline {
    animation: underlineGrow 1s ease-out 0.5s both;
}

.emoji-pulse {
    display: inline-block;
    animation: pulse 5s ease-in-out infinite;
}
</style>

<div style="text-align: center; margin: 2rem 0;" class="animated-title">
    <h1 style="
        font-family: 'Segoe UI', 'Roboto', sans-serif;
        font-size: 3.5rem;
        font-weight: 700;
        text-shadow: 0 4px 8px rgba(0, 177, 169, 0.3);
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
    " class="gradient-text">
        💲</span> CE AI Tools </span>💲
    </h1>
    <div style="
        width: 100px;
        height: 4px;
        background: linear-gradient(90deg, #00B1A9, #00E5D6);
        margin: 0 auto;
        border-radius: 2px;
        box-shadow: 0 2px 4px rgba(0, 177, 169, 0.4);
    " class="animated-underline"></div>
</div>
""", unsafe_allow_html=True)

# ✅ FIXED: Using the correct raw GitHub URL for the GIF
gif_url = "https://raw.githubusercontent.com/apizrahman24/Cost-Predictor/main/USD.gif"
st.image(gif_url, use_container_width=True)

# Footer
st.markdown(
    "<div class='footer-div'>"
    "Developed for internal project cost analysis – <b style='color:#00B1A9;'>RT2025</b>"
    "</div>",
    unsafe_allow_html=True
)
