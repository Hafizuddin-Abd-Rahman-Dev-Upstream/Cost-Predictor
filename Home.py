import streamlit as st

st.set_page_config(page_title="CE AI Tools", page_icon="💲", layout="centered")

PETRONAS_TEAL = "#00B2A9"
PETRONAS_NAVY = "#003A5D"
PETRONAS_DARK = "#002B36"

# ---- CSS: glow is on BODY, forced behind via z-index and pointer-events ----
st.markdown(f"""
<style>
/* Put glow behind EVERYTHING and never capture clicks */
html, body {{
  height: 100%;
}}

body {{
  background: linear-gradient(135deg, {PETRONAS_DARK}, {PETRONAS_NAVY}) !important;
}}

body::before, body::after {{
  content: "";
  position: fixed;
  inset: -25%;
  z-index: -9999;              /* critical: always behind */
  pointer-events: none;        /* critical: never block clicks */
  filter: blur(45px);
  opacity: 0.78;
}}

body::before {{
  background:
    radial-gradient(circle at 25% 25%, rgba(0,178,169,0.55), transparent 55%),
    radial-gradient(circle at 75% 35%, rgba(0,58,93,0.45), transparent 60%),
    radial-gradient(circle at 55% 80%, rgba(0,178,169,0.30), transparent 55%);
  animation: glowA 14s ease-in-out infinite;
}}

body::after {{
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

/* Glass main container */
section.main > div {{
  background: rgba(255,255,255,0.74);
  border-radius: 22px;
  padding: 2.2rem;
  border: 1px solid rgba(255,255,255,0.24);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  box-shadow: 0 30px 70px rgba(0,0,0,0.28);
}}

/* Page transitions */
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

/* Buttons */
.stButton > button {{
  background: linear-gradient(135deg, {PETRONAS_TEAL}, {PETRONAS_NAVY});
  color: white !important;
  font-weight: 750;
  border-radius: 14px;
  padding: 0.78em 1.55em;
  border: 1px solid rgba(255,255,255,0.18);
  box-shadow: 0 16px 34px rgba(0,0,0,0.30), 0 0 28px rgba(0,178,169,0.22);
  transition: all 0.18s ease;
}}
.stButton > button:hover {{
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 22px 46px rgba(0,0,0,0.35), 0 0 34px rgba(0,178,169,0.30);
}}
</style>
""", unsafe_allow_html=True)

# ---- Router ----
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "dir" not in st.session_state:
    st.session_state.dir = "up"

def go(p, d="up"):
    st.session_state.page = p
    st.session_state.dir = d
    st.rerun()

with st.sidebar:
    st.header("Navigation")
    if st.button("🏠 Home"): go("Home", "up")
    if st.button("🧮 Estimator"): go("Estimator", "left")
    if st.button("ℹ️ About"): go("About", "up")

transition_class = "page-transition left" if st.session_state.dir == "left" else "page-transition"
st.markdown(f"<div class='{transition_class}'>", unsafe_allow_html=True)

if st.session_state.page == "Home":
    st.title("💲 CE AI Tools")
    st.write("If you can click the sidebar and switch pages, transitions are working ✅")

elif st.session_state.page == "Estimator":
    st.title("🧮 Estimator")
    a = st.number_input("A", value=10.0)
    b = st.number_input("B", value=5.0)
    st.success(f"RM {a*b:,.2f}")

else:
    st.title("ℹ️ About")
    st.write("Developed by Cost Engineering – DFEE • RT2025")

st.markdown("</div>", unsafe_allow_html=True)
