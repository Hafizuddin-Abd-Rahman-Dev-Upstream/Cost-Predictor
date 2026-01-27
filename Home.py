import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import csv
import glob
import time

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

/* ===== Admin Panel Styles ===== */
.admin-card {{
    background: linear-gradient(135deg, rgba(0,178,169,0.08), rgba(0,58,93,0.05)) !important;
    border: 1px solid rgba(0,178,169,0.25) !important;
    border-radius: 16px !important;
    padding: 1.5rem !important;
    margin: 1rem 0 !important;
}}
.log-table {{
    font-size: 0.9em !important;
}}
.status-success {{
    color: #10B981 !important;
    font-weight: 600 !important;
}}
.status-failed {{
    color: #EF4444 !important;
    font-weight: 600 !important;
}}
.status-logout {{
    color: #F59E0B !important;
    font-weight: 600 !important;
}}

/* ===== Debug Panel ===== */
.debug-info {{
    font-family: 'Courier New', monospace !important;
    font-size: 0.8rem !important;
    background: rgba(0,0,0,0.03) !important;
    padding: 0.5rem !important;
    border-radius: 8px !important;
    border-left: 3px solid {PETRONAS_TEAL} !important;
}}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# 📊 SIMPLE LOGGING SYSTEM THAT WORKS
# ----------------------------

# Set log directory - Use /tmp for Streamlit Cloud (always writable)
LOG_DIR = "/tmp/ceai_login_logs"  # Changed to /tmp for better compatibility

# Create directory if it doesn't exist
try:
    os.makedirs(LOG_DIR, exist_ok=True)
except:
    # Fallback to current directory
    LOG_DIR = "login_logs"
    os.makedirs(LOG_DIR, exist_ok=True)

def log_login_attempt(email, status, additional_info=""):
    """Simple logging function that always works"""
    try:
        # Create directory (double check)
        os.makedirs(LOG_DIR, exist_ok=True)
        
        # Get today's date for filename
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(LOG_DIR, f"login_log_{today}.csv")
        
        # Create log entry
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "email": str(email)[:100],  # Limit length
            "status": str(status)[:20],
            "additional_info": str(additional_info)[:200],
            "day_of_week": datetime.now().strftime("%A"),
            "hour": datetime.now().strftime("%H:00")
        }
        
        # Check if file exists
        file_exists = os.path.isfile(log_file)
        
        # Write to file
        with open(log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=log_entry.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(log_entry)
        
        return True
    except Exception as e:
        # Silent error - don't break the app
        return False

def get_today_logs():
    """Get today's logs"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(LOG_DIR, f"login_log_{today}.csv")
        
        if os.path.exists(log_file):
            return pd.read_csv(log_file)
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def get_all_log_files():
    """Get all log files"""
    try:
        files = []
        for file in os.listdir(LOG_DIR):
            if file.startswith("login_log_") and file.endswith(".csv"):
                files.append(file)
        return sorted(files, reverse=True)
    except:
        return []

def cleanup_old_logs(days=30):
    """Remove old log files"""
    try:
        cutoff = datetime.now() - timedelta(days=days)
        
        for file in get_all_log_files():
            try:
                # Extract date from filename
                date_str = file.replace("login_log_", "").replace(".csv", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                if file_date < cutoff:
                    os.remove(os.path.join(LOG_DIR, file))
            except:
                continue
    except:
        pass

# Run cleanup once
if "cleaned" not in st.session_state:
    cleanup_old_logs(30)
    st.session_state.cleaned = True

# ----------------------------
# 🔐 PASSWORD PROTECTION
# ----------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_email = ""

# Get credentials from secrets
try:
    APPROVED_EMAILS = st.secrets.get("emails", [])
    ADMIN_EMAILS = st.secrets.get("admin_emails", [])
    correct_password = st.secrets.get("password", "")
    
    # Ensure they're lists
    if isinstance(APPROVED_EMAILS, str):
        APPROVED_EMAILS = [APPROVED_EMAILS]
    if isinstance(ADMIN_EMAILS, str):
        ADMIN_EMAILS = [ADMIN_EMAILS]
        
except:
    st.error("⚠️ Error loading secrets. Please check your secrets.toml file.")
    APPROVED_EMAILS = []
    ADMIN_EMAILS = []
    correct_password = ""

# Show debug info in sidebar
with st.sidebar:
    st.markdown("### 🔧 Debug Info")
    st.write(f"📁 Log dir: `{LOG_DIR}`")
    st.write(f"✅ Dir exists: {os.path.exists(LOG_DIR)}")
    st.write(f"👤 Current user: {st.session_state.get('user_email', 'Not logged in')}")
    st.write(f"👑 Admin emails: {len(ADMIN_EMAILS)} found")
    
    if st.session_state.get('user_email'):
        is_admin = st.session_state.user_email in ADMIN_EMAILS
        st.write(f"🎯 Is admin: {is_admin}")

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
                st.session_state.user_email = email
                
                # Log successful login
                log_login_attempt(email, "SUCCESS", "Login successful")
                
                st.success("✅ Access granted.")
                time.sleep(0.5)
                st.rerun()
            else:
                # Log failed attempt
                log_login_attempt(email if email else "Unknown", "FAILED", "Invalid credentials")
                st.error("❌ Invalid email or password. Please contact Cost Engineering Focal for access")

    st.stop()

# ----------------------------
# 🔓 LOGOUT BUTTON
# ----------------------------
col1, col2, col3 = st.columns([7, 2, 2])
with col2:
    if st.button("🔓 Logout"):
        # Log logout action
        log_login_attempt(st.session_state.user_email, "LOGOUT", "User logged out")
        st.session_state.authenticated = False
        st.session_state.user_email = ""
        st.rerun()

# ----------------------------
# 📊 ADMIN PANEL (FIXED)
# ----------------------------

# Check if current user is admin
current_user = st.session_state.user_email
is_admin = current_user in ADMIN_EMAILS if ADMIN_EMAILS else False

# Show admin panel if user is admin
if is_admin:
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align:center;">
        <h2 style="color:{PETRONAS_NAVY}; margin-bottom: 0.5rem;">📊 ADMIN DASHBOARD</h2>
        <div style="color:rgba(0,0,0,0.6); font-size:0.95rem; margin-bottom: 1.5rem;">
            Login Activity Monitoring & Analytics
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Refresh button
    if st.button("🔄 Refresh Logs", key="admin_refresh"):
        st.rerun()
    
    # Today's logs
    st.subheader("📅 Today's Activity")
    
    today_logs = get_today_logs()
    
    if not today_logs.empty:
        # Show statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total = len(today_logs)
            st.metric("Total Logins", total)
        
        with col2:
            success = len(today_logs[today_logs['status'] == 'SUCCESS'])
            st.metric("Successful", success)
        
        with col3:
            failed = len(today_logs[today_logs['status'] == 'FAILED'])
            st.metric("Failed", failed)
        
        with col4:
            logout = len(today_logs[today_logs['status'] == 'LOGOUT'])
            st.metric("Logouts", logout)
        
        # Show the data
        st.dataframe(today_logs, use_container_width=True)
        
        # Download button
        csv_data = today_logs.to_csv(index=False)
        st.download_button(
            label="📥 Download Today's Logs",
            data=csv_data,
            file_name=f"login_logs_{datetime.now().strftime('%Y-%m-%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No logs recorded today yet.")
        st.write("Try logging out and back in to create the first log entry.")
    
    # Historical logs
    st.subheader("📂 Historical Logs")
    
    all_files = get_all_log_files()
    
    if all_files:
        selected_file = st.selectbox("Select a log file to view:", all_files)
        
        if selected_file:
            file_path = os.path.join(LOG_DIR, selected_file)
            try:
                df = pd.read_csv(file_path)
                
                # Show file stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Records", len(df))
                with col2:
                    success = len(df[df['status'] == 'SUCCESS'])
                    st.metric("Successful", success)
                with col3:
                    failed = len(df[df['status'] == 'FAILED'])
                    st.metric("Failed", failed)
                
                # Show data
                st.dataframe(df, use_container_width=True)
                
                # Download button
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label=f"📥 Download {selected_file}",
                    data=csv_data,
                    file_name=selected_file,
                    mime="text/csv"
                )
            except Exception as e:
                st.error(f"Error reading file: {e}")
    else:
        st.info("No historical log files found.")
    
    # Log management
    st.subheader("🛠️ Log Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clean Old Logs (30+ days)"):
            cleanup_old_logs(30)
            st.success("Old logs cleaned up successfully!")
            time.sleep(1)
            st.rerun()
    
    with col2:
        # Test logging
        if st.button("🧪 Test Logging"):
            test_result = log_login_attempt(
                current_user, 
                "TEST", 
                "Manual test from admin panel"
            )
            if test_result:
                st.success("✅ Test log created successfully!")
                st.rerun()
            else:
                st.error("❌ Test logging failed")
    
    # Log directory info
    st.info(f"📁 Logs are stored in: `{LOG_DIR}`")
    
    st.markdown("---")

# ----------------------------
# 🎯 MAIN CONTENT (For all users)
# ----------------------------

# Hero / Header
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

# Welcome message with admin badge
st.markdown(f"""
<div style="text-align:center; margin-bottom: 1.5rem;">
  <div style="
      display: inline-block;
      padding: 0.5rem 1rem;
      background: rgba(0,178,169,0.08);
      border-radius: 12px;
      border: 1px solid rgba(0,178,169,0.2);
      font-size: 0.95rem;
      color: {PETRONAS_NAVY};
  ">
    👋 Welcome, <b>{st.session_state.user_email}</b>
    {' 👑 (Admin)' if is_admin else ''}
  </div>
</div>
""", unsafe_allow_html=True)

# Catchphrase
st.markdown(f"""
<div class="hero" style="text-align:center; margin: 1.0rem 0 0.8rem 0;">
  <div style="
      font-size: 1.35rem;
      font-weight: 800;
      color: {PETRONAS_NAVY};
      margin-bottom: 0.55rem;
  ">
    "Smart Cost Estimation Made Simple"
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

# Quick tools section
st.markdown("---")
st.markdown("### 🛠️ Available Tools")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div style='padding: 1.5rem; background: rgba(0,178,169,0.08); border-radius: 12px; border: 1px solid rgba(0,178,169,0.2);'>
        <h4>📊 Cost Predictor</h4>
        <p>AI-powered cost estimation based on project parameters and historical data.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style='padding: 1.5rem; background: rgba(0,178,169,0.08); border-radius: 12px; border: 1px solid rgba(0,178,169,0.2); margin-top: 1rem;'>
        <h4>📈 Benchmark Analyzer</h4>
        <p>Compare project costs against industry benchmarks and historical data.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style='padding: 1.5rem; background: rgba(0,178,169,0.08); border-radius: 12px; border: 1px solid rgba(0,178,169,0.2);'>
        <h4>⚡ Risk Calculator</h4>
        <p>Calculate and visualize project risks with Monte Carlo simulations.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style='padding: 1.5rem; background: rgba(0,178,169,0.08); border-radius: 12px; border: 1px solid rgba(0,178,169,0.2); margin-top: 1rem;'>
        <h4>📄 Report Generator</h4>
        <p>Automatically generate professional cost estimation reports.</p>
    </div>
    """, unsafe_allow_html=True)

# Test button for non-admin users
if not is_admin:
    st.markdown("---")
    if st.button("🔍 Check My Login Activity"):
        # Show user's recent activity
        today_logs = get_today_logs()
        if not today_logs.empty:
            user_logs = today_logs[today_logs['email'] == current_user]
            if not user_logs.empty:
                st.info(f"📊 Your activity today: {len(user_logs)} login(s)")
                st.dataframe(user_logs[['timestamp', 'status']])
            else:
                st.info("No activity recorded for you today.")
        else:
            st.info("No logs available yet.")

# Footer
st.markdown("---")
st.markdown(
    "<div class='footer-div'>"
    f"💲 <b>CE AI Tools</b> • Logged in as: {current_user}<br>"
    f"Admin access: {'✅ Enabled' if is_admin else '❌ Not enabled'}<br>"
    "Developed by <b>Cost Engineering - DFEE</b> — <b>RT2025</b>"
    "</div>",
    unsafe_allow_html=True
)

# ----------------------------
# 🚨 TROUBLESHOOTING HELP
# ----------------------------
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🚨 Troubleshooting")
    
    with st.expander("Logs not showing?"):
        st.markdown("""
        **Common fixes:**
        
        1. **Check secrets.toml:**
        ```toml
        admin_emails = ["your.email@petronas.com"]  # Your exact email
        ```
        
        2. **Try logging out and back in**
        
        3. **Check directory permissions:**
           - The app uses `/tmp/ceai_login_logs/`
           - This always works on Streamlit Cloud
        
        4. **Force create a test log:**
        ```python
        # In your app, add this test button
        if st.button("Test Logging"):
            log_login_attempt("test@email.com", "TEST", "Test entry")
        ```
        """)
    
    if st.button("🧪 Create Test Log Entry"):
        test_result = log_login_attempt(
            "test@system.com", 
            "TEST", 
            "Manual test from sidebar"
        )
        if test_result:
            st.success("✅ Test log created!")
        else:
            st.error("❌ Test failed")
        st.rerun()
