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

# ============================
# PETRONAS THEME COLORS
# ============================
PETRONAS_TEAL = "#00B2A9"
PETRONAS_NAVY = "#003A5D"
PETRONAS_DARK = "#002B36"

# ============================
# GLOBAL CSS (Glow + Transitions)
# ============================
st.markdown(f"""
<style>

/* ============================
   🌌 PETRONAS GLOW BACKGROUND
   ============================ */
.stApp {{
    background:
      radial-gradient(circle at 20% 20%, rgba(0,178,169,0.20), transparent 45%),
      radial-gradient(circle at 80% 30%, rgba(0,58,93,0.25), transparent 50%),
      radial-gradient(circle at 50% 85%, rgba(0,178,169,0.18), transparent 55%),
      linear-gradient(135deg, {PETRONAS_DARK}, {PETRONAS_NAVY});
    position: relative;
    overflow: hidden;
}}

.stApp::before,
.stApp::after {{
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

/* ============================
   GLASS MAIN CONTAINER
   ============================ */
section.main > div {{
    position: relative;
    z-index: 1;
    background: rgba(255,255,255,0.72);
    border-radius: 22px;
    padding: 2.4rem;
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border: 1px solid rgba(255,255,255,0.25);
    box-shadow:
      0 30px 70px rgba(0,0,0,0.28),
      0 0 0 1px rgba(0,178,169,0.12);
}}

/* ============================
   PAGE TRANSITIONS
   ============================ */
@keyframes pageFadeUp {{
  from {{ opacity: 0; transform: translateY(12px) scale(0.995); }}
  to   {{ opacity: 1; transform: translateY(0) scale(1); }}
}}
@keyframes pageSlideLeft {{
  from {{ opacity: 0; transform: translateX(14px); }}
  to   {{ opacity: 1; transform: translateX(0); }}
}}
.page-transition {{
  animation: pageFadeUp 420ms cubic-bezier(.2,.8,.2,1);
  will-change: transform, opacity;
}}
.page-transition.left {{
  animation: pageSlideLeft 420ms cubic-bezier(.2,.8,.2,1);
}}

/* ============================
   SIDEBAR GLASS
   ============================ */
section[data-testid="stSidebar"] > div {{
    position: relative;
    z-index: 1;
    background: rgba(0, 43, 54, 0.38);
    backdrop-filter: blur(16px);
    border-right: 1px solid rgba(255,255,255,0.10);
}}
section[data-testid="stSidebar"] button[aria-label="Collapse sidebar"] {{
    display: none !important;
}}

/* ============================
   TYPOGRAPHY
   ============================ */
h1, h2, h3 {{
    color: {PETRONAS_NAVY};
    letter-spacing: -0.6px;
}}
p {{
    color: rgba(0,0,0,0.65);
}}

/* ============================
   SHIMMER DIVIDER
   ============================ */
@keyframes shimmer {{
    0% {{ background-position: -200% 0; }}
    100% {{ background-position: 200% 0; }}
}}
.shimmer {{
    height: 4px;
    width: 100%;
    border-radius: 999px;
    margin: 1.4rem 0 1.8rem 0;
    background: linear-gradient(
        90deg,
        transparent,
        rgba(0,178,169,0.95),
        white,
        rgba(0,178,169,0.95),
        transparent
    );
    background-size: 200% 100%;
    animation: shimmer 2.8s linear infinite;
}}

/* ============================
   BUTTONS
   ============================ */
.stButton > button {{
    background: linear-gradient(135deg, {PETRONAS_TEAL}, {PETRONAS_NAVY});
    color: white !important;
    font-weight: 750;
    border-radius: 14px;
    padding: 0.78em 1.55em;
    border: 1px solid rgba(255,255,255,0.18);
    box-shadow:
      0 16px 34px rgba(0,0,0,0.30),
      0 0 28px rgba(0,178,169,0.22);
    transition: all 0.18s ease;
}}
.stButton > button:hover {{
    transform: translateY(-3px) scale(1.02);
    box-shadow:
      0 22px 46px rgba(0,0,0,0.35),
      0 0 34px rgba(0,178,169,0.30);
}}

/* Hide Streamlit icons */
[data-testid="stShareButton"],
[data-testid="stFavoriteButton"] {{
    display: none !important;
}}

</style>
""", unsafe_allow_html=True)

# ============================
# SIMPLE "ROUTER" FOR PAGES
# ============================
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "transition_dir" not in st.session_state:
    st.session_state.transition_dir = "up"  # or "left"

def go(page_name: str, direction: str = "up"):
    st.session_state.page = page_name
    st.session_state.transition_dir = direction
    st.rerun()

# ============================
# AUTH
# ============================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

APPROVED_EMAILS = st.secrets.get("emails", [])
PASSWORD = st.secrets.get("password")

if not st.session_state.authenticated:
    with st.form("login"):
        st.markdown("<h2>🔐 Secure Access</h2>", unsafe_allow_html=True)
        st.markdown("<div class='shimmer'></div>", unsafe_allow_html=True)

        email = st.text_input("Email")
        pwd = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if email in APPROVED_EMAILS and pwd == PASSWORD:
                st.session_state.authenticated = True
                st.success("Access granted")
                st.rerun()
            else:
                st.error("Invalid credentials")
    st.stop()

# ============================
# SIDEBAR NAV (with transitions)
# ============================
with st.sidebar:
    st.markdown("### Navigation")
    if st.button("🏠 Home"):
        go("Home", direction="up")
    if st.button("🧮 Cost Estimator"):
        go("Estimator", direction="left")
    if st.button("📚 Reference"):
        go("Reference", direction="left")
    if st.button("ℹ️ About"):
        go("About", direction="up")

    st.markdown("---")
    if st.button("🔓 Logout"):
        st.session_state.authenticated = False
        st.rerun()

# ============================
# PAGE WRAPPER (animation trigger)
# ============================
transition_class = "page-transition left" if st.session_state.transition_dir == "left" else "page-transition"

st.markdown(f"<div class='{transition_class}'>", unsafe_allow_html=True)

# ============================
# PAGES
# ============================
if st.session_state.page == "Home":
    st.markdown("""
    <div style="text-align:center;">
      <h1>💲 CE AI Tools</h1>
      <p>AI-powered cost estimation platform for internal engineering use</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div class='shimmer'></div>", unsafe_allow_html=True)

    logo_url = "https://raw.githubusercontent.com/apizrahman24/Cost-Predictor/main/logo.png"
    st.markdown(
        f"<div style='text-align:center'><img src='{logo_url}' width='280' style='filter: drop-shadow(0 18px 24px rgba(0,0,0,0.25)) drop-shadow(0 0 22px rgba(0,178,169,0.28));'></div>",
        unsafe_allow_html=True
    )

    st.markdown("""
    <div style="text-align:center; margin-top:1.2rem">
        <h3>Smart Cost Estimation Made Simple</h3>
        <p>Predict faster • Standardize estimates • Reduce uncertainty</p>
    </div>
    """, unsafe_allow_html=True)

elif st.session_state.page == "Estimator":
    st.markdown("## 🧮 Cost Estimator")
    st.markdown("<div class='shimmer'></div>", unsafe_allow_html=True)

    with st.form("estimator_form"):
        a = st.number_input("Input A", value=10.0)
        b = st.number_input("Input B", value=5.0)
        submitted = st.form_submit_button("Run Estimate")

    if submitted:
        st.success(f"Estimated Cost: **RM {a * b:,.2f}**")

elif st.session_state.page == "Reference":
    st.markdown("## 📚 Reference")
    st.markdown("<div class='shimmer'></div>", unsafe_allow_html=True)
    st.info("Put your reference tables, standards, and guidance notes here.")

elif st.session_state.page == "About":
    st.markdown("## ℹ️ About")
    st.markdown("<div class='shimmer'></div>", unsafe_allow_html=True)
    st.write("Developed by Cost Engineering – DFEE • RT2025")

# close wrapper
st.markdown("</div>", unsafe_allow_html=True)

# ============================
# FOOTER
# ============================
st.markdown(
    "<div class='footer' style='text-align:center; margin-top:2.2rem; font-size:0.95rem; color:rgba(0,0,0,0.55)'>"
    "Developed by <b style='color:#00B2A9'>Cost Engineering – DFEE</b> • RT2025</div>",
    unsafe_allow_html=True
)
