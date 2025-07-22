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

# Graceful handling if password is not defined in secrets
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
                st.experimental_rerun()
            else:
                st.error("❌ Incorrect password")
    st.stop()
