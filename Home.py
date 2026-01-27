import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import csv
import glob
import time
from pathlib import Path

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
</style>
""", unsafe_allow_html=True)

# ----------------------------
# 📊 LOGGING SYSTEM FOR STREAMLIT CLOUD
# ----------------------------

def setup_logging():
    """Setup logging directory for Streamlit Cloud"""
    # For Streamlit Cloud, use /tmp directory which is writable
    # and persists across app restarts
    log_dir = "/tmp/login_logs"  # Changed to /tmp for Streamlit Cloud
    
    try:
        # Create directory if it doesn't exist
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        return log_dir
    except Exception as e:
        # Fallback to current directory if /tmp fails
        fallback_dir = "login_logs"
        Path(fallback_dir).mkdir(parents=True, exist_ok=True)
        return fallback_dir

def log_login_attempt(email, status, log_dir, additional_info=""):
    """Log login attempts to daily CSV files"""
    try:
        # Get current date for filename
        current_date = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(log_dir, f"login_log_{current_date}.csv")
        
        # Create log entry
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "email": email,
            "status": status,
            "additional_info": additional_info,
            "day_of_week": datetime.now().strftime("%A"),
            "hour": datetime.now().strftime("%H:00")
        }
        
        # Write to CSV
        file_exists = os.path.isfile(log_file)
        
        with open(log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["timestamp", "email", "status", "additional_info", "day_of_week", "hour"])
            if not file_exists:
                writer.writeheader()
            writer.writerow(log_entry)
        
        return True
    except Exception as e:
        # Silent fail - don't break the app if logging fails
        return False

def cleanup_old_logs(log_dir, days_to_keep=30):
    """Remove log files older than specified days"""
    try:
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for log_file in glob.glob(os.path.join(log_dir, "login_log_*.csv")):
            try:
                filename = os.path.basename(log_file)
                date_str = filename.replace("login_log_", "").replace(".csv", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                if file_date < cutoff_date:
                    os.remove(log_file)
            except:
                continue
    except:
        pass

def get_all_logs(log_dir):
    """Get all logs combined into a single DataFrame"""
    all_logs = []
    try:
        # Check if directory exists
        if not os.path.exists(log_dir):
            return pd.DataFrame()
            
        log_files = sorted([f for f in os.listdir(log_dir) if f.endswith('.csv')], reverse=True)
        
        for file in log_files:
            try:
                file_path = os.path.join(log_dir, file)
                df = pd.read_csv(file_path)
                df['log_date'] = file.replace('login_log_', '').replace('.csv', '')
                all_logs.append(df)
            except:
                continue
        
        if all_logs:
            return pd.concat(all_logs, ignore_index=True)
    except:
        pass
    return pd.DataFrame()

def get_log_statistics(log_dir):
    """Get statistics from logs"""
    try:
        df = get_all_logs(log_dir)
        if df.empty:
            return {
                "total_logins": 0,
                "successful": 0,
                "failed": 0,
                "unique_users": 0,
                "today_logins": 0
            }
        
        today = datetime.now().strftime("%Y-%m-%d")
        today_logs = df[df['log_date'] == today] if 'log_date' in df.columns else pd.DataFrame()
        
        return {
            "total_logins": len(df),
            "successful": len(df[df['status'] == 'SUCCESS']),
            "failed": len(df[df['status'] == 'FAILED']),
            "unique_users": df['email'].nunique(),
            "today_logins": len(today_logs),
            "today_success": len(today_logs[today_logs['status'] == 'SUCCESS']) if not today_logs.empty else 0,
            "today_failed": len(today_logs[today_logs['status'] == 'FAILED']) if not today_logs.empty else 0
        }
    except:
        return {
            "total_logins": 0,
            "successful": 0,
            "failed": 0,
            "unique_users": 0,
            "today_logins": 0,
            "today_success": 0,
            "today_failed": 0
        }

# Initialize logging - THIS WILL CREATE THE DIRECTORY
LOG_DIR = setup_logging()

# Debug info for Streamlit Cloud (remove in production)
st.sidebar.info(f"Log dir: {LOG_DIR}")
st.sidebar.info(f"Log dir exists: {os.path.exists(LOG_DIR)}")

# Cleanup old logs (run once per session)
if "cleanup_done" not in st.session_state:
    cleanup_old_logs(LOG_DIR, days_to_keep=30)
    st.session_state.cleanup_done = True

# ----------------------------
# 🔐 Password protection with LOGGING
# ----------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_email = ""

# Get credentials from secrets
APPROVED_EMAILS = st.secrets.get("emails", [])
ADMIN_EMAILS = st.secrets.get("admin_emails", ["admin@petronas.com"])
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
                st.session_state.user_email = email
                
                # Log successful login
                log_login_attempt(email, "SUCCESS", LOG_DIR, "User logged in successfully")
                
                st.success("✅ Access granted.")
                time.sleep(0.5)
                st.rerun()
            else:
                # Log failed attempt
                log_login_attempt(email if email else "Unknown", "FAILED", LOG_DIR, "Invalid credentials")
                st.error("❌ Invalid email or password. Please contact Cost Engineering Focal for access")

    st.stop()

# ----------------------------
# Top controls
# ----------------------------
col1, col2, col3 = st.columns([7, 2, 2])
with col2:
    if st.button("🔓 Logout"):
        # Log logout action
        log_login_attempt(st.session_state.user_email, "LOGOUT", LOG_DIR, "User logged out")
        st.session_state.authenticated = False
        st.session_state.user_email = ""
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

# Welcome message with user email
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
  </div>
</div>
""", unsafe_allow_html=True)

# Catchphrase (modern)
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

# Divider
st.markdown("---")

# ----------------------------
# 📊 ADMIN PANEL SECTION (Only for admin users)
# ----------------------------
if st.session_state.user_email in ADMIN_EMAILS:
    st.markdown(f"""
    <div style="text-align:center;">
        <h2 style="color:{PETRONAS_NAVY}; margin-bottom: 0.5rem;">📊 Admin Dashboard</h2>
        <div style="color:rgba(0,0,0,0.6); font-size:0.95rem; margin-bottom: 1.5rem;">
            Login Activity Monitoring & Analytics
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Get statistics
    stats = get_log_statistics(LOG_DIR)
    
    # Display statistics in columns
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Logins", stats["total_logins"])
    with col2:
        st.metric("Successful", stats["successful"], 
                 f"Today: {stats['today_success']}")
    with col3:
        st.metric("Failed", stats["failed"],
                 f"Today: {stats['today_failed']}")
    with col4:
        st.metric("Unique Users", stats["unique_users"])
    
    # Show current log directory info
    st.info(f"📁 Logs stored in: `{LOG_DIR}`")
    
    # Today's activity
    st.subheader("📅 Today's Activity")
    today_file = os.path.join(LOG_DIR, f"login_log_{datetime.now().strftime('%Y-%m-%d')}.csv")
    
    if os.path.exists(today_file):
        today_df = pd.read_csv(today_file)
        
        # Format status with colors
        def format_status(status):
            if status == "SUCCESS":
                return f'<span class="status-success">✅ {status}</span>'
            elif status == "FAILED":
                return f'<span class="status-failed">❌ {status}</span>'
            elif status == "LOGOUT":
                return f'<span class="status-logout">🔓 {status}</span>'
            return status
        
        # Create formatted dataframe for display
        display_df = today_df.copy()
        display_df['status'] = display_df['status'].apply(format_status)
        
        # Show table
        st.markdown('<div class="admin-card">', unsafe_allow_html=True)
        st.markdown(f"**Today's Logins:** {len(today_df)} records")
        st.write(display_df[['timestamp', 'email', 'status', 'additional_info']].to_html(escape=False, index=False), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Download button for today's logs
        csv_data = today_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Today's Logs",
            data=csv_data,
            file_name=f"login_logs_{datetime.now().strftime('%Y-%m-%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No login activity recorded today.")
    
    # Historical Logs Section
    st.subheader("📂 Historical Logs")
    
    # List all log files
    try:
        log_files = sorted([f for f in os.listdir(LOG_DIR) if f.endswith('.csv')], reverse=True)
    except:
        log_files = []
    
    if log_files:
        selected_file = st.selectbox("Select log file to view:", log_files)
        
        if selected_file:
            file_path = os.path.join(LOG_DIR, selected_file)
            df = pd.read_csv(file_path)
            
            # Show file statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Records", len(df))
            with col2:
                success_count = len(df[df['status'] == 'SUCCESS'])
                st.metric("Successful", success_count)
            with col3:
                failed_count = len(df[df['status'] == 'FAILED'])
                st.metric("Failed", failed_count)
            
            # Show data
            st.markdown('<div class="admin-card">', unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Download button for selected file
            csv_data = df.to_csv(index=False)
            st.download_button(
                label=f"📥 Download {selected_file}",
                data=csv_data,
                file_name=selected_file,
                mime="text/csv"
            )
            
        # Combined Analysis
        st.subheader("📈 Combined Analysis")
        
        if st.button("Generate Monthly Report"):
            all_logs_df = get_all_logs(LOG_DIR)
            
            if not all_logs_df.empty:
                # Create monthly summary
                all_logs_df['timestamp'] = pd.to_datetime(all_logs_df['timestamp'])
                all_logs_df['month'] = all_logs_df['timestamp'].dt.strftime('%Y-%m')
                
                monthly_summary = all_logs_df.groupby(['month', 'status']).size().unstack(fill_value=0)
                
                # Display chart
                st.bar_chart(monthly_summary)
                
                # Show top users
                st.markdown("**Top 10 Users by Login Activity:**")
                top_users = all_logs_df['email'].value_counts().head(10)
                st.dataframe(top_users.reset_index().rename(columns={'index': 'Email', 'email': 'Login Count'}))
            else:
                st.warning("No data available for analysis.")
    else:
        st.info("No log files found.")
    
    # Log cleanup section (for admins only)
    st.subheader("🛠️ Log Management")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Run Log Cleanup Now"):
            cleanup_old_logs(LOG_DIR, days_to_keep=30)
            st.success("Log cleanup completed! Files older than 30 days have been removed.")
            st.rerun()
    
    with col2:
        # Count log files
        log_count = len(log_files) if 'log_files' in locals() else 0
        st.metric("Total Log Files", log_count)
    
    st.markdown("---")

# Main content divider
st.markdown("### 🛠️ Available Tools")
st.markdown("Select from the following cost engineering tools:")

# Tool cards (you can expand this section)
col1, col2 = st.columns(2)

with col1:
    with st.container():
        st.markdown("""
        <div style='padding: 1.5rem; background: rgba(0,178,169,0.08); border-radius: 12px; border: 1px solid rgba(0,178,169,0.2);'>
            <h4>📊 Cost Predictor</h4>
            <p>AI-powered cost estimation based on project parameters and historical data.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with st.container():
        st.markdown("""
        <div style='padding: 1.5rem; background: rgba(0,178,169,0.08); border-radius: 12px; border: 1px solid rgba(0,178,169,0.2); margin-top: 1rem;'>
            <h4>📈 Benchmark Analyzer</h4>
            <p>Compare project costs against industry benchmarks and historical data.</p>
        </div>
        """, unsafe_allow_html=True)

with col2:
    with st.container():
        st.markdown("""
        <div style='padding: 1.5rem; background: rgba(0,178,169,0.08); border-radius: 12px; border: 1px solid rgba(0,178,169,0.2);'>
            <h4>⚡ Risk Calculator</h4>
            <p>Calculate and visualize project risks with Monte Carlo simulations.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with st.container():
        st.markdown("""
        <div style='padding: 1.5rem; background: rgba(0,178,169,0.08); border-radius: 12px; border: 1px solid rgba(0,178,169,0.2); margin-top: 1rem;'>
            <h4>📄 Report Generator</h4>
            <p>Automatically generate professional cost estimation reports.</p>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(
    "<div class='footer-div'>"
    "Developed by <b>Cost Engineering - DFEE</b> for internal project cost estimation uses — <b>RT2025</b><br>"
    f"Login tracking active • Last cleanup: {datetime.now().strftime('%Y-%m-%d')}"
    "</div>",
    unsafe_allow_html=True
)
