# ======================================================================================
# CAPEX AI RT2026 - IMPROVED VERSION
# 
# Enhanced with:
# - Modern UI/UX with PETRONAS branding
# - Better error handling and validation
# - Fixed training pipeline issues
# - Added MAE metric
# - Session state management
# - Performance optimizations
# - Professional exports
#
# requirements.txt:
# streamlit>=1.28.0
# pandas>=2.0.0
# numpy>=1.24.0
# scipy>=1.10.0
# scikit-learn>=1.3.0
# plotly>=5.14.0
# matplotlib>=3.7.0
# python-pptx>=0.6.21
# openpyxl>=3.1.0
# requests>=2.31.0
# ======================================================================================

import io
import json
import zipfile
import re
import requests
import hashlib
import numpy as np
import pandas as pd
import streamlit as st
from typing import Tuple, Dict, List, Optional, Any

# --- Guard: scikit-learn missing (prevents hard crash on Streamlit Cloud) ---
try:
    from sklearn.impute import KNNImputer, SimpleImputer
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import Ridge, Lasso
    from sklearn.svm import SVR
    from sklearn.tree import DecisionTreeRegressor
    from sklearn.pipeline import Pipeline
    from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
except Exception as e:
    st.error(
        "❌ Missing dependency: **scikit-learn**.\n\n"
        "Fix:\n"
        "1) Open your **requirements.txt**\n"
        "2) Add this line: `scikit-learn>=1.3.0`\n"
        "3) Commit + redeploy.\n\n"
        f"Details: {e}"
    )
    st.stop()

from scipy.stats import linregress
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.utils import get_column_letter

# ---------------------------------------------------------------------------------------
# PAGE CONFIG & INITIALIZATION
# ---------------------------------------------------------------------------------------
st.set_page_config(
    page_title="CAPEX AI RT2026",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------------------
# DESIGN SYSTEM - PETRONAS BRANDING
# ---------------------------------------------------------------------------------------
PETRONAS = {
    # Primary Colors
    "teal": "#00A19B",
    "teal_dark": "#008C87",
    "teal_light": "#E0F7FA",
    "purple": "#6C4DD3",
    "purple_light": "#F3F0FF",
    
    # Neutrals
    "white": "#FFFFFF",
    "black": "#0E1116",
    "gray_50": "#F8F9FA",
    "gray_100": "#E9ECEF",
    "gray_200": "#DEE2E6",
    "gray_300": "#CED4DA",
    "gray_700": "#495057",
    
    # Semantic Colors
    "success": "#28A745",
    "warning": "#FFC107",
    "error": "#DC3545",
    "info": "#17A2B8",
    
    # UI Tokens
    "border": "rgba(0,0,0,0.10)",
    "shadow": "0 4px 20px rgba(0,0,0,0.08)",
    "radius": "12px"
}

# ---------------------------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------------------------------------
def initialize_session_state():
    """Initialize all session state variables with default values"""
    defaults = {
        "datasets": {},
        "predictions": {},
        "processed_excel_files": set(),
        "_last_metrics": None,
        "projects": {},
        "component_labels": {},
        "uploader_nonce": 0,
        "widget_nonce": 0,
        "training_history": {},  # Track training runs
        "current_view": "data",   # Track current tab
        "authenticated": False,
        "active_dataset": None,
        "model_cache": {},
        "notification_queue": [],
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

# ---------------------------------------------------------------------------------------
# ENHANCED HELPER FUNCTIONS
# ---------------------------------------------------------------------------------------
def compute_data_hash(df: pd.DataFrame) -> str:
    """Compute hash of dataframe for caching"""
    try:
        return hashlib.md5(
            pd.util.hash_pandas_object(df, index=True).values
        ).hexdigest()
    except Exception:
        return str(id(df))

def show_toast(msg: str, icon: str = "✅", duration: int = 3):
    """Improved toast notification with better UX"""
    try:
        st.toast(f"{icon} {msg}", icon=icon)
    except Exception:
        if icon == "✅":
            st.success(msg)
        elif icon == "⚠️":
            st.warning(msg)
        elif icon == "❌":
            st.error(msg)
        else:
            st.info(msg)

def format_currency(num: float, currency: str = "") -> str:
    """Format number as currency with proper formatting"""
    try:
        formatted = f"{float(num):,.2f}"
        return f"{currency} {formatted}".strip() if currency else formatted
    except Exception:
        return str(num)

def normalize_to_100(d: Dict[str, float]) -> Tuple[Dict[str, float], float]:
    """Normalize dictionary values to sum to 100%"""
    total = sum(float(v) for v in d.values())
    if total <= 0:
        return d, total
    
    out = {k: float(v) * 100.0 / total for k, v in d.items()}
    keys = list(out.keys())
    rounded = {k: round(out[k], 2) for k in keys}
    
    diff = 100.0 - sum(rounded.values())
    if keys:
        rounded[keys[-1]] = round(rounded[keys[-1]] + diff, 2)
    
    return rounded, total

def validate_dataframe(
    df: pd.DataFrame,
    min_rows: int = 2,
    min_cols: int = 2
) -> Tuple[bool, str]:
    """Validate dataframe has minimum requirements"""
    if df is None or df.empty:
        return False, "Dataset is empty"
    
    if df.shape[0] < min_rows:
        return False, f"Dataset has only {df.shape[0]} rows. Need at least {min_rows}."
    
    numeric_cols = df.select_dtypes(include=[np.number]).shape[1]
    if numeric_cols < min_cols:
        return False, f"Dataset has only {numeric_cols} numeric columns. Need at least {min_cols}."
    
    return True, "Valid"

def get_last_column_target(df: pd.DataFrame) -> str:
    """Get the last column name (target column)"""
    if df is None or df.empty:
        raise ValueError("Empty dataset provided.")
    return str(df.columns[-1])

def coerce_series_numeric(s: pd.Series) -> pd.Series:
    """Safely coerce series to numeric"""
    if pd.api.types.is_numeric_dtype(s):
        return s.astype(float)
    return pd.to_numeric(s, errors="coerce")

def numeric_features_from_df(df: pd.DataFrame, target_col: str) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Extract numeric features and target from dataframe.
    Target is always the last column, safely coerced to numeric.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column not found: {target_col}")

    # Coerce target to numeric
    y_raw = df[target_col]
    y = coerce_series_numeric(y_raw)

    # Features: numeric columns excluding target
    X = df.drop(columns=[target_col]).select_dtypes(include=[np.number]).copy()

    if X.shape[1] < 1:
        raise ValueError("Need at least 1 numeric feature column (excluding target).")

    # Fallback if target is unusable
    if y.dropna().shape[0] == 0:
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(num_cols) >= 2:
            fallback = num_cols[-1]
            st.warning(
                f"⚠️ Last column '{target_col}' could not be converted to numeric. "
                f"Falling back to last numeric column '{fallback}'."
            )
            y = df[fallback].astype(float)
            X = df.drop(columns=[fallback]).select_dtypes(include=[np.number]).copy()
            target_col = str(fallback)
        else:
            raise ValueError(
                f"Last column '{target_col}' is not numeric and no numeric fallback target exists."
            )

    return X, y.astype(float)

def is_junk_col(colname: str) -> bool:
    """Identify junk column names"""
    h = str(colname).strip().upper()
    return (not h) or h.startswith("UNNAMED") or h in {"INDEX", "IDX"}

def get_currency_symbol(df: pd.DataFrame, target_col: Optional[str] = None) -> str:
    """Extract currency symbol from column headers"""
    if df is None or df.empty:
        return ""
    
    if target_col and target_col in df.columns:
        header = str(target_col).upper()
        if "€" in header: return "€"
        if "£" in header: return "£"
        if "$" in header: return "$"
        if "USD" in header: return "USD"
        if re.search(r"\b(MYR|RM)\b", header): return "RM"
    
    for c in reversed(df.columns):
        if not is_junk_col(c):
            header = str(c).upper()
            if "€" in header: return "€"
            if "£" in header: return "£"
            if "$" in header: return "$"
            if "USD" in header: return "USD"
            if re.search(r"\b(MYR|RM)\b", header): return "RM"
    
    return ""

# ---------------------------------------------------------------------------------------
# GLOBAL CSS WITH ENHANCED DESIGN
# ---------------------------------------------------------------------------------------
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* {{
    font-family: 'Inter', sans-serif;
    transition: all 0.2s ease-in-out;
}}

[data-testid="stAppViewContainer"] {{
    background: linear-gradient(135deg, {PETRONAS["gray_50"]} 0%, {PETRONAS["white"]} 100%);
    background-attachment: fixed;
}}

.main .block-container {{
    padding-top: 1rem;
    padding-bottom: 2rem;
    max-width: 100%;
}}

/* Hero Section */
.petronas-hero {{
    border-radius: {PETRONAS["radius"]};
    padding: 2.5rem 3rem;
    margin: 1rem 0 2.5rem 0;
    color: {PETRONAS["white"]};
    background: linear-gradient(135deg, 
        {PETRONAS["teal"]} 0%, 
        {PETRONAS["purple"]} 50%, 
        {PETRONAS["black"]} 100%);
    background-size: 200% 200%;
    animation: heroGradient 8s ease-in-out infinite, 
               fadeIn 0.8s ease-in-out,
               heroPulse 5s ease-in-out infinite;
    box-shadow: 0 12px 32px rgba(0, 161, 155, 0.2);
    position: relative;
    overflow: hidden;
}}

.petronas-hero::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(circle at 30% 20%, 
        rgba(255,255,255,0.1) 0%, 
        transparent 70%);
}}

.petronas-hero h1 {{
    margin: 0 0 0.75rem;
    font-weight: 800;
    font-size: 2.5rem;
    letter-spacing: -0.5px;
    position: relative;
    z-index: 2;
}}

.petronas-hero p {{
    margin: 0;
    opacity: 0.95;
    font-weight: 500;
    font-size: 1.1rem;
    position: relative;
    z-index: 2;
}}

/* Cards */
.card {{
    background: {PETRONAS["white"]};
    border-radius: {PETRONAS["radius"]};
    padding: 1.5rem;
    border: 1px solid {PETRONAS["border"]};
    box-shadow: {PETRONAS["shadow"]};
    margin-bottom: 1rem;
}}

.card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}}

/* Buttons */
.stButton > button,
.stDownloadButton > button,
.petronas-button {{
    border-radius: 10px;
    padding: 0.75rem 1.5rem;
    font-weight: 600;
    font-size: 0.95rem;
    color: {PETRONAS["white"]} !important;
    border: none;
    background: linear-gradient(135deg, {PETRONAS["teal"]}, {PETRONAS["purple"]});
    background-size: 200% auto;
    transition: all 0.3s ease !important;
    position: relative;
    overflow: hidden;
}}

.stButton > button:hover,
.stDownloadButton > button:hover,
.petronas-button:hover {{
    background-position: right center;
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(108, 77, 211, 0.3);
}}

.stButton > button:disabled,
.stDownloadButton > button:disabled {{
    opacity: 0.6;
    cursor: not-allowed;
    transform: none !important;
}}

/* Tabs */
.stTabs [role="tablist"] {{
    gap: 4px;
    border-bottom: 2px solid {PETRONAS["gray_100"]};
    padding-bottom: 0;
}}

.stTabs [role="tab"] {{
    background: transparent;
    color: {PETRONAS["gray_700"]};
    border-radius: 8px 8px 0 0;
    padding: 12px 24px;
    border: none;
    font-weight: 600;
    transition: all 0.3s ease;
    margin: 0 2px;
}}

.stTabs [role="tab"]:hover {{
    background: {PETRONAS["teal_light"]};
    color: {PETRONAS["teal"]};
}}

.stTabs [role="tab"][aria-selected="true"] {{
    background: {PETRONAS["white"]};
    color: {PETRONAS["teal"]};
    border-bottom: 3px solid {PETRONAS["teal"]};
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}}

/* Metrics */
[data-testid="stMetric"] {{
    background: {PETRONAS["white"]};
    border-radius: {PETRONAS["radius"]};
    padding: 1rem;
    border: 1px solid {PETRONAS["border"]};
}}

[data-testid="stMetricValue"] {{
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    color: {PETRONAS["teal"]} !important;
}}

[data-testid="stMetricLabel"] {{
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    color: {PETRONAS["gray_700"]} !important;
}}

/* Progress bars */
.stProgress > div > div > div {{
    background: linear-gradient(90deg, {PETRONAS["teal"]}, {PETRONAS["purple"]});
}}

/* Dataframes */
.dataframe {{
    border-radius: 8px !important;
    overflow: hidden !important;
}}

/* Animations */
@keyframes heroGradient {{
    0% {{ background-position: 0% 50%; }}
    50% {{ background-position: 100% 50%; }}
    100% {{ background-position: 0% 50%; }}
}}

@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(20px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

@keyframes heroPulse {{
    0%, 100% {{ box-shadow: 0 12px 32px rgba(0, 161, 155, 0.2); }}
    50% {{ box-shadow: 0 12px 40px rgba(108, 77, 211, 0.3); }}
}}

@keyframes glowSlide {{
    0% {{ background-position: 0% 50%; }}
    50% {{ background-position: 100% 50%; }}
    100% {{ background-position: 0% 50%; }}
}}

/* Responsive */
@media (max-width: 768px) {{
    .petronas-hero {{
        padding: 1.5rem;
        margin: 0.5rem 0 1.5rem 0;
    }}
    
    .petronas-hero h1 {{
        font-size: 1.8rem;
    }}
    
    .petronas-hero p {{
        font-size: 1rem;
    }}
    
    .stTabs [role="tab"] {{
        padding: 8px 16px;
        font-size: 0.9rem;
    }}
}}

/* Custom scrollbar */
::-webkit-scrollbar {{
    width: 8px;
    height: 8px;
}}

::-webkit-scrollbar-track {{
    background: {PETRONAS["gray_100"]};
    border-radius: 4px;
}}

::-webkit-scrollbar-thumb {{
    background: linear-gradient({PETRONAS["teal"]}, {PETRONAS["purple"]});
    border-radius: 4px;
}}

::-webkit-scrollbar-thumb:hover {{
    background: linear-gradient({PETRONAS["teal_dark"]}, {PETRONAS["purple"]});
}}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------------------
# SHAREPOINT LINKS
# ---------------------------------------------------------------------------------------
SHAREPOINT_LINKS = {
    "Shallow Water": "https://petronas.sharepoint.com/sites/your-site/shallow-water",
    "Deep Water": "https://petronas.sharepoint.com/sites/your-site/deep-water",
    "Onshore": "https://petronas.sharepoint.com/sites/your-site/onshore",
    "Uncon": "https://petronas.sharepoint.com/sites/your-site/uncon",
    "CCS": "https://petronas.sharepoint.com/sites/your-site/ccs",
}

# ---------------------------------------------------------------------------------------
# HERO HEADER
# ---------------------------------------------------------------------------------------
st.markdown(
    """
<div class="petronas-hero">
  <h1>CAPEX AI RT2026</h1>
  <p>Advanced data-driven CAPEX prediction and project analysis</p>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------------------------------------
if not st.session_state.authenticated:
    APPROVED_EMAILS = [str(e).strip().lower() for e in st.secrets.get("emails", [])]
    correct_password = st.secrets.get("password", None)
    
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        with st.form("login_form"):
            st.markdown("### 🔐 Access Required")
            col1, col2 = st.columns(2)
            with col1:
                email = st.text_input("Email Address", key="login_email")
            with col2:
                password = st.text_input("Access Password", type="password", key="login_pwd")
            
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                email_clean = email.strip().lower()
                if email_clean in APPROVED_EMAILS and password == correct_password:
                    st.session_state.authenticated = True
                    show_toast("✅ Access granted. Welcome!", "✅")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials. Please try again.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ---------------------------------------------------------------------------------------
# NAVIGATION ROW - SHAREPOINT BUTTONS
# ---------------------------------------------------------------------------------------
nav_labels = ["SHALLOW WATER", "DEEP WATER", "ONSHORE", "UNCON", "CCS"]
nav_cols = st.columns(len(nav_labels))
for col, label in zip(nav_cols, nav_labels):
    with col:
        url = SHAREPOINT_LINKS.get(label.title(), "#")
        st.markdown(
            f'''
            <a href="{url}" target="_blank" rel="noopener"
               class="petronas-button"
               style="width:100%; text-align:center; display:inline-block;">
               {label}
            </a>
            ''',
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------------------
# TOP-LEVEL TABS WITH ENHANCED LABELS
# ---------------------------------------------------------------------------------------
tab_data, tab_pb, tab_mc, tab_compare = st.tabs([
    "📊 **Data & Modeling**", 
    "🏗️ **Project Builder**", 
    "🎲 **Monte Carlo**", 
    "🔀 **Compare Projects**"
])

# =======================================================================================
# DATA TAB - ENHANCED WITH SECTIONS
# =======================================================================================
with tab_data:
    st.markdown('<h2 style="color:#000;">📊 Data & Modeling</h2>', unsafe_allow_html=True)
    
    # --- SECTION 1: DATA SOURCES ---
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 1️⃣ Data Sources")
        
        col1, col2 = st.columns([1.2, 1])
        with col1:
            data_source = st.radio(
                "Choose data source",
                ["Upload CSV", "Load from Server"],
                horizontal=True,
                key="data_source"
            )
        
        with col2:
            st.caption("Enterprise Storage (SharePoint)")
            data_link = "https://petronas.sharepoint.com/sites/ecm_ups_coe/confidential/DFE%20Cost%20Engineering"
            st.markdown(
                f'<a href="{data_link}" target="_blank" rel="noopener" class="petronas-button">Open Enterprise Storage</a>',
                unsafe_allow_html=True,
            )
        
        uploaded_files = []
        if data_source == "Upload CSV":
            uploaded_files = st.file_uploader(
                "Upload CSV files (max 200MB)",
                type="csv",
                accept_multiple_files=True,
                help="Upload one or more CSV files for analysis",
                key=f"csv_uploader_{st.session_state.uploader_nonce}"
            )
        else:
            # GitHub data loading (simplified)
            st.info("Server loading requires GitHub integration setup.")
        
        if uploaded_files:
            with st.spinner("Processing uploaded files..."):
                for up in uploaded_files:
                    if up.name not in st.session_state.datasets:
                        try:
                            df = pd.read_csv(up)
                            # Validate dataset
                            is_valid, message = validate_dataframe(df)
                            if is_valid:
                                st.session_state.datasets[up.name] = df
                                st.session_state.predictions.setdefault(up.name, [])
                                st.session_state.active_dataset = up.name
                                show_toast(f"✅ Loaded: {up.name} ({df.shape[0]} rows, {df.shape[1]} columns)")
                            else:
                                st.warning(f"Skipped {up.name}: {message}")
                        except Exception as e:
                            st.error(f"Failed to read {up.name}: {e}")
                if uploaded_files:
                    st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.divider()
    
    # --- SECTION 2: DATASET PREVIEW ---
    if st.session_state.datasets:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 2️⃣ Dataset Preview")
            
            ds_name = st.selectbox(
                "Select dataset",
                list(st.session_state.datasets.keys()),
                index=0,
                key="active_dataset_select"
            )
            df = st.session_state.datasets[ds_name]
            
            # Quick stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Rows", f"{df.shape[0]:,}")
            with col2:
                st.metric("Columns", f"{df.shape[1]:,}")
            with col3:
                numeric_cols = df.select_dtypes(include=[np.number]).shape[1]
                st.metric("Numeric Columns", f"{numeric_cols}")
            with col4:
                currency = get_currency_symbol(df)
                st.metric("Currency", currency if currency else "—")
            
            # Data preview
            with st.expander("📋 Preview Data (first 20 rows)", expanded=False):
                st.dataframe(df.head(20), use_container_width=True)
            
            # Data info
            with st.expander("ℹ️ Dataset Information", expanded=False):
                buffer = io.StringIO()
                df.info(buf=buffer)
                st.text(buffer.getvalue())
                
                # Missing values
                missing = df.isnull().sum()
                if missing.sum() > 0:
                    st.write("Missing values per column:")
                    st.dataframe(missing[missing > 0])
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    st.divider()
    
    # --- SECTION 3: MODEL TRAINING ---
    if st.session_state.datasets:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 3️⃣ Model Training")
            
            ds_train = st.selectbox(
                "Dataset for training",
                list(st.session_state.datasets.keys()),
                key="train_dataset_select"
            )
            df_train = st.session_state.datasets[ds_train]
            target_col = get_last_column_target(df_train)
            
            col1, col2 = st.columns([1, 3])
            with col1:
                test_size = st.slider(
                    "Test size ratio",
                    0.1, 0.5, 0.2, 0.05,
                    help="Proportion of data to use for testing",
                    key="test_size_slider"
                )
                random_state = st.number_input("Random seed", 0, 1000, 42, key="random_state")
                
                if st.button("🚀 Train Models", use_container_width=True, key="train_button"):
                    st.session_state.training_history[ds_train] = {
                        "timestamp": pd.Timestamp.now(),
                        "test_size": test_size,
                        "random_state": random_state
                    }
            
            with col2:
                st.caption(f"**Target column (last column):** {target_col}")
                st.caption("""
                The following models will be evaluated:
                - Random Forest Regressor
                - Gradient Boosting Regressor
                - Ridge Regression
                - Lasso Regression
                - Support Vector Regressor
                - Decision Tree Regressor
                """)
            
            # Model training execution
            if "train_button" in st.session_state and st.session_state.train_button:
                try:
                    with st.spinner("Training models... This may take a moment."):
                        progress_bar = st.progress(0)
                        
                        # Prepare data
                        X, y = numeric_features_from_df(df_train, target_col)
                        
                        # Split data
                        X_train, X_test, y_train, y_test = train_test_split(
                            X, y, test_size=test_size, random_state=random_state
                        )
                        
                        # Model candidates with enhanced parameters
                        MODEL_CANDIDATES = {
                            "RandomForest": lambda: RandomForestRegressor(
                                n_estimators=100,
                                max_depth=10,
                                random_state=random_state,
                                n_jobs=-1  # Parallel processing
                            ),
                            "GradientBoosting": lambda: GradientBoostingRegressor(
                                n_estimators=100,
                                learning_rate=0.1,
                                random_state=random_state
                            ),
                            "Ridge": lambda: Ridge(alpha=1.0),
                            "Lasso": lambda: Lasso(alpha=0.1),
                            "SVR": lambda: SVR(kernel='rbf', C=1.0),
                            "DecisionTree": lambda: DecisionTreeRegressor(
                                max_depth=10,
                                random_state=random_state
                            ),
                        }
                        
                        SCALE_MODELS = {"Ridge", "Lasso", "SVR"}
                        
                        def make_pipeline(model_name: str):
                            ctor = MODEL_CANDIDATES[model_name]
                            model = ctor()
                            
                            steps = [("imputer", SimpleImputer(strategy="median"))]
                            if model_name in SCALE_MODELS:
                                steps.append(("scaler", MinMaxScaler()))
                            steps.append(("model", model))
                            return Pipeline(steps)
                        
                        # Evaluate models
                        results = []
                        model_count = len(MODEL_CANDIDATES)
                        
                        for idx, (name, _) in enumerate(MODEL_CANDIDATES.items()):
                            try:
                                pipe = make_pipeline(name)
                                pipe.fit(X_train, y_train)
                                y_pred = pipe.predict(X_test)
                                
                                rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
                                mae = float(mean_absolute_error(y_test, y_pred))
                                r2 = float(r2_score(y_test, y_pred))
                                
                                results.append({
                                    "model": name,
                                    "rmse": rmse,
                                    "mae": mae,
                                    "r2": r2
                                })
                                
                                progress_bar.progress((idx + 1) / model_count)
                                st.session_state.model_cache[f"{ds_train}_{name}"] = pipe
                                
                            except Exception as e:
                                st.warning(f"Model {name} failed: {str(e)}")
                                continue
                        
                        # Find best model
                        if results:
                            results_df = pd.DataFrame(results)
                            best_row = results_df.loc[results_df['r2'].idxmax()]
                            
                            st.session_state._last_metrics = {
                                "best_model": best_row["model"],
                                "rmse": best_row["rmse"],
                                "mae": best_row["mae"],
                                "r2": best_row["r2"],
                                "models": results
                            }
                            
                            # Display results
                            st.success("✅ Training complete!")
                            
                            # Best model metrics
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Best Model", best_row["model"])
                            with col2:
                                st.metric("R² Score", f"{best_row['r2']:.3f}")
                            with col3:
                                st.metric("RMSE", f"{best_row['rmse']:,.2f}")
                            with col4:
                                st.metric("MAE", f"{best_row['mae']:,.2f}")
                            
                            # Model comparison table with styling
                            st.markdown("#### Model Comparison")
                            results_df_sorted = results_df.sort_values("r2", ascending=False)
                            
                            # Apply color gradient to R² column
                            def color_r2(val):
                                if val >= 0.8:
                                    return f"background-color: {PETRONAS['success']}; color: white;"
                                elif val >= 0.6:
                                    return f"background-color: {PETRONAS['warning']}; color: black;"
                                else:
                                    return f"background-color: {PETRONAS['error']}; color: white;"
                            
                            styled_df = results_df_sorted.style.format({
                                "rmse": "{:,.2f}",
                                "mae": "{:,.2f}",
                                "r2": "{:.3f}"
                            }).applymap(color_r2, subset=['r2'])
                            
                            st.dataframe(styled_df, use_container_width=True)
                            
                            # Feature importance for tree-based models
                            if best_row["model"] in ["RandomForest", "GradientBoosting", "DecisionTree"]:
                                st.markdown("#### Feature Importance")
                                best_pipe = st.session_state.model_cache[f"{ds_train}_{best_row['model']}"]
                                
                                if hasattr(best_pipe.named_steps['model'], 'feature_importances_'):
                                    importances = best_pipe.named_steps['model'].feature_importances_
                                    feat_imp_df = pd.DataFrame({
                                        'feature': X.columns,
                                        'importance': importances
                                    }).sort_values('importance', ascending=True)
                                    
                                    fig = px.bar(
                                        feat_imp_df.tail(20),  # Top 20 features
                                        x='importance',
                                        y='feature',
                                        orientation='h',
                                        title=f"Feature Importance - {best_row['model']}",
                                        color='importance',
                                        color_continuous_scale=[PETRONAS['teal_light'], PETRONAS['teal']]
                                    )
                                    fig.update_layout(height=400)
                                    st.plotly_chart(fig, use_container_width=True)
                        
                except Exception as e:
                    st.error(f"Training failed: {str(e)}")
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    st.divider()
    
    # --- SECTION 4: DATA VISUALIZATION ---
    if st.session_state.datasets:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 4️⃣ Data Visualization")
            
            ds_viz = st.selectbox(
                "Dataset for visualization",
                list(st.session_state.datasets.keys()),
                key="viz_dataset_select"
            )
            df_viz = st.session_state.datasets[ds_viz]
            
            tab_corr, tab_dist, tab_relationships = st.tabs([
                "📈 Correlation Matrix",
                "📊 Distributions",
                "🔗 Relationships"
            ])
            
            with tab_corr:
                # Correlation heatmap
                numeric_cols = df_viz.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 1:
                    corr_matrix = df_viz[numeric_cols].corr()
                    
                    fig = px.imshow(
                        corr_matrix,
                        text_auto=".2f",
                        aspect="auto",
                        color_continuous_scale="RdBu_r",
                        zmin=-1,
                        zmax=1,
                        title="Correlation Matrix"
                    )
                    fig.update_layout(height=600)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Need at least 2 numeric columns for correlation matrix.")
            
            with tab_dist:
                # Distribution plots
                if len(numeric_cols) > 0:
                    selected_col = st.selectbox("Select column", numeric_cols, key="dist_col")
                    
                    fig = px.histogram(
                        df_viz,
                        x=selected_col,
                        nbins=50,
                        title=f"Distribution of {selected_col}",
                        color_discrete_sequence=[PETRONAS['teal']]
                    )
                    fig.update_layout(bargap=0.1)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Box plot
                    fig_box = px.box(
                        df_viz,
                        y=selected_col,
                        title=f"Box Plot of {selected_col}",
                        color_discrete_sequence=[PETRONAS['purple']]
                    )
                    st.plotly_chart(fig_box, use_container_width=True)
            
            with tab_relationships:
                # Scatter plots
                if len(numeric_cols) >= 2:
                    col1, col2 = st.columns(2)
                    with col1:
                        x_col = st.selectbox("X-axis", numeric_cols, key="scatter_x")
                    with col2:
                        y_col = st.selectbox("Y-axis", numeric_cols, key="scatter_y")
                    
                    if x_col != y_col:
                        fig = px.scatter(
                            df_viz,
                            x=x_col,
                            y=y_col,
                            title=f"{y_col} vs {x_col}",
                            trendline="ols",
                            color_discrete_sequence=[PETRONAS['teal']]
                        )
                        
                        # Add R² annotation
                        mask = df_viz[[x_col, y_col]].notna().all(axis=1)
                        if mask.sum() >= 2:
                            x_vals = df_viz.loc[mask, x_col].astype(float)
                            y_vals = df_viz.loc[mask, y_col].astype(float)
                            slope, intercept, r_value, p_value, std_err = linregress(x_vals, y_vals)
                            
                            fig.add_annotation(
                                x=0.05,
                                y=0.95,
                                xref="paper",
                                yref="paper",
                                text=f"R² = {r_value**2:.3f}",
                                showarrow=False,
                                font=dict(size=14, color=PETRONAS['purple']),
                                bgcolor="white",
                                bordercolor=PETRONAS['purple'],
                                borderwidth=1,
                                borderpad=4
                            )
                        
                        st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    st.divider()
    
    # --- SECTION 5: PREDICTIONS ---
    if st.session_state.datasets and st.session_state._last_metrics:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 5️⃣ Make Predictions")
            
            ds_pred = st.selectbox(
                "Dataset for predictions",
                list(st.session_state.datasets.keys()),
                key="pred_dataset_select"
            )
            df_pred = st.session_state.datasets[ds_pred]
            target_col = get_last_column_target(df_pred)
            currency = get_currency_symbol(df_pred, target_col)
            
            # WBS Level 1 inputs
            st.markdown("#### WBS Level 1 Percentages")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Cost Components**")
                eng = st.number_input("Engineering (%)", 0.0, 100.0, 12.0, 1.0, key="pred_eng")
                procurement = st.number_input("Procurement (%)", 0.0, 100.0, 33.0, 1.0, key="pred_proc")
                fabrication = st.number_input("Fabrication/Construction (%)", 0.0, 100.0, 33.0, 1.0, key="pred_fab")
                ti = st.number_input("Transportation & Installation (%)", 0.0, 100.0, 22.0, 1.0, key="pred_ti")
                
                eprr = {
                    "Engineering": eng,
                    "Procurement": procurement,
                    "Fabrication/Construction": fabrication,
                    "Transportation & Installation": ti
                }
                eprr_total = sum(eprr.values())
                st.metric("WBS Total", f"{eprr_total:.1f}%")
            
            with col2:
                st.markdown("**Additional Costs**")
                sst_pct = st.number_input("SST (%)", 0.0, 100.0, 0.0, 0.5, key="pred_sst")
                owners_pct = st.number_input("Owner's Cost (%)", 0.0, 100.0, 0.0, 0.5, key="pred_owner")
                cont_pct = st.number_input("Contingency (%)", 0.0, 100.0, 0.0, 0.5, key="pred_cont")
                esc_pct = st.number_input("Escalation & Inflation (%)", 0.0, 100.0, 0.0, 0.5, key="pred_esc")
            
            # Prediction inputs
            st.markdown("#### Feature Inputs")
            project_name = st.text_input(
                "Project Name",
                placeholder="e.g., Offshore Pipeline Replacement 2026",
                key="pred_project_name"
            )
            
            # Get best model for predictions
            best_model_name = st.session_state._last_metrics.get("best_model", "RandomForest")
            model_key = f"{ds_pred}_{best_model_name}"
            
            if model_key in st.session_state.model_cache:
                model_pipe = st.session_state.model_cache[model_key]
                
                # Get feature columns (exclude target)
                X, y = numeric_features_from_df(df_pred, target_col)
                feature_cols = X.columns.tolist()
                
                # Create input form
                input_data = {}
                cols = st.columns(3)
                for idx, feat in enumerate(feature_cols):
                    with cols[idx % 3]:
                        # Get descriptive statistics for guidance
                        if feat in df_pred.columns:
                            mean_val = df_pred[feat].mean()
                            std_val = df_pred[feat].std()
                            input_data[feat] = st.number_input(
                                f"{feat}",
                                value=float(mean_val) if not pd.isna(mean_val) else 0.0,
                                help=f"Mean: {mean_val:.2f}, Std: {std_val:.2f}",
                                key=f"pred_input_{feat}"
                            )
                
                if st.button("🔮 Predict", use_container_width=True, key="predict_button"):
                    try:
                        # Make prediction
                        input_df = pd.DataFrame([input_data], columns=feature_cols)
                        base_pred = float(model_pipe.predict(input_df)[0])
                        
                        # Calculate cost breakdown
                        def calculate_cost_breakdown(base_cost, eprr_dict, sst, owners, cont, esc):
                            base_cost = float(base_cost)
                            
                            owners_cost = base_cost * (owners / 100.0)
                            sst_cost = base_cost * (sst / 100.0)
                            contingency_cost = (base_cost + owners_cost) * (cont / 100.0)
                            escalation_cost = (base_cost + owners_cost) * (esc / 100.0)
                            
                            eprr_costs = {
                                k: base_cost * (v / 100.0)
                                for k, v in eprr_dict.items()
                            }
                            
                            grand_total = base_cost + owners_cost + sst_cost + contingency_cost + escalation_cost
                            
                            return {
                                "base_pred": base_cost,
                                "owners_cost": owners_cost,
                                "sst_cost": sst_cost,
                                "contingency_cost": contingency_cost,
                                "escalation_cost": escalation_cost,
                                "eprr_costs": eprr_costs,
                                "grand_total": grand_total
                            }
                        
                        breakdown = calculate_cost_breakdown(
                            base_pred, eprr, sst_pct, owners_pct, cont_pct, esc_pct
                        )
                        
                        # Store prediction
                        prediction_record = {
                            "project_name": project_name,
                            "timestamp": pd.Timestamp.now().isoformat(),
                            "dataset": ds_pred,
                            "model_used": best_model_name,
                            "inputs": input_data,
                            "predictions": breakdown,
                            "currency": currency
                        }
                        
                        st.session_state.predictions.setdefault(ds_pred, []).append(prediction_record)
                        
                        # Display results
                        st.success("✅ Prediction complete!")
                        
                        # Metrics display
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Base Prediction", f"{currency} {breakdown['base_pred']:,.2f}")
                        with col2:
                            st.metric("Owner's Cost", f"{currency} {breakdown['owners_cost']:,.2f}")
                        with col3:
                            st.metric("Contingency", f"{currency} {breakdown['contingency_cost']:,.2f}")
                        
                        col4, col5 = st.columns(2)
                        with col4:
                            st.metric("Escalation", f"{currency} {breakdown['escalation_cost']:,.2f}")
                        with col5:
                            st.metric("Grand Total", f"{currency} {breakdown['grand_total']:,.2f}", 
                                     delta=f"+{sst_pct:.1f}% SST")
                        
                    except Exception as e:
                        st.error(f"Prediction failed: {str(e)}")
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    st.divider()
    
    # --- SECTION 6: PREDICTION RESULTS ---
    if st.session_state.predictions:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 6️⃣ Prediction Results")
            
            ds_results = st.selectbox(
                "Dataset",
                [k for k, v in st.session_state.predictions.items() if v],
                key="results_dataset_select"
            )
            
            predictions = st.session_state.predictions.get(ds_results, [])
            
            if predictions:
                # Convert to DataFrame for display
                results_data = []
                for pred in predictions:
                    row = {
                        "Project": pred.get("project_name", "N/A"),
                        "Timestamp": pred.get("timestamp", ""),
                        "Base CAPEX": pred["predictions"]["base_pred"],
                        "Owner's Cost": pred["predictions"]["owners_cost"],
                        "SST": pred["predictions"]["sst_cost"],
                        "Contingency": pred["predictions"]["contingency_cost"],
                        "Escalation": pred["predictions"]["escalation_cost"],
                        "Grand Total": pred["predictions"]["grand_total"]
                    }
                    results_data.append(row)
                
                results_df = pd.DataFrame(results_data)
                
                # Display with formatting
                st.dataframe(
                    results_df.style.format({
                        "Base CAPEX": "{:,.2f}",
                        "Owner's Cost": "{:,.2f}",
                        "SST": "{:,.2f}",
                        "Contingency": "{:,.2f}",
                        "Escalation": "{:,.2f}",
                        "Grand Total": "{:,.2f}"
                    }),
                    use_container_width=True
                )
                
                # Export options
                st.markdown("#### Export Results")
                col1, col2 = st.columns(2)
                
                with col1:
                    # Excel export
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        results_df.to_excel(writer, sheet_name='Predictions', index=False)
                    excel_buffer.seek(0)
                    
                    st.download_button(
                        label="📥 Download Excel",
                        data=excel_buffer,
                        file_name=f"capex_predictions_{ds_results}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                with col2:
                    # CSV export
                    csv_buffer = io.StringIO()
                    results_df.to_csv(csv_buffer, index=False)
                    
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv_buffer.getvalue(),
                        file_name=f"capex_predictions_{ds_results}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                # Clear predictions button
                if st.button("🗑️ Clear All Predictions", type="secondary", use_container_width=True):
                    st.session_state.predictions[ds_results] = []
                    show_toast("Predictions cleared", "🗑️")
                    st.rerun()
            
            else:
                st.info("No predictions available. Make predictions in the previous section.")
            
            st.markdown("</div>", unsafe_allow_html=True)

# =======================================================================================
# PROJECT BUILDER TAB - ENHANCED
# =======================================================================================
with tab_pb:
    st.markdown('<h2 style="color:#000;">🏗️ Project Builder</h2>', unsafe_allow_html=True)
    
    # Section 1: Create/Select Project
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 1️⃣ Create/Select Project")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            new_project_name = st.text_input(
                "New Project Name",
                placeholder="e.g., CAPEX 2026 - Offshore Platform",
                key="new_project_name"
            )
        with col2:
            if st.button("➕ Create Project", use_container_width=True, key="create_project_btn"):
                if new_project_name and new_project_name not in st.session_state.projects:
                    st.session_state.projects[new_project_name] = {
                        "created": pd.Timestamp.now().isoformat(),
                        "components": [],
                        "currency": "",
                        "description": ""
                    }
                    show_toast(f"Project '{new_project_name}' created", "✅")
                    st.rerun()
        
        if st.session_state.projects:
            selected_project = st.selectbox(
                "Select Project",
                list(st.session_state.projects.keys()),
                key="project_select"
            )
            st.caption(f"Project created: {st.session_state.projects[selected_project].get('created', 'N/A')}")
        else:
            st.info("No projects yet. Create a project to get started.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    if st.session_state.projects:
        st.divider()
        
        # Section 2: Add Component
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 2️⃣ Add Component")
            
            if not st.session_state.datasets:
                st.warning("No datasets available. Upload data in the Data tab first.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    component_dataset = st.selectbox(
                        "Dataset",
                        list(st.session_state.datasets.keys()),
                        key="component_dataset"
                    )
                    component_type = st.text_input(
                        "Component Type",
                        placeholder="e.g., Platform, Pipeline, Subsea",
                        key="component_type"
                    )
                
                with col2:
                    df_comp = st.session_state.datasets[component_dataset]
                    target_col = get_last_column_target(df_comp)
                    currency = get_currency_symbol(df_comp, target_col)
                    
                    st.caption(f"Target: {target_col}")
                    st.caption(f"Currency: {currency}")
                
                # Component inputs
                st.markdown("#### Feature Values")
                X_comp, y_comp = numeric_features_from_df(df_comp, target_col)
                feature_cols = X_comp.columns.tolist()
                
                input_data = {}
                cols = st.columns(3)
                for idx, feat in enumerate(feature_cols):
                    with cols[idx % 3]:
                        if feat in df_comp.columns:
                            mean_val = df_comp[feat].mean()
                            input_data[feat] = st.number_input(
                                feat,
                                value=float(mean_val) if not pd.isna(mean_val) else 0.0,
                                key=f"comp_input_{feat}"
                            )
                
                # Cost percentages
                st.markdown("#### Cost Percentages")
                cost_col1, cost_col2 = st.columns(2)
                
                with cost_col1:
                    eng_pct = st.number_input("Engineering %", 0.0, 100.0, 12.0, key="comp_eng")
                    proc_pct = st.number_input("Procurement %", 0.0, 100.0, 33.0, key="comp_proc")
                    fab_pct = st.number_input("Fabrication %", 0.0, 100.0, 33.0, key="comp_fab")
                    ti_pct = st.number_input("T&I %", 0.0, 100.0, 22.0, key="comp_ti")
                
                with cost_col2:
                    sst_pct = st.number_input("SST %", 0.0, 100.0, 0.0, key="comp_sst")
                    owner_pct = st.number_input("Owner's %", 0.0, 100.0, 0.0, key="comp_owner")
                    cont_pct = st.number_input("Contingency %", 0.0, 100.0, 0.0, key="comp_cont")
                    esc_pct = st.number_input("Escalation %", 0.0, 100.0, 0.0, key="comp_esc")
                
                if st.button("➕ Add Component to Project", use_container_width=True, key="add_component_btn"):
                    try:
                        # Get or train model
                        model_key = f"{component_dataset}_RandomForest"
                        if model_key not in st.session_state.model_cache:
                            pipe, _, _, _, _ = train_best_model_cached(
                                df_comp, target_col, 0.2, 42, component_dataset
                            )
                            st.session_state.model_cache[model_key] = pipe
                        
                        model_pipe = st.session_state.model_cache[model_key]
                        
                        # Make prediction
                        input_df = pd.DataFrame([input_data], columns=feature_cols)
                        base_pred = float(model_pipe.predict(input_df)[0])
                        
                        # Calculate costs
                        eprr = {
                            "Engineering": eng_pct,
                            "Procurement": proc_pct,
                            "Fabrication": fab_pct,
                            "T&I": ti_pct
                        }
                        
                        breakdown = calculate_cost_breakdown(
                            base_pred, eprr, sst_pct, owner_pct, cont_pct, esc_pct
                        )
                        
                        # Create component
                        component = {
                            "type": component_type or "Unnamed Component",
                            "dataset": component_dataset,
                            "timestamp": pd.Timestamp.now().isoformat(),
                            "model_used": "RandomForest",
                            "inputs": input_data,
                            "predictions": breakdown
                        }
                        
                        # Add to project
                        project = st.session_state.projects[selected_project]
                        project["components"].append(component)
                        project["currency"] = currency
                        
                        show_toast(f"Component added to {selected_project}", "✅")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Failed to add component: {str(e)}")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.divider()
        
        # Section 3: Project Overview
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 3️⃣ Project Overview")
            
            project = st.session_state.projects[selected_project]
            components = project.get("components", [])
            
            if not components:
                st.info("No components in this project yet.")
            else:
                # Calculate totals
                totals = {
                    "base_capex": 0.0,
                    "owners_cost": 0.0,
                    "sst_cost": 0.0,
                    "contingency": 0.0,
                    "escalation": 0.0,
                    "grand_total": 0.0
                }
                
                component_data = []
                for comp in components:
                    preds = comp["predictions"]
                    component_data.append({
                        "Component": comp["type"],
                        "Base CAPEX": preds["base_pred"],
                        "Owner's": preds["owners_cost"],
                        "SST": preds["sst_cost"],
                        "Contingency": preds["contingency_cost"],
                        "Escalation": preds["escalation_cost"],
                        "Total": preds["grand_total"]
                    })
                    
                    totals["base_capex"] += preds["base_pred"]
                    totals["owners_cost"] += preds["owners_cost"]
                    totals["sst_cost"] += preds["sst_cost"]
                    totals["contingency"] += preds["contingency_cost"]
                    totals["escalation"] += preds["escalation_cost"]
                    totals["grand_total"] += preds["grand_total"]
                
                # Display totals
                currency = project.get("currency", "")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Base CAPEX", f"{currency} {totals['base_capex']:,.2f}")
                with col2:
                    st.metric("Total Owner's Cost", f"{currency} {totals['owners_cost']:,.2f}")
                with col3:
                    st.metric("Grand Total", f"{currency} {totals['grand_total']:,.2f}")
                
                # Component table
                st.markdown("#### Components")
                comp_df = pd.DataFrame(component_data)
                st.dataframe(
                    comp_df.style.format({
                        "Base CAPEX": "{:,.2f}",
                        "Owner's": "{:,.2f}",
                        "SST": "{:,.2f}",
                        "Contingency": "{:,.2f}",
                        "Escalation": "{:,.2f}",
                        "Total": "{:,.2f}"
                    }),
                    use_container_width=True
                )
                
                # Visualizations
                st.markdown("#### Cost Breakdown")
                tab1, tab2 = st.tabs(["Stacked Bar", "Pie Chart"])
                
                with tab1:
                    fig = px.bar(
                        comp_df,
                        x="Component",
                        y=["Base CAPEX", "Owner's", "SST", "Contingency", "Escalation"],
                        title="Cost Composition by Component",
                        barmode="stack",
                        color_discrete_sequence=[
                            PETRONAS["teal"],
                            PETRONAS["purple"],
                            PETRONAS["success"],
                            PETRONAS["warning"],
                            PETRONAS["error"]
                        ]
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                
                with tab2:
                    total_costs = {
                        "Base CAPEX": totals["base_capex"],
                        "Owner's": totals["owners_cost"],
                        "SST": totals["sst_cost"],
                        "Contingency": totals["contingency"],
                        "Escalation": totals["escalation"]
                    }
                    fig = px.pie(
                        values=list(total_costs.values()),
                        names=list(total_costs.keys()),
                        title="Overall Cost Distribution",
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.divider()
        
        # Section 4: Export/Import
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 4️⃣ Export/Import")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Export Project")
                
                # JSON Export
                json_data = json.dumps(project, indent=2, default=str)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_data,
                    file_name=f"{selected_project}.json",
                    mime="application/json",
                    use_container_width=True
                )
                
                # Excel Export
                if components:
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        # Summary sheet
                        summary_data = {
                            "Metric": ["Base CAPEX", "Owner's Cost", "SST", "Contingency", "Escalation", "Grand Total"],
                            "Amount": [
                                totals["base_capex"],
                                totals["owners_cost"],
                                totals["sst_cost"],
                                totals["contingency"],
                                totals["escalation"],
                                totals["grand_total"]
                            ]
                        }
                        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
                        
                        # Components sheet
                        comp_df.to_excel(writer, sheet_name='Components', index=False)
                    
                    excel_buffer.seek(0)
                    
                    st.download_button(
                        label="📥 Download Excel",
                        data=excel_buffer,
                        file_name=f"{selected_project}_report.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            
            with col2:
                st.markdown("#### Import Project")
                uploaded_json = st.file_uploader(
                    "Upload project JSON",
                    type=['json'],
                    key="project_upload"
                )
                
                if uploaded_json is not None:
                    try:
                        imported_data = json.load(uploaded_json)
                        import_name = st.text_input(
                            "Project name for import",
                            value=selected_project,
                            key="import_name"
                        )
                        
                        if st.button("📤 Import Project", use_container_width=True):
                            st.session_state.projects[import_name] = imported_data
                            show_toast(f"Project '{import_name}' imported", "✅")
                            st.rerun()
                    
                    except Exception as e:
                        st.error(f"Import failed: {str(e)}")
            
            st.markdown("</div>", unsafe_allow_html=True)

# =======================================================================================
# MONTE CARLO TAB - ENHANCED
# =======================================================================================
with tab_mc:
    st.markdown('<h2 style="color:#000;">🎲 Monte Carlo Simulation</h2>', unsafe_allow_html=True)
    
    if not st.session_state.projects:
        st.info("No projects found. Create a project in the Project Builder first.")
    else:
        # Section 1: Simulation Settings
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 1️⃣ Simulation Settings")
            
            mc_project = st.selectbox(
                "Project",
                list(st.session_state.projects.keys()),
                key="mc_project_select"
            )
            
            project = st.session_state.projects[mc_project]
            components = project.get("components", [])
            
            if not components:
                st.warning("Selected project has no components.")
            else:
                col1, col2, col3 = st.columns(3)
                with col1:
                    n_simulations = st.number_input(
                        "Number of Simulations",
                        min_value=100,
                        max_value=100000,
                        value=5000,
                        step=100,
                        key="n_simulations"
                    )
                    random_seed = st.number_input(
                        "Random Seed",
                        min_value=0,
                        max_value=999999,
                        value=42,
                        key="random_seed"
                    )
                
                with col2:
                    feature_uncertainty = st.slider(
                        "Feature Uncertainty (±%)",
                        min_value=0.0,
                        max_value=30.0,
                        value=5.0,
                        step=0.5,
                        key="feature_uncertainty"
                    )
                    cost_uncertainty = st.slider(
                        "Cost Uncertainty (±%)",
                        min_value=0.0,
                        max_value=20.0,
                        value=1.0,
                        step=0.1,
                        key="cost_uncertainty"
                    )
                
                with col3:
                    normalize_wbs = st.checkbox(
                        "Normalize WBS to 100% each simulation",
                        value=False,
                        key="normalize_wbs"
                    )
                    budget = st.number_input(
                        "Budget Threshold",
                        min_value=0.0,
                        value=float(sum(comp["predictions"]["grand_total"] for comp in components)),
                        step=1000.0,
                        key="mc_budget"
                    )
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.divider()
        
        # Section 2: Scenario Buckets
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 2️⃣ Scenario Buckets")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                low_cutoff = st.slider(
                    "Low < baseline by (%)",
                    0, 50, 10, 1,
                    key="low_cutoff"
                )
            with col2:
                base_band = st.slider(
                    "Base band ± (%)",
                    1, 50, 10, 1,
                    key="base_band"
                )
            with col3:
                high_cutoff = st.slider(
                    "High > baseline by (%)",
                    0, 50, 10, 1,
                    key="high_cutoff"
                )
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.divider()
        
        # Section 3: Run Simulation
        if st.button("🎲 Run Monte Carlo Simulation", type="primary", use_container_width=True):
            try:
                with st.spinner("Running Monte Carlo simulation..."):
                    progress_bar = st.progress(0)
                    
                    # Initialize arrays for results
                    n = int(n_simulations)
                    all_simulations = []
                    component_simulations = {}
                    
                    # Simulate each component
                    for comp_idx, component in enumerate(components):
                        comp_name = component["type"]
                        
                        # Get model for this component
                        dataset_name = component["dataset"]
                        df_comp = st.session_state.datasets.get(dataset_name)
                        
                        if df_comp is None:
                            continue
                        
                        target_col = get_last_column_target(df_comp)
                        model_key = f"{dataset_name}_RandomForest"
                        
                        if model_key not in st.session_state.model_cache:
                            pipe, _, _, _, _ = train_best_model_cached(
                                df_comp, target_col, 0.2, 42, dataset_name
                            )
                            st.session_state.model_cache[model_key] = pipe
                        
                        model_pipe = st.session_state.model_cache[model_key]
                        
                        # Get feature columns
                        X_comp, _ = numeric_features_from_df(df_comp, target_col)
                        feature_cols = X_comp.columns.tolist()
                        
                        # Base inputs
                        base_inputs = component["inputs"]
                        
                        # Run component-level Monte Carlo
                        np.random.seed(random_seed + comp_idx)
                        
                        # Feature uncertainty
                        base_array = np.array([base_inputs.get(f, 0.0) for f in feature_cols])
                        feature_noise = np.random.normal(
                            0,
                            feature_uncertainty / 100.0,
                            size=(n, len(feature_cols))
                        )
                        
                        # Apply noise to non-NaN values
                        mask = ~np.isnan(base_array)
                        if mask.any():
                            feature_matrix = np.tile(base_array, (n, 1))
                            feature_matrix[:, mask] = feature_matrix[:, mask] * (1 + feature_noise[:, mask])
                        else:
                            feature_matrix = np.tile(base_array, (n, 1))
                        
                        # Make predictions
                        input_df = pd.DataFrame(feature_matrix, columns=feature_cols)
                        base_predictions = model_pipe.predict(input_df).astype(float)
                        
                        # Cost uncertainty
                        preds = component["predictions"]
                        eprr = {
                            "Engineering": preds.get("eng_pct", 12.0),
                            "Procurement": preds.get("proc_pct", 33.0),
                            "Fabrication": preds.get("fab_pct", 33.0),
                            "T&I": preds.get("ti_pct", 22.0)
                        }
                        
                        # Simulate cost percentages with uncertainty
                        cost_noise = np.random.normal(0, cost_uncertainty / 100.0, size=n)
                        
                        sst_pct_sim = np.clip(preds.get("sst_pct", 0.0) * (1 + cost_noise), 0, 100)
                        owner_pct_sim = np.clip(preds.get("owner_pct", 0.0) * (1 + cost_noise), 0, 100)
                        cont_pct_sim = np.clip(preds.get("cont_pct", 0.0) * (1 + cost_noise), 0, 100)
                        esc_pct_sim = np.clip(preds.get("esc_pct", 0.0) * (1 + cost_noise), 0, 100)
                        
                        # Calculate costs for each simulation
                        owner_cost = base_predictions * (owner_pct_sim / 100.0)
                        sst_cost = base_predictions * (sst_pct_sim / 100.0)
                        contingency = (base_predictions + owner_cost) * (cont_pct_sim / 100.0)
                        escalation = (base_predictions + owner_cost) * (esc_pct_sim / 100.0)
                        
                        grand_total = base_predictions + owner_cost + sst_cost + contingency + escalation
                        
                        # Store component simulations
                        component_simulations[comp_name] = {
                            "base": base_predictions,
                            "owner": owner_cost,
                            "sst": sst_cost,
                            "contingency": contingency,
                            "escalation": escalation,
                            "total": grand_total
                        }
                        
                        all_simulations.append(grand_total)
                        
                        progress_bar.progress((comp_idx + 1) / len(components))
                    
                    # Combine component simulations
                    if all_simulations:
                        project_simulations = np.sum(all_simulations, axis=0)
                        
                        # Calculate statistics
                        baseline = float(sum(comp["predictions"]["grand_total"] for comp in components))
                        p50 = np.percentile(project_simulations, 50)
                        p80 = np.percentile(project_simulations, 80)
                        p90 = np.percentile(project_simulations, 90)
                        exceed_prob = np.mean(project_simulations > budget) * 100
                        
                        # Display results
                        st.success("✅ Simulation complete!")
                        
                        # Key metrics
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("P50", f"{currency} {p50:,.2f}")
                        with col2:
                            st.metric("P80", f"{currency} {p80:,.2f}")
                        with col3:
                            st.metric("P90", f"{currency} {p90:,.2f}")
                        with col4:
                            st.metric("P(> Budget)", f"{exceed_prob:.1f}%")
                        
                        # Histogram
                        st.markdown("#### Project Grand Total Distribution")
                        fig = px.histogram(
                            x=project_simulations,
                            nbins=50,
                            title="Monte Carlo Results",
                            labels={"x": "Grand Total", "y": "Frequency"},
                            color_discrete_sequence=[PETRONAS["teal"]]
                        )
                        
                        # Add reference lines
                        fig.add_vline(x=p50, line_dash="dash", line_color=PETRONAS["purple"],
                                     annotation_text="P50", annotation_position="top")
                        fig.add_vline(x=p80, line_dash="dash", line_color=PETRONAS["warning"],
                                     annotation_text="P80", annotation_position="top")
                        fig.add_vline(x=p90, line_dash="dash", line_color=PETRONAS["error"],
                                     annotation_text="P90", annotation_position="top")
                        fig.add_vline(x=budget, line_dash="solid", line_color=PETRONAS["black"],
                                     annotation_text="Budget", annotation_position="bottom")
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # CDF Plot
                        st.markdown("#### Cumulative Distribution Function")
                        sorted_sims = np.sort(project_simulations)
                        cdf = np.arange(1, len(sorted_sims) + 1) / len(sorted_sims)
                        
                        fig_cdf = go.Figure()
                        fig_cdf.add_trace(go.Scatter(
                            x=sorted_sims,
                            y=cdf,
                            mode='lines',
                            name='CDF',
                            line=dict(color=PETRONAS["teal"], width=3)
                        ))
                        
                        fig_cdf.add_trace(go.Scatter(
                            x=sorted_sims,
                            y=1 - cdf,
                            mode='lines',
                            name='Exceedance',
                            line=dict(color=PETRONAS["purple"], width=3, dash='dash')
                        ))
                        
                        fig_cdf.update_layout(
                            title="CDF & Exceedance Probability",
                            xaxis_title="Grand Total",
                            yaxis_title="Probability",
                            yaxis_tickformat=".0%",
                            height=500
                        )
                        
                        st.plotly_chart(fig_cdf, use_container_width=True)
                        
                        # Component contribution
                        st.markdown("#### Component Contribution to Variance")
                        component_variances = []
                        for comp_name, sims in component_simulations.items():
                            var_share = np.var(sims["total"]) / np.var(project_simulations) * 100
                            component_variances.append({
                                "Component": comp_name,
                                "Variance Share": var_share,
                                "Mean Cost": np.mean(sims["total"])
                            })
                        
                        var_df = pd.DataFrame(component_variances)
                        var_df = var_df.sort_values("Variance Share", ascending=True)
                        
                        fig_var = px.bar(
                            var_df,
                            x="Variance Share",
                            y="Component",
                            orientation='h',
                            title="Variance Contribution by Component",
                            color="Mean Cost",
                            color_continuous_scale="Viridis"
                        )
                        fig_var.update_layout(height=400)
                        st.plotly_chart(fig_var, use_container_width=True)
                        
                        # Export results
                        st.markdown("#### Export Results")
                        
                        # Create results DataFrame
                        results_df = pd.DataFrame({
                            "simulation": range(1, n + 1),
                            "project_total": project_simulations
                        })
                        
                        for comp_name, sims in component_simulations.items():
                            results_df[f"{comp_name}_total"] = sims["total"]
                        
                        # Download buttons
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            csv = results_df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download CSV",
                                data=csv,
                                file_name=f"monte_carlo_{mc_project}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                        
                        with col2:
                            excel_buffer = io.BytesIO()
                            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                                results_df.to_excel(writer, sheet_name='Simulations', index=False)
                                
                                # Summary sheet
                                summary_data = {
                                    "Statistic": ["Baseline", "P50", "P80", "P90", "Budget", "Exceedance Probability"],
                                    "Value": [baseline, p50, p80, p90, budget, exceed_prob]
                                }
                                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
                                
                                # Variance sheet
                                var_df.to_excel(writer, sheet_name='Variance Analysis', index=False)
                            
                            excel_buffer.seek(0)
                            
                            st.download_button(
                                label="📥 Download Excel Report",
                                data=excel_buffer,
                                file_name=f"monte_carlo_report_{mc_project}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
            
            except Exception as e:
                st.error(f"Simulation failed: {str(e)}")

# =======================================================================================
# COMPARE PROJECTS TAB - ENHANCED
# =======================================================================================
with tab_compare:
    st.markdown('<h2 style="color:#000;">🔀 Compare Projects</h2>', unsafe_allow_html=True)
    
    if len(st.session_state.projects) < 2:
        st.info("Need at least 2 projects to compare. Create projects in the Project Builder.")
    else:
        # Project selection
        selected_projects = st.multiselect(
            "Select projects to compare",
            list(st.session_state.projects.keys()),
            default=list(st.session_state.projects.keys())[:2],
            key="compare_projects"
        )
        
        if len(selected_projects) >= 2:
            # Collect project data
            comparison_data = []
            
            for proj_name in selected_projects:
                project = st.session_state.projects[proj_name]
                components = project.get("components", [])
                
                if components:
                    totals = {
                        "base_capex": 0.0,
                        "owners_cost": 0.0,
                        "sst_cost": 0.0,
                        "contingency": 0.0,
                        "escalation": 0.0,
                        "grand_total": 0.0
                    }
                    
                    for comp in components:
                        preds = comp["predictions"]
                        totals["base_capex"] += preds["base_pred"]
                        totals["owners_cost"] += preds["owners_cost"]
                        totals["sst_cost"] += preds["sst_cost"]
                        totals["contingency"] += preds["contingency_cost"]
                        totals["escalation"] += preds["escalation_cost"]
                        totals["grand_total"] += preds["grand_total"]
                    
                    comparison_data.append({
                        "Project": proj_name,
                        "Components": len(components),
                        **totals
                    })
            
            if comparison_data:
                comp_df = pd.DataFrame(comparison_data)
                currency = project.get("currency", "")
                
                # Display summary table
                st.markdown("### Project Comparison Summary")
                st.dataframe(
                    comp_df.style.format({
                        "base_capex": "{:,.2f}",
                        "owners_cost": "{:,.2f}",
                        "sst_cost": "{:,.2f}",
                        "contingency": "{:,.2f}",
                        "escalation": "{:,.2f}",
                        "grand_total": "{:,.2f}"
                    }),
                    use_container_width=True
                )
                
                # Visualizations
                st.markdown("### Visual Comparison")
                
                tab1, tab2, tab3 = st.tabs(["Total Cost", "Cost Composition", "Component Breakdown"])
                
                with tab1:
                    fig = px.bar(
                        comp_df,
                        x="Project",
                        y="grand_total",
                        title="Grand Total Comparison",
                        color="Project",
                        text="grand_total",
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                
                with tab2:
                    # Prepare data for stacked bar
                    melt_df = comp_df.melt(
                        id_vars=["Project"],
                        value_vars=["base_capex", "owners_cost", "sst_cost", "contingency", "escalation"],
                        var_name="Cost Type",
                        value_name="Amount"
                    )
                    
                    # Format cost type names
                    cost_type_map = {
                        "base_capex": "Base CAPEX",
                        "owners_cost": "Owner's",
                        "sst_cost": "SST",
                        "contingency": "Contingency",
                        "escalation": "Escalation"
                    }
                    melt_df["Cost Type"] = melt_df["Cost Type"].map(cost_type_map)
                    
                    fig = px.bar(
                        melt_df,
                        x="Project",
                        y="Amount",
                        color="Cost Type",
                        title="Cost Composition by Project",
                        barmode="stack",
                        color_discrete_sequence=[
                            PETRONAS["teal"],
                            PETRONAS["purple"],
                            PETRONAS["success"],
                            PETRONAS["warning"],
                            PETRONAS["error"]
                        ]
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                
                with tab3:
                    # Component-level comparison
                    component_data = []
                    for proj_name in selected_projects:
                        project = st.session_state.projects[proj_name]
                        for comp in project.get("components", []):
                            component_data.append({
                                "Project": proj_name,
                                "Component": comp["type"],
                                "Grand Total": comp["predictions"]["grand_total"]
                            })
                    
                    if component_data:
                        comp_comp_df = pd.DataFrame(component_data)
                        
                        fig = px.bar(
                            comp_comp_df,
                            x="Component",
                            y="Grand Total",
                            color="Project",
                            barmode="group",
                            title="Component-level Comparison",
                            color_discrete_sequence=px.colors.qualitative.Set3
                        )
                        fig.update_layout(height=500, xaxis_tickangle=45)
                        st.plotly_chart(fig, use_container_width=True)
                
                # Export comparison
                st.markdown("### Export Comparison")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Excel export
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        comp_df.to_excel(writer, sheet_name='Summary', index=False)
                        
                        # Detailed component data
                        all_components = []
                        for proj_name in selected_projects:
                            project = st.session_state.projects[proj_name]
                            for comp in project.get("components", []):
                                all_components.append({
                                    "Project": proj_name,
                                    "Component": comp["type"],
                                    "Base CAPEX": comp["predictions"]["base_pred"],
                                    "Owner's Cost": comp["predictions"]["owners_cost"],
                                    "SST": comp["predictions"]["sst_cost"],
                                    "Contingency": comp["predictions"]["contingency_cost"],
                                    "Escalation": comp["predictions"]["escalation_cost"],
                                    "Grand Total": comp["predictions"]["grand_total"]
                                })
                        
                        if all_components:
                            pd.DataFrame(all_components).to_excel(writer, sheet_name='Components', index=False)
                    
                    excel_buffer.seek(0)
                    
                    st.download_button(
                        label="📥 Download Excel Report",
                        data=excel_buffer,
                        file_name="project_comparison.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                with col2:
                    # PDF/PPT export placeholder
                    st.info("PowerPoint export coming soon!")

# ---------------------------------------------------------------------------------------
# SIDEBAR INFORMATION
# ---------------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <h3 style='color: white; margin-bottom: 0.5rem;'>💠 CAPEX AI RT2026</h3>
        <p style='color: rgba(255,255,255,0.8); font-size: 0.9rem;'>
        Data-driven CAPEX prediction and analysis
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Quick stats
    st.markdown("### 📊 Quick Stats")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Datasets", len(st.session_state.datasets))
    with col2:
        st.metric("Projects", len(st.session_state.projects))
    
    if st.session_state._last_metrics:
        st.divider()
        st.markdown("### 🎯 Last Training")
        st.metric("Best Model", st.session_state._last_metrics.get("best_model", "N/A"))
        st.metric("R² Score", f"{st.session_state._last_metrics.get('r2', 0):.3f}")
    
    st.divider()
    
    # Help section
    with st.expander("ℹ️ Need Help?"):
        st.markdown("""
        **Quick Guide:**
        1. **Data Tab**: Upload data and train models
        2. **Project Builder**: Create multi-component projects
        3. **Monte Carlo**: Run uncertainty simulations
        4. **Compare**: Compare multiple projects
        
        **Tips:**
        - Target column is always the last column
        - Models are cached for faster predictions
        - Export results for reporting
        """)
    
    # Clear cache button
    if st.button("🧹 Clear Cache", use_container_width=True):
        keys_to_clear = ["datasets", "predictions", "processed_excel_files", "_last_metrics", "model_cache"]
        for key in keys_to_clear:
            if key in st.session_state:
                st.session_state[key] = {} if key != "processed_excel_files" else set()
        
        st.session_state.uploader_nonce += 1
        st.session_state.widget_nonce += 1
        
        show_toast("Cache cleared successfully", "🧹")
        st.rerun()

# ---------------------------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------------------------
st.divider()
st.markdown(
    f"""
    <div style='text-align: center; color: {PETRONAS["gray_700"]}; font-size: 0.9rem; padding: 1rem;'>
        <p>CAPEX AI RT2026 • PETRONAS • Version 2.0 Improved</p>
        <p style='font-size: 0.8rem; opacity: 0.7;'>For internal use only</p>
    </div>
    """,
    unsafe_allow_html=True
)
