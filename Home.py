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

# Graceful handling if password is not set
correct_password = st.secrets.get("password", None)

if not st.session_state.authenticated:
    with st.form("login_form"):
        password = st.text_input("🔐 Enter Access Password", type="password")
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
