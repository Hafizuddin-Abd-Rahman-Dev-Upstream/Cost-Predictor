import streamlit as st

# Set page config
st.set_page_config(
    page_title="Welcome | Cost Prediction RT2025",
    page_icon="💲",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Password protection
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    password = st.text_input("🔐 Enter Access Password", type="password")
    if password == st.secrets["password"]:  # You will define 'password' in .streamlit/secrets.toml
        st.session_state.authenticated = True
        st.success("✅ Access granted")
    elif password:
        st.error("❌ Incorrect password")
    st.stop()

# Welcome Page Content
st.title("💲 Welcome to Cost Prediction RT2025")
st.markdown("""
---

### 👋 Hello and Welcome!

This application helps you perform intelligent **project cost estimations** and breakdowns based on historical and real-time input data.

Please navigate to the desired module using the sidebar (top left corner) to begin.

---

### 🔍 What You Can Do:
- 📂 Upload or load datasets
- 📈 Predict project costs using machine learning
- ⚙️ Apply EPCIC and PRR cost breakdowns
- 📊 Visualize cost curves
- 📤 Download prediction results in Excel

---

### 🔐 Access Control
Some pages may require a password. Please contact your administrator if you do not have one.

---
""")

# Footer
st.markdown(
    "<div style='text-align: center; color: grey;'>"
    "Developed for internal project cost analysis – RT2025"
    "</div>",
    unsafe_allow_html=True
)
