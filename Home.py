import streamlit as st

# Set page config
st.set_page_config(
    page_title="CE AI Tools",
    page_icon="💲",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional styling with #00B1A9 theme
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Main app styling */
    .stApp {
        background: linear-gradient(135deg, #00B1A9 0%, #008B85 25%, #006B66 50%, #004D47 75%, #003332 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Main container styling */
    .main .block-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 20px 40px rgba(0, 177, 169, 0.3);
        margin-top: 2rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(0, 177, 169, 0.2);
    }
    
    /* Title styling */
    h1 {
        color: #00B1A9 !important;
        font-weight: 700 !important;
        text-align: center;
        font-size: 2.5rem !important;
        margin-bottom: 1rem !important;
        text-shadow: 2px 2px 4px rgba(0, 177, 169, 0.1);
    }
    
    /* Header styling */
    h3 {
        color: #006B66 !important;
        font-weight: 600 !important;
        margin-top: 1.5rem !important;
    }
    
    /* Welcome section styling */
    .welcome-header {
        background: linear-gradient(90deg, #00B1A9, #008B85);
        color: white;
        padding: 1rem 2rem;
        border-radius: 15px;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 8px 16px rgba(0, 177, 169, 0.2);
    }
    
    /* Feature cards */
    .feature-card {
        background: linear-gradient(135deg, rgba(0, 177, 169, 0.1), rgba(0, 139, 133, 0.05));
        border-left: 4px solid #00B1A9;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 177, 169, 0.1);
        transition: transform 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 177, 169, 0.2);
    }
    
    /* Login form styling */
    .stForm {
        background: rgba(0, 177, 169, 0.05);
        padding: 2rem;
        border-radius: 15px;
        border: 2px solid rgba(0, 177, 169, 0.2);
        margin: 1rem 0;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #00B1A9, #008B85);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 8px rgba(0, 177, 169, 0.2);
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #008B85, #006B66);
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 177, 169, 0.3);
    }
    
    /* Input field styling */
    .stTextInput > div > div > input {
        border: 2px solid rgba(0, 177, 169, 0.3);
        border-radius: 10px;
        padding: 0.75rem;
        transition: border-color 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #00B1A9;
        box-shadow: 0 0 0 2px rgba(0, 177, 169, 0.2);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #00B1A9, #008B85);
    }
    
    /* Success/Error message styling */
    .stSuccess {
        background: rgba(0, 177, 169, 0.1);
        border: 1px solid #00B1A9;
        border-radius: 10px;
    }
    
    .stError {
        border-radius: 10px;
    }
    
    /* Footer styling */
    .footer {
        background: linear-gradient(90deg, rgba(0, 177, 169, 0.1), rgba(0, 139, 133, 0.05));
        padding: 1rem;
        border-radius: 10px;
        margin-top: 2rem;
        text-align: center;
        color: #006B66;
        font-weight: 500;
        border: 1px solid rgba(0, 177, 169, 0.2);
    }
    
    /* Animated background elements */
    .stApp::before {
        content: '';
        position: fixed;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(0, 177, 169, 0.1) 0%, transparent 70%);
        animation: float 20s ease-in-out infinite;
        z-index: -1;
    }
    
    @keyframes float {
        0%, 100% { transform: translate(0, 0) rotate(0deg); }
        33% { transform: translate(30px, -30px) rotate(120deg); }
        66% { transform: translate(-20px, 20px) rotate(240deg); }
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Sidebar toggle button styling - make it white and always visible */
    button[kind="header"] {
        color: white !important;
        background-color: rgba(255, 255, 255, 0.2) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 8px !important;
        padding: 0.5rem !important;
        margin: 0.5rem !important;
        transition: all 0.3s ease !important;
        opacity: 1 !important;
        visibility: visible !important;
    }
    
    button[kind="header"]:hover {
        background-color: rgba(255, 255, 255, 0.3) !important;
        border-color: rgba(255, 255, 255, 0.5) !important;
        transform: scale(1.05) !important;
    }
    
    /* Sidebar toggle icon styling */
    button[kind="header"] svg {
        color: white !important;
        fill: white !important;
    }
    
    /* Header toolbar styling */
    .stApp > header[data-testid="stHeader"] {
        background: transparent !important;
        height: auto !important;
    }
    
    /* Alternative selector for sidebar button */
    [data-testid="collapsedControl"] {
        color: white !important;
        background-color: rgba(255, 255, 255, 0.2) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 8px !important;
        padding: 0.5rem !important;
        margin: 0.5rem !important;
        opacity: 1 !important;
        visibility: visible !important;
    }
    
    [data-testid="collapsedControl"]:hover {
        background-color: rgba(255, 255, 255, 0.3) !important;
        border-color: rgba(255, 255, 255, 0.5) !important;
        transform: scale(1.05) !important;
    }
    
    [data-testid="collapsedControl"] svg {
        color: white !important;
        fill: white !important;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(0, 177, 169, 0.1);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #00B1A9;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #008B85;
    }
</style>
""", unsafe_allow_html=True)

# Password protection
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Graceful handling if password is not set
correct_password = st.secrets.get("password", None)

if not st.session_state.authenticated:
    # Login header
    st.markdown("""
    <div class="welcome-header">
        <h2 style="margin: 0; color: white;">🔐 Secure Access Portal</h2>
        <p style="margin: 0.5rem 0 0 0; color: rgba(255,255,255,0.9);">Enter your credentials to access CE AI Tools</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        password = st.text_input("🔐 Enter Access Password", type="password", placeholder="Enter your password...")
        submitted = st.form_submit_button("🚀 Login", use_container_width=True)
        
        if submitted:
            if correct_password is None:
                st.error("🚫 Password not configured. Please contact admin.")
            elif password == correct_password:
                st.session_state.authenticated = True
                st.success("✅ Access granted! Redirecting...")
                st.rerun()
            else:
                st.error("❌ Incorrect password. Please try again.")
    st.stop()

# Welcome Page Content
st.title("🚀 CE AI Tools")

# Welcome section
st.markdown("""
<div class="welcome-header">
    <h2 style="margin: 0; color: white;">👋 Welcome to the Future of Cost Estimation</h2>
    <p style="margin: 0.5rem 0 0 0; color: rgba(255,255,255,0.9);">Intelligent project cost analysis powered by advanced AI</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Introduction
st.markdown("""
### 🎯 **Transform Your Project Planning**
This cutting-edge application revolutionizes **project cost estimations** using machine learning algorithms trained on historical data. Navigate through our intuitive interface to unlock powerful analytical capabilities.
""")

# Feature cards
st.markdown("""
<div class="feature-card">
    <h4 style="color: #00B1A9; margin-bottom: 0.5rem;">📂 Smart Data Management</h4>
    <p style="margin: 0;">Upload, process, and manage your datasets with intelligent validation and preprocessing capabilities.</p>
</div>

<div class="feature-card">
    <h4 style="color: #00B1A9; margin-bottom: 0.5rem;">🤖 AI-Powered Predictions</h4>
    <p style="margin: 0;">Leverage advanced machine learning models to generate accurate project cost predictions with confidence intervals.</p>
</div>

<div class="feature-card">
    <h4 style="color: #00B1A9; margin-bottom: 0.5rem;">⚙️ Professional Cost Breakdowns</h4>
    <p style="margin: 0;">Apply industry-standard EPCIC and PRR methodologies for comprehensive cost analysis and reporting.</p>
</div>

<div class="feature-card">
    <h4 style="color: #00B1A9; margin-bottom: 0.5rem;">📊 Dynamic Visualizations</h4>
    <p style="margin: 0;">Create interactive cost curves, trend analysis, and professional charts for stakeholder presentations.</p>
</div>

<div class="feature-card">
    <h4 style="color: #00B1A9; margin-bottom: 0.5rem;">📤 Seamless Export</h4>
    <p style="margin: 0;">Download comprehensive reports and predictions in Excel format with customizable templates.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Getting started section
st.markdown("""
### 🚀 **Getting Started**
1. **Navigate** using the sidebar menu (☰ top left corner)
2. **Upload** your project data or use sample datasets
3. **Configure** your analysis parameters
4. **Generate** intelligent cost predictions
5. **Export** results for team collaboration
""")

st.markdown("---")

# Security notice
st.markdown("""
<div style="background: linear-gradient(90deg, rgba(0, 177, 169, 0.1), rgba(0, 139, 133, 0.05)); 
           padding: 1rem; border-radius: 10px; border-left: 4px solid #00B1A9; margin: 1rem 0;">
    <h4 style="color: #00B1A9; margin-bottom: 0.5rem;">🔐 Security & Access</h4>
    <p style="margin: 0;">This application implements enterprise-grade security measures. Contact your administrator for access credentials or technical support.</p>
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="footer">
    <p style="margin: 0; font-size: 0.9rem;">
        <strong>CE AI Tools Platform</strong> | Developed for Advanced Project Cost Analysis | RT2025<br>
        <span style="color: #00B1A9;">🔬 Powered by Machine Learning & Data Science</span>
    </p>
</div>
""", unsafe_allow_html=True)
