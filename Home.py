import streamlit as st

# ============================
# PAGE CONFIG (MUST BE FIRST)
# ============================
st.set_page_config(
    page_title="CE AI Tools",
    page_icon="💲",
    layout="centered",
    initial_sidebar_state="expanded"
)

PETRONAS_TEAL = "#00B2A9"
PETRONAS_NAVY = "#003A5D"
PETRONAS_DARK = "#002B36"

# ============================
# CSS (keep your glow + transitions)
# ============================
st.markdown(f"""
<style>
.stApp {{
    background:
      radial-gradient(circle at 20% 20%, rgba(0,178,169,0.20), transparent 45%),
      radial-gradient(circle at 80% 30%, rgba(0,58,93,0.25), transparent 50%),
      radial-gradient(circle at 50% 85%, rgba(0,178,169,0.18), transparent 55%),
      linear-gradient(135deg, {PETRONAS_DARK}, {PETRONAS_NAVY});
    position: relative;
    overflow: hidden;
}}
.stApp::before,.stApp::after {{
    content: "";
    position: fixed;
    inset: -20%;
    z-index: 0;
    filter: blur(40px);
    opacity: 0.75;
    pointer-events: none;
}}
.stApp::before {{
    background:
      radial-gradient(circle at 30% 30%, rgba(0,178,169,0.55), transparent 55%),
      radial-gradient(circle at 70% 45%, rgba(0,58,93,0.45), transparent 60%),
      radial-gradient(circle at 55% 80%, rgba(0,178,169,0.35), transparent 55%);
    animation: glowA 14s ease-in-out infinite;
}}
.stApp::after {{
    background:
      radial-gradient(circle at 65% 25%, rgba(0,178,169,0.35), transparent 55%),
      radial-gradient(circle at 25% 70%, rgba(0,58,93,0.40), transparent 60%);
    animation: glowB 18s ease-in-out infinite;
    mix-blend-mode: screen;
}}
@keyframes glowA {{
    0% {{ transform: translate(-2%, -1%) scale(1.02); }}
    50% {{ transform: translate(2%, 2%) scale(1.08); }}
    100% {{ transform: translate(-2%, -1%) scale(1.02); }}
}}
@keyframes glowB {{
    0% {{ transform: translate(2%, 1%) scale(1.03); }}
    50% {{ transform: translate(-2%, -2%) scale(1.08); }}
    100% {{ transform: translate(2%, 1%) scale(1.03); }}
}}
section.main > div {{
    position: relative;
    z-index: 1;
    background: rgba(255,255,255,0.72);
    border-radius: 22px;
    padding: 2.4rem;
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border: 1px solid rgba(255,255,255,0.25);
    box-shadow: 0 30px 70px rgba(0,0,0,0.28);
}}
@keyframes pageFadeUp {{
  from {{ opacity: 0; transform: translateY(12px) scale(0.995); }}
  to   {{ opacity: 1; transform: translateY(0) scale(1); }}
}}
@keyframes pageSlideLeft {{
  from {{ opacity: 0; transform: translateX(14px); }}
  to   {{ opacity: 1; transform: translateX(0); }}
}}
.page-transition {{ animation: pageFadeUp 420ms cubic-bezier(.2,.8,.2,1); }}
.page-transition.left {{ animation: pageSlideLeft 420ms cubic-bezier(.2,.8,.2,1); }}

/* IMPORTANT: don't hide sidebar collapse button while debugging */
section[data-testid="stSidebar"] > div {{
    background: rgba(0, 43, 54, 0.38);
    backdrop-filter: blur(16px);
}}
</style>
""", unsafe_allow_html=True)

# ============================
# ROUTER
# ============================
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "transition_dir" not in st.session_state:
    st.session_state.transition_dir = "up"

def go(page_name: str, direction: str = "up"):
    st.session_state.page = page_name
    st.session_state.transition_dir = direction
    st.rerun()

# ============================
# AUTH (FIXED: safe fallbacks + clear errors)
# ============================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# These will be [] / None if secrets not configured
APPROVED_EMAILS = st.secrets.get("emails", [])
PASSWORD = st.secrets.get("password", None)

# Dev fallback (so you can still use the app locally)
DEV_MODE = False  # set True for local testing
DEV_EMAIL = "test@petronas.com"
DEV_PASSWORD = "1234"

if DEV_MODE:
    APPROVED_EMAILS = [DEV_EMAIL]
    PASSWORD = DEV_PASSWORD

if not st.session_state.authenticated:
    st.markdown("## 🔐 Secure Access")
    st.markdown("---")

    # Show helpful message if secrets missing
    if (not DEV_MODE) and (PASSWORD is None or APPROVED_EMAILS == []):
        st.error("Auth secrets are not configured. Add them to `.streamlit/secrets.toml` (or enable DEV_MODE).")
        st.code(
            """
# .streamlit/secrets.toml
password = "your_password"
emails = ["user1@petronas.com", "user2@petronas.com"]
            """.strip()
        )

    with st.form("login"):
        email = st.text_input("Email")
        pwd = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if email in APPROVED_EMAILS and PASSWORD is not None and pwd == PASSWORD:
                st.session_state.authenticated = True
                st.success("Access granted")
                st.rerun()
            else:
                st.error("Invalid credentials")

    st.stop()

# ============================
# SIDEBAR NAV
# ============================
with st.sidebar:
    st.markdown("### Navigation")
    if st.button("🏠 Home"):
        go("Home", "up")
    if st.button("🧮 Cost Estimator"):
        go("Estimator", "left")
    if st.button("📚 Reference"):
        go("Reference", "left")
    if st.button("ℹ️ About"):
        go("About", "up")

    st.markdown("---")
    if st.button("🔓 Logout"):
        st.session_state.authenticated = False
        st.rerun()

# ============================
# PAGE CONTENT (transition wrapper)
# ============================
transition_class = "page-transition left" if st.session_state.transition_dir == "left" else "page-transition"
st.markdown(f"<div class='{transition_class}'>", unsafe_allow_html=True)

if st.session_state.page == "Home":
    st.markdown(
        """
        <div style="text-align:center;">
          <h1>💲 CE AI Tools</h1>
          <p>AI-powered cost estimation platform for internal engineering use</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    logo_url = "https://raw.githubusercontent.com/apizrahman24/Cost-Predictor/main/logo.png"
    st.markdown(f"<div style='text-align:center; margin-top:10px;'><img src='{logo_url}' width='280'></div>", unsafe_allow_html=True)

elif st.session_state.page == "Estimator":
    st.markdown("## 🧮 Cost Estimator")
    with st.form("estimator_form"):
        a = st.number_input("Input A", value=10.0)
        b = st.number_input("Input B", value=5.0)
        submitted = st.form_submit_button("Run Estimate")
    if submitted:
        st.success(f"Estimated Cost: **RM {a*b:,.2f}**")

elif st.session_state.page == "Reference":
    st.markdown("## 📚 Reference")
    st.info("Put your reference tables, standards, and guidance notes here.")

elif st.session_state.page == "About":
    st.markdown("## ℹ️ About")
    st.write("Developed by Cost Engineering – DFEE • RT2025")

st.markdown("</div>", unsafe_allow_html=True)
