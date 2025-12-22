import streamlit as st

# ✅ Set page config FIRST (must be before other st.* calls)
st.set_page_config(
    page_title="CE AI Tools",
    page_icon="💲",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ----------------------------
# 🎨 PETRONAS-ish Modern Theme
# ----------------------------
PETRONAS_TEAL = "#00B2A9"
PETRONAS_NAVY = "#003A5D"
BG = "#F6FBFB"
CARD = "rgba(255,255,255,0.72)"
BORDER = "rgba(0,178,169,0.18)"

st.markdown(f"""
<style>
/* ===== Base ===== */
html, body, [class*="css"] {{
    font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Arial !important;
}}
.stApp {{
    background: radial-gradient(1200px 600px at 10% 0%, rgba(0,178,169,0.12), transparent 55%),
                radial-gradient(1000px 600px at 90% 10%, rgba(0,58,93,0.10), transparent 55%),
                {BG};
}}

/* ===== Main container as glass card ===== */
section.main > div {{
    background: {CARD};
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid {BORDER};
    border-radius: 18px;
    padding: 2.2rem 2.2rem 1.8rem 2.2rem;
    box-shadow: 0 18px 40px rgba(0,0,0,0.06);
}}

/* ===== Titles ===== */
h1, h2, h3 {{
    color: {PETRONAS_NAVY};
    letter-spacing: -0.5px;
}}

/* ===== Sidebar cleanup + subtle header ===== */
section[data-testid="stSidebar"] > div {{
    background: linear-gradient(180deg, rgba(0,178,169,0.08), transparent 40%);
}}
section[data-testid="stSidebar"] button[aria-label="Collapse sidebar"] {{
    display: none !important;
}}

/* ===== Animated header reveal ===== */
@keyframes heroIn {{
  0% {{ opacity: 0; transform: translateY(-18px); filter: blur(4px); }}
  100% {{ opacity: 1; transform: translateY(0); filter: blur(0); }}
}}
.hero {{
  animation: heroIn 900ms cubic-bezier(.2,.8,.2,1) 1;
}}

/* ===== Logo float ===== */
@keyframes floaty {{
  0%, 100% {{ transform: translateY(0); }}
  50% {{ transform: translateY(-6px); }}
}}
.logo-float {{
  animation: floaty 3.2s ease-in-out infinite;
}}

/* ===== Shimmer divider ===== */
@keyframes shimmer {{
  0% {{ background-position: -200% 0; }}
  100% {{ background-position: 200% 0; }}
}}
.shimmer-line {{
  height: 3px;
  border-radius: 999px;
  margin: 1.2rem 0 1.6rem 0;
  background: linear-gradient(90deg,
      rgba(0,178,169,0.0),
      rgba(0,178,169,0.9),
      rgba(0,58,93,0.9),
      rgba(0,178,169,0.0)
  );
  background-size: 200% 100%;
  animation: shimmer 2.4s linear infinite;
  opacity: 0.85;
}}

/* ===== Buttons ===== */
.stButton>button {{
    background: linear-gradient(135deg, {PETRONAS_TEAL}, {PETRONAS_NAVY}) !important;
    color: white !important;
    border-radius: 12px !important;
    border: 0 !important;
    font-weight: 700;
    padding: 0.7em 1.4em;
    box-shadow: 0 10px 20px rgba(0,58,93,0.12);
    transform: translateY(0);
    transition: transform .15s ease, filter .15s ease, box-shadow .15s ease;
    position: relative;
    overflow: hidden;
}}
.stButton>button:hover {{
    transform: translateY(-2px);
    filter: brightness(1.02);
    box-shadow: 0 14px 24px rgba(0,58,93,0.18);
}}
/* Ripple effect */
.stButton>button:active::after {{
    content: "";
    position: absolute;
    inset: 0;
    background: radial-gradient(circle, rgba(255,255,255,.45) 10%, transparent 12%);
    transform: scale(10);
    opacity: 0;
    animation: ripple 550ms ease-out;
}}
@keyframes ripple {{
  0% {{ transform: scale(0); opacity: .55; }}
  100% {{ transform: scale(8); opacity: 0; }}
}}

/* ===== Inputs ===== */
.stTextInput>div>div>input {{
    border: 1.6px solid rgba(0,178,169,0.45) !important;
    border-radius: 12px !important;
    padding: 0.65em 0.85em !important;
    background: rgba(255,255,255,0.75) !important;
}}
.stTextInput>div>div>input:focus {{
    outline: none !important;
    border: 1.8px solid {PETRONAS_TEAL} !important;
    box-shadow: 0 0 0 4px rgba(0,178,169,0.16);
}}

/* ===== Forms ===== */
.stForm {{
    background: rgba(255,255,255,0.55) !important;
    border: 1px solid rgba(0,178,169,0.16) !important;
    padding: 1.6rem !important;
    border-radius: 16px !important;
    box-shadow: 0 10px 26px rgba(0,0,0,0.05);
}}

/* ===== Alerts ===== */
.stAlert {{
    border-radius: 12px !important;
}}

/* ===== Footer ===== */
.footer-div {{
    text-align: center;
    color: rgba(0,0,0,0.55);
    font-size: 0.95em;
    margin-top: 2.2em;
}}
.footer-div b {{
    color: {PETRONAS_TEAL};
}}

/* ===== Optional: hide Streamlit share/star ===== */
[data-testid="stShareButton"],
[data-testid="stFavoriteButton"] {{
    display: none !important;
}}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# 🔐 Password protection
# ----------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

APPROVED_EMAILS = st.secrets.get("emails", [])
correct_password = st.secrets.get("password", None)

if not st.session_state.authenticated:
    with st.form("login_form"):
        st.markdown("### 🔐 Access Required")
        st.markdown("<div class='shimmer-line'></div>", unsafe_allow_html=True)

        email = st.text_input("Email Address")
        password = st.text_input("Enter Access Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if email in APPROVED_EMAILS and password == correct_password:
                st.session_state.authenticated = True
                st.success("✅ Access granted.")
                st.rerun()
            else:
                st.error("❌ Invalid email or password. Please contact Cost Engineering Focal for access")

    st.stop()

# ----------------------------
# Top controls
# ----------------------------
col1, col2, col3 = st.columns([7, 2, 2])
with col2:
    if st.button("🔓 Logout"):
        st.session_state.authenticated = False
        st.rerun()

# ----------------------------
# Hero / Header (modern + animated)
# ----------------------------
st.markdown(f"""
<div class="hero" style="text-align:center; margin: 1.6rem 0 0.6rem 0;">
  <div style="
      display:inline-block;
      padding: 0.35rem 0.9rem;
      border-radius: 999px;
      background: rgba(0,178,169,0.10);
      border: 1px solid rgba(0,178,169,0.18);
      color: {PETRONAS_NAVY};
      font-weight: 700;
      font-size: 0.95rem;
  ">Internal Tools • Cost Engineering</div>

  <h1 style="
      margin: 0.85rem 0 0.4rem 0;
      font-size: 3.1rem;
      font-weight: 800;
      line-height: 1.05;
      color: {PETRONAS_NAVY};
  ">
    💲 CE AI Tools
  </h1>

  <div style="max-width: 720px; margin: 0.2rem auto 0 auto; color: rgba(0,0,0,0.58); font-size: 1.1rem; line-height: 1.6;">
    AI-powered estimation tools to streamline cost engineering workflows with consistent, data-driven outputs.
  </div>
</div>

<div class="shimmer-line"></div>
""", unsafe_allow_html=True)

# ----------------------------
# Logo (float animation)
# ----------------------------
logo_url = "https://raw.githubusercontent.com/apizrahman24/Cost-Predictor/main/logo.png"
st.markdown(
    f"""
    <div style="display:flex; justify-content:center; align-items:center; margin: 0.6rem 0 0.4rem 0;">
        <img class="logo-float" src="{logo_url}" width="290" style="filter: drop-shadow(0 10px 18px rgba(0,58,93,0.18));">
    </div>
    """,
    unsafe_allow_html=True
)

# Catchphrase (modern)
st.markdown(f"""
<div class="hero" style="text-align:center; margin: 1.0rem 0 0.8rem 0;">
  <div style="
      font-size: 1.35rem;
      font-weight: 800;
      color: {PETRONAS_NAVY};
      margin-bottom: 0.55rem;
  ">
    “Smart Cost Estimation Made Simple”
  </div>

  <div style="
      font-size: 1.05rem;
      color: rgba(0,0,0,0.58);
      line-height: 1.7;
      max-width: 720px;
      margin: 0 auto;
  ">
    Predict faster, document cleaner, and standardize estimation assumptions — built for internal project use.
  </div>
</div>
""", unsafe_allow_html=True)

# Divider
st.markdown("---")

# Footer
st.markdown(
    "<div class='footer-div'>"
    "Developed by <b>Cost Engineering - DFEE</b> for internal project cost estimation uses — <b>RT2025</b>"
    "</div>",
    unsafe_allow_html=True
)
