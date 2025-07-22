import streamlit as st

# Set page config
st.set_page_config(
    page_title="Welcome | Cost Prediction RT2025",
    page_icon="💲",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Optional: Hide the sidebar completely on this page
hide_sidebar = """
    <style>
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
    </style>
"""
st.markdown(hide_sidebar, unsafe_allow_html=True)

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
