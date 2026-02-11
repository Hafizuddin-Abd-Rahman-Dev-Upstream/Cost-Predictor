# ======================================================================================
# CAPEX AI RT2026 
#
# requirements.txt:
# streamlit
# pandas
# numpy
# scipy
# scikit-learn
# plotly
# matplotlib
# python-pptx
# openpyxl
# requests
# ======================================================================================

import io
import json
import zipfile
import re
import requests
import numpy as np
import pandas as pd
import streamlit as st

# --- Guard: scikit-learn missing (prevents hard crash on Streamlit Cloud) ---
try:
    from sklearn.impute import KNNImputer, SimpleImputer
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import MinMaxScaler, StandardScaler
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import Ridge, Lasso
    from sklearn.svm import SVR
    from sklearn.tree import DecisionTreeRegressor
    from sklearn.pipeline import Pipeline
    from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
    from sklearn.compose import ColumnTransformer
    from sklearn.feature_selection import SelectKBest, f_regression
except Exception as e:
    st.error(
        "❌ Missing dependency: **scikit-learn**.\n\n"
        "Fix:\n"
        "1) Open your **requirements.txt**\n"
        "2) Add this line: `scikit-learn`\n"
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
# PAGE CONFIG
# ---------------------------------------------------------------------------------------
st.set_page_config(
    page_title="CAPEX AI RT2026",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------------------
# THEME TOKENS
# ---------------------------------------------------------------------------------------
PETRONAS = {
    "teal": "#00A19B",
    "teal_dark": "#008C87",
    "purple": "#6C4DD3",
    "white": "#FFFFFF",
    "black": "#0E1116",
    "border": "rgba(0,0,0,0.10)",
}

# ---------------------------------------------------------------------------------------
# SHAREPOINT LINKS (FILL THESE LATER)
# ---------------------------------------------------------------------------------------
SHAREPOINT_LINKS = {
    "Shallow Water": "https://petronas.sharepoint.com/sites/your-site/shallow-water",
    "Deep Water": "https://petronas.sharepoint.com/sites/your-site/deep-water",
    "Onshore": "https://petronas.sharepoint.com/sites/your-site/onshore",
    "Uncon": "https://petronas.sharepoint.com/sites/your-site/uncon",
    "CCS": "https://petronas.sharepoint.com/sites/your-site/ccs",
}

# ---------------------------------------------------------------------------------------
# GLOBAL CSS
# ---------------------------------------------------------------------------------------
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body {{ font-family: 'Inter', sans-serif; }}
[data-testid="stAppViewContainer"] {{
  background: {PETRONAS["white"]};
  color: {PETRONAS["black"]};
  padding-top: 0.5rem;
}}
#MainMenu, footer {{ visibility: hidden; }}
[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, {PETRONAS["teal"]} 0%, {PETRONAS["teal_dark"]} 100%) !important;
  color: #fff !important;
  border-top-right-radius: 16px;
  border-bottom-right-radius: 16px;
  box-shadow: 0 6px 20px rgba(0,0,0,0.15);
}}
[data-testid="stSidebar"] * {{ color: #fff !important; }}
[data-testid="collapsedControl"] {{
  position: fixed !important;
  top: 50% !important;
  left: 10px !important;
  transform: translateY(-50%) !important;
  z-index: 9999 !important;
}}
.petronas-hero {{
  border-radius: 20px;
  padding: 28px 32px;
  margin: 6px 0 18px 0;
  color: #fff;
  background: linear-gradient(135deg, {PETRONAS["teal"]}, {PETRONAS["purple"]}, {PETRONAS["black"]});
  background-size: 200% 200%;
  animation: heroGradient 8s ease-in-out infinite, fadeIn .8s ease-in-out, heroPulse 5s ease-in-out infinite;
  box-shadow: 0 10px 24px rgba(0,0,0,.12);
}}
@keyframes heroGradient {{
  0% {{ background-position: 0% 50%; }}
  50% {{ background-position: 100% 50%; }}
  100% {{ background-position: 0% 50%; }}
}}
@keyframes fadeIn {{
  from {{ opacity: 0; transform: translateY(10px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes heroPulse {{
  0%   {{ box-shadow: 0 0 16px rgba(0,161,155,0.45); }}
  25%  {{ box-shadow: 0 0 26px rgba(108,77,211,0.55); }}
  50%  {{ box-shadow: 0 0 36px rgba(0,161,155,0.55); }}
  75%  {{ box-shadow: 0 0 26px rgba(108,77,211,0.55); }}
  100% {{ box-shadow: 0 0 16px rgba(0,161,155,0.45); }}
}}
.petronas-hero h1 {{ margin: 0 0 5px; font-weight: 800; letter-spacing: 0.3px; }}
.petronas-hero p {{ margin: 0; opacity: .9; font-weight: 500; }}

.stButton > button, .stDownloadButton > button, .petronas-button {{
  border-radius: 10px;
  padding: .6rem 1.1rem;
  font-weight: 600;
  color: #fff !important;
  border: none;
  background: linear-gradient(to right, {PETRONAS["teal"]}, {PETRONAS["purple"]});
  background-size: 200% auto;
  transition: background-position .85s ease, transform .2s ease, box-shadow .25s ease;
  text-decoration: none;
  display: inline-block;
}}
.stButton > button:hover, .stDownloadButton > button:hover, .petronas-button:hover {{
  background-position: right center;
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(0,0,0,0.18);
}}

.stTabs [role="tablist"] {{
  display: flex;
  gap: 8px;
  border-bottom: none;
  padding-bottom: 6px;
}}
.stTabs [role="tab"] {{
  background: #fff;
  color: {PETRONAS["black"]};
  border-radius: 8px;
  padding: 10px 18px;
  border: 1px solid {PETRONAS["border"]};
  font-weight: 600;
  transition: all .3s ease;
  position: relative;
}}
.stTabs [role="tab"]:hover {{
  background: linear-gradient(to right, {PETRONAS["teal"]}, {PETRONAS["purple"]});
  color: #fff;
}}
.stTabs [role="tab"][aria-selected="true"] {{
  background: linear-gradient(to right, {PETRONAS["teal"]}, {PETRONAS["purple"]});
  color: #fff;
  border-color: transparent;
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
}}
.stTabs [role="tab"][aria-selected="true"]::after {{
  content: "";
  position: absolute;
  left: 10%;
  bottom: -3px;
  width: 80%;
  height: 3px;
  background: linear-gradient(90deg, {PETRONAS["teal"]}, {PETRONAS["purple"]}, {PETRONAS["teal"]});
  background-size: 200% 100%;
  border-radius: 2px;
  animation: glowSlide 2.5s linear infinite;
}}
@keyframes glowSlide {{
  0% {{ background-position: 0% 50%; }}
  50% {{ background-position: 100% 50%; }}
  100% {{ background-position: 0% 50%; }}
}}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------------------
# HERO HEADER
# ---------------------------------------------------------------------------------------
st.markdown(
    """
<div class="petronas-hero">
  <h1>CAPEX AI RT2026</h1>
  <p>Data-driven CAPEX prediction</p>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

APPROVED_EMAILS = [str(e).strip().lower() for e in st.secrets.get("emails", [])]
correct_password = st.secrets.get("password", None)

if not st.session_state.authenticated:
    with st.form("login_form"):
        st.markdown("#### 🔐 Access Required", unsafe_allow_html=True)
        email = (st.text_input("Email Address", key="login_email") or "").strip().lower()
        password = st.text_input("Access Password", type="password", key="login_pwd")
        submitted = st.form_submit_button("Login")

        if submitted:
            ok = (email in APPROVED_EMAILS) and (password == correct_password)
            if ok:
                st.session_state.authenticated = True
                st.success("✅ Access granted.")
                st.rerun()
            else:
                st.error("❌ Invalid credentials.")
    st.stop()

# ---------------------------------------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------------------------------------
if "datasets" not in st.session_state:
    st.session_state.datasets = {}
if "predictions" not in st.session_state:
    st.session_state.predictions = {}
if "processed_excel_files" not in st.session_state:
    st.session_state.processed_excel_files = set()
if "_last_metrics" not in st.session_state:
    st.session_state._last_metrics = None
if "projects" not in st.session_state:
    st.session_state.projects = {}
if "component_labels" not in st.session_state:
    st.session_state.component_labels = {}
if "uploader_nonce" not in st.session_state:
    st.session_state.uploader_nonce = 0
if "widget_nonce" not in st.session_state:
    st.session_state.widget_nonce = 0

# ---------------------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------------------
def toast(msg, icon="✅"):
    try:
        st.toast(f"{icon} {msg}")
    except Exception:
        st.success(msg if icon == "✅" else msg)


def format_with_commas(num):
    try:
        return f"{float(num):,.2f}"
    except Exception:
        return str(num)


def normalize_to_100(d: dict):
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


def is_junk_col(colname: str) -> bool:
    h = str(colname).strip().upper()
    return (not h) or h.startswith("UNNAMED") or h in {"INDEX", "IDX"}


def currency_from_header(header: str) -> str:
    h = (header or "").strip().upper()
    if "€" in h:
        return "€"
    if "£" in h:
        return "£"
    if "$" in h:
        return "$"
    if re.search(r"\bUSD\b", h):
        return "USD"
    if re.search(r"\b(MYR|RM)\b", h):
        return "RM"
    return ""


def get_currency_symbol(df: pd.DataFrame, target_col: str | None = None) -> str:
    if df is None or df.empty:
        return ""
    if target_col and target_col in df.columns:
        return currency_from_header(str(target_col))
    for c in reversed(df.columns):
        if not is_junk_col(c):
            return currency_from_header(str(c))
    return ""


def cost_breakdown(
    base_pred: float,
    sst_pct: float,
    owners_pct: float,
    cont_pct: float,
    esc_pct: float,
):
    base_pred = float(base_pred)

    owners_cost = round(base_pred * (owners_pct / 100.0), 2)
    sst_cost = round(base_pred * (sst_pct / 100.0), 2)

    contingency_cost = round((base_pred + owners_cost) * (cont_pct / 100.0), 2)
    escalation_cost = round((base_pred + owners_cost) * (esc_pct / 100.0), 2)

    grand_total = round(base_pred + owners_cost + sst_cost + contingency_cost + escalation_cost, 2)
    return owners_cost, sst_cost, contingency_cost, escalation_cost, grand_total


def project_components_df(proj):
    comps = proj.get("components", [])
    rows = []
    for c in comps:
        rows.append(
            {
                "Component": c["component_type"],
                "Dataset": c["dataset"],
                "Model": c.get("model_used", ""),
                "Base CAPEX": float(c["prediction"]),
                "Owner's Cost": float(c["breakdown"]["owners_cost"]),
                "Contingency": float(c["breakdown"]["contingency_cost"]),
                "Escalation": float(c["breakdown"]["escalation_cost"]),
                "SST": float(c["breakdown"]["sst_cost"]),
                "Grand Total": float(c["breakdown"]["grand_total"]),
            }
        )
    return pd.DataFrame(rows)


def project_totals(proj):
    dfc = project_components_df(proj)
    if dfc.empty:
        return {"capex_sum": 0.0, "owners": 0.0, "cont": 0.0, "esc": 0.0, "sst": 0.0, "grand_total": 0.0}
    return {
        "capex_sum": float(dfc["Base CAPEX"].sum()),
        "owners": float(dfc["Owner's Cost"].sum()),
        "cont": float(dfc["Contingency"].sum()),
        "esc": float(dfc["Escalation"].sum()),
        "sst": float(dfc["SST"].sum()),
        "grand_total": float(dfc["Grand Total"].sum()),
    }


# ======================================================================================
# IMPROVED DATA PIPELINE
# ======================================================================================
class DataPreprocessor:
    """Improved data preprocessing pipeline"""
    
    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Clean dataframe: remove junk columns, handle missing values"""
        # Remove junk columns
        df = df.copy()
        cols_to_drop = [col for col in df.columns if is_junk_col(col)]
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)
        
        return df
    
    @staticmethod
    def extract_features_target(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, str]:
        """Extract features and target (last column is always target)"""
        if df is None or df.empty:
            raise ValueError("Empty dataset")
        
        # Target is always last column
        target_col = df.columns[-1]
        
        # Features are all columns except target
        feature_cols = [col for col in df.columns if col != target_col]
        
        if not feature_cols:
            raise ValueError("No feature columns found (need at least 1 feature)")
        
        # Extract features and target
        X = df[feature_cols].copy()
        y = df[target_col].copy()
        
        # Convert target to numeric
        try:
            y = pd.to_numeric(y, errors='coerce')
        except:
            raise ValueError(f"Target column '{target_col}' cannot be converted to numeric")
        
        # Check if target has enough valid values
        if y.isna().sum() / len(y) > 0.8:  # More than 80% missing
            raise ValueError(f"Target column '{target_col}' has too many missing values")
        
        return X, y, target_col
    
    @staticmethod
    def validate_feature_columns(X: pd.DataFrame, required_cols: list = None) -> pd.DataFrame:
        """Validate and prepare feature columns"""
        X = X.copy()
        
        # Convert numeric columns
        numeric_cols = X.select_dtypes(include=[np.number]).columns
        non_numeric_cols = [col for col in X.columns if col not in numeric_cols]
        
        if non_numeric_cols:
            st.warning(f"Non-numeric columns will be converted: {non_numeric_cols}")
            for col in non_numeric_cols:
                try:
                    X[col] = pd.to_numeric(X[col], errors='coerce')
                except:
                    X[col] = np.nan
        
        # Check for required columns (for batch prediction)
        if required_cols:
            missing = [col for col in required_cols if col not in X.columns]
            if missing:
                raise ValueError(f"Missing required columns: {missing}")
        
        return X


# ======================================================================================
# IMPROVED MODEL PIPELINE
# ======================================================================================
class ModelPipeline:
    """Improved model training and prediction pipeline"""
    
    MODEL_CANDIDATES = {
        "RandomForest": lambda rs=42: RandomForestRegressor(
            n_estimators=100, 
            max_depth=None,
            min_samples_split=2,
            min_samples_leaf=1,
            random_state=rs
        ),
        "GradientBoosting": lambda rs=42: GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=3,
            random_state=rs
        ),
        "Ridge": lambda rs=42: Ridge(alpha=1.0),
        "Lasso": lambda rs=42: Lasso(alpha=1.0),
        "DecisionTree": lambda rs=42: DecisionTreeRegressor(random_state=rs),
        "SVR": lambda rs=42: SVR(kernel='rbf', C=1.0, epsilon=0.1),
    }
    
    SCALE_MODELS = {"Ridge", "Lasso", "SVR"}
    
    @classmethod
    def create_pipeline(cls, model_name: str, random_state=42) -> Pipeline:
        """Create a robust ML pipeline"""
        if model_name not in cls.MODEL_CANDIDATES:
            model_name = "RandomForest"
        
        # Get model constructor
        ctor = cls.MODEL_CANDIDATES[model_name]
        try:
            model = ctor(random_state)
        except TypeError:
            model = ctor()
        
        # Build pipeline steps
        steps = []
        
        # Imputation
        steps.append(("imputer", SimpleImputer(strategy="median")))
        
        # Feature selection for high-dimensional data
        steps.append(("feature_selector", SelectKBest(score_func=f_regression, k='all')))
        
        # Scaling for models that need it
        if model_name in cls.SCALE_MODELS:
            steps.append(("scaler", StandardScaler()))
        
        # Add model
        steps.append(("model", model))
        
        return Pipeline(steps)
    
    @classmethod
    @st.cache_resource(show_spinner=False)
    def train_model_cached(_cls, X: pd.DataFrame, y: pd.Series, model_name: str = None, 
                          test_size: float = 0.2, random_state: int = 42) -> tuple:
        """Train and cache model with improved validation"""
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        # If model not specified, try all and pick best
        if model_name is None:
            best_model = None
            best_score = -np.inf
            best_metrics = {}
            
            for name in _cls.MODEL_CANDIDATES.keys():
                try:
                    pipeline = _cls.create_pipeline(name, random_state)
                    pipeline.fit(X_train, y_train)
                    
                    # Predict and evaluate
                    y_pred = pipeline.predict(X_test)
                    r2 = r2_score(y_test, y_pred)
                    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                    mae = mean_absolute_error(y_test, y_pred)
                    
                    if r2 > best_score:
                        best_score = r2
                        best_model = name
                        best_metrics = {
                            "model": name,
                            "r2": r2,
                            "rmse": rmse,
                            "mae": mae,
                            "pipeline": pipeline,
                            "feature_cols": list(X.columns)
                        }
                except Exception as e:
                    st.warning(f"Model {name} failed: {str(e)[:100]}")
            
            if best_model is None:
                best_model = "RandomForest"
                pipeline = _cls.create_pipeline(best_model, random_state)
                pipeline.fit(X_train, y_train)
                best_metrics = {
                    "model": best_model,
                    "r2": 0,
                    "rmse": 0,
                    "mae": 0,
                    "pipeline": pipeline,
                    "feature_cols": list(X.columns)
                }
        else:
            # Use specified model
            pipeline = _cls.create_pipeline(model_name, random_state)
            pipeline.fit(X_train, y_train)
            
            y_pred = pipeline.predict(X_test)
            best_metrics = {
                "model": model_name,
                "r2": r2_score(y_test, y_pred),
                "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
                "mae": mean_absolute_error(y_test, y_pred),
                "pipeline": pipeline,
                "feature_cols": list(X.columns)
            }
        
        return best_metrics
    
    @staticmethod
    def prepare_prediction_input(feature_cols: list, payload: dict) -> pd.DataFrame:
        """Prepare input data for prediction"""
        row = {}
        for col in feature_cols:
            val = payload.get(col, np.nan)
            # Handle different input types
            if val is None or (isinstance(val, str) and val.strip() == ""):
                row[col] = np.nan
            elif isinstance(val, (int, float, np.number)):
                row[col] = float(val)
            else:
                try:
                    row[col] = float(val)
                except:
                    row[col] = np.nan
        
        return pd.DataFrame([row], columns=feature_cols)


# ======================================================================================
# MONTE CARLO HELPERS (Simplified)
# ======================================================================================
def monte_carlo_simulation(
    model_pipeline: Pipeline,
    feature_cols: list,
    base_values: dict,
    n_simulations: int = 1000,
    feature_uncertainty: float = 0.05,
    cost_uncertainty: dict = None
) -> pd.DataFrame:
    """Simplified Monte Carlo simulation"""
    np.random.seed(42)
    
    # Prepare base values
    base_array = np.array([float(base_values.get(col, np.nan)) for col in feature_cols])
    
    # Generate simulations
    simulations = []
    for _ in range(n_simulations):
        # Add noise to features
        noise = np.random.normal(0, feature_uncertainty, len(base_array))
        sim_features = base_array * (1 + noise)
        
        # Prepare dataframe for prediction
        sim_df = pd.DataFrame([sim_features], columns=feature_cols)
        
        # Predict
        try:
            base_pred = float(model_pipeline.predict(sim_df)[0])
        except:
            base_pred = 0
        
        simulations.append(base_pred)
    
    return pd.DataFrame({"prediction": simulations})


# ---------------------------------------------------------------------------------------
# DATA / MODEL HELPERS
# ---------------------------------------------------------------------------------------
GITHUB_USER = "Hafizuddin-Abd-Rahman-Dev-Upstream"
REPO_NAME = "Cost-Predictor"
BRANCH = "main"
DATA_FOLDER = "pages/data_CAPEX"


@st.cache_data(ttl=600, show_spinner=False)
def fetch_json(url: str):
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=600, show_spinner=False)
def list_csvs_from_manifest(folder_path: str):
    manifest_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{folder_path}/files.json"
    try:
        data = fetch_json(manifest_url)
        if isinstance(data, list):
            return [str(x) for x in data]
        return []
    except Exception as e:
        st.error(f"Failed to load CSV manifest: {e}")
        return []


# ---------------------------------------------------------------------------------------
# NAV ROW — SHAREPOINT BUTTONS
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
# TOP-LEVEL TABS
# ---------------------------------------------------------------------------------------
tab_data, tab_pb, tab_mc, tab_compare = st.tabs(
    ["📊 Data", "🏗️ Project Builder", "🎲 Monte Carlo", "🔀 Compare Projects"]
)

# =======================================================================================
# DATA TAB - IMPROVED
# =======================================================================================
with tab_data:
    st.markdown('<h3 style="margin-top:0;color:#000;">📁 Data</h3>', unsafe_allow_html=True)

    st.markdown('<h4 style="margin:0;color:#000;">Data Sources</h4><p></p>', unsafe_allow_html=True)
    c1, c2 = st.columns([1.2, 1])
    with c1:
        data_source = st.radio("Choose data source", ["Upload CSV", "Load from Server"], horizontal=True, key="data_source")

    with c2:
        st.caption("Enterprise Storage (SharePoint)")
        data_link = (
            "https://petronas.sharepoint.com/sites/ecm_ups_coe/confidential/"
            "DFE%20Cost%20Engineering/Forms/AllItems.aspx?"
            "id=%2Fsites%2Fecm%5Fups%5Fcoe%2Fconfidential%2FDFE%20Cost%20Engineering"
            "%2F2%2ETemplate%20Tools%2FCost%20Predictor%2FDatabase%2FCAPEX%20%2D%20RT%20Q1%202025"
        )
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
            key=f"csv_uploader_{st.session_state.uploader_nonce}",
        )
    else:
        github_csvs = list_csvs_from_manifest(DATA_FOLDER)
        if github_csvs:
            selected_file = st.selectbox("Choose CSV from GitHub", github_csvs, key="github_csv_select")
            if st.button("Load selected CSV", key="load_github_csv_btn"):
                raw_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{DATA_FOLDER}/{selected_file}"
                try:
                    df = pd.read_csv(raw_url)
                    # Clean and store
                    df_clean = DataPreprocessor.clean_dataframe(df)
                    st.session_state.datasets[selected_file] = df_clean
                    st.session_state.predictions.setdefault(selected_file, [])
                    toast(f"Loaded from GitHub: {selected_file}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error loading CSV: {e}")
        else:
            st.info("No CSV files found in GitHub folder.")

    if uploaded_files:
        for up in uploaded_files:
            if up.name not in st.session_state.datasets:
                try:
                    df = pd.read_csv(up)
                    # Clean and store
                    df_clean = DataPreprocessor.clean_dataframe(df)
                    st.session_state.datasets[up.name] = df_clean
                    st.session_state.predictions.setdefault(up.name, [])
                except Exception as e:
                    st.error(f"Failed to read {up.name}: {e}")
        toast("Dataset(s) added.")

    st.divider()

    # Control buttons
    cA, cB, cC, cD = st.columns([1, 1, 1, 2])
    with cA:
        if st.button("🧹 Clear predictions", key="clear_preds_btn"):
            st.session_state.predictions = {k: [] for k in st.session_state.predictions.keys()}
            toast("Predictions cleared.", "🧹")
            st.rerun()
    with cB:
        if st.button("🧺 Clear history", key="clear_processed_btn"):
            st.session_state.processed_excel_files = set()
            toast("History cleared.", "🧺")
            st.rerun()
    with cC:
        if st.button("🔁 Refresh", key="refresh_manifest_btn"):
            list_csvs_from_manifest.clear()
            fetch_json.clear()
            toast("Refreshed.", "🔁")
            st.rerun()
    with cD:
        if st.button("🗂️ Clear all data", key="clear_datasets_btn"):
            st.session_state.datasets = {}
            st.session_state.predictions = {}
            st.session_state.processed_excel_files = set()
            st.session_state._last_metrics = None
            st.session_state.uploader_nonce += 1
            st.session_state.widget_nonce += 1
            toast("All data cleared.", "🗂️")
            st.rerun()

    st.divider()

    # Dataset selection
    if st.session_state.datasets:
        ds_name_data = st.selectbox("Active dataset", list(st.session_state.datasets.keys()), key="active_dataset_data")
        df_active = st.session_state.datasets[ds_name_data]
        
        # Get target column (always last column)
        target_col_active = df_active.columns[-1]
        currency_active = get_currency_symbol(df_active, target_col_active)
        
        colA, colB, colC, colD2 = st.columns([1, 1, 1, 2])
        with colA:
            st.metric("Rows", f"{df_active.shape[0]:,}")
        with colB:
            st.metric("Columns", f"{df_active.shape[1]:,}")
        with colC:
            st.metric("Currency", f"{currency_active or '—'}")
        with colD2:
            st.caption(f"Target column: **{target_col_active}**")
        
        with st.expander("Preview (first 10 rows)", expanded=False):
            st.dataframe(df_active.head(10), use_container_width=True)
    else:
        st.info("Upload or load a dataset to proceed.")
        st.stop()

    # ========================= IMPROVED MODEL TRAINING =========================
    st.divider()
    st.markdown('<h3 style="margin-top:0;color:#000;">⚙️ Model Training</h3>', unsafe_allow_html=True)
    
    ds_name_model = st.selectbox("Dataset for training", list(st.session_state.datasets.keys()), key="ds_model")
    df_model = st.session_state.datasets[ds_name_model]
    
    # Extract features and target
    try:
        X, y, target_col = DataPreprocessor.extract_features_target(df_model)
        st.success(f"✅ Data prepared: {X.shape[1]} features, target: {target_col}")
        
        # Display data info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Features", X.shape[1])
        with col2:
            st.metric("Samples", X.shape[0])
        with col3:
            valid_target = y.notna().sum()
            st.metric("Valid targets", f"{valid_target} ({valid_target/len(y)*100:.1f}%)")
        
    except Exception as e:
        st.error(f"Data preparation failed: {e}")
        st.stop()
    
    # Training options
    m1, m2 = st.columns([1, 3])
    with m1:
        test_size = st.slider("Test size", 0.1, 0.5, 0.2, 0.05, key="train_test_size")
        model_choice = st.selectbox("Model", ["Auto-select best", "RandomForest", "GradientBoosting", "Ridge", "Lasso", "DecisionTree", "SVR"], key="model_choice")
        run_train = st.button("Train Model", key="run_training_btn", type="primary")
    
    with m2:
        if model_choice == "Auto-select best":
            st.caption("Will try all models and select the best one based on R² score")
        else:
            st.caption(f"Using {model_choice} model")
    
    if run_train:
        try:
            with st.spinner("Training model..."):
                if model_choice == "Auto-select best":
                    model_name = None
                else:
                    model_name = model_choice
                
                metrics = ModelPipeline.train_model_cached(
                    X, y, 
                    model_name=model_name,
                    test_size=float(test_size),
                    random_state=42
                )
            
            st.session_state._last_metrics = metrics
            st.session_state[f"trained_model__{ds_name_model}"] = metrics
            
            toast("Training complete!")
            
            # Display metrics
            st.markdown("##### Model Performance")
            mcol1, mcol2, mcol3, mcol4 = st.columns(4)
            with mcol1:
                st.metric("Model", metrics["model"])
            with mcol2:
                st.metric("R² Score", f"{metrics['r2']:.3f}")
            with mcol3:
                st.metric("RMSE", f"{metrics['rmse']:,.2f}")
            with mcol4:
                st.metric("MAE", f"{metrics['mae']:,.2f}")
            
            # Store model for predictions
            st.session_state[f"current_pipeline__{ds_name_model}"] = metrics["pipeline"]
            st.session_state[f"feature_cols__{ds_name_model}"] = metrics["feature_cols"]
            
        except Exception as e:
            st.error(f"Training failed: {e}")

    # ========================= VISUALIZATION ==================================
    st.divider()
    st.markdown('<h3 style="margin-top:0;color:#000;">📈 Visualization</h3>', unsafe_allow_html=True)
    
    ds_name_viz = st.selectbox("Dataset for visualization", list(st.session_state.datasets.keys()), key="ds_viz")
    df_viz = st.session_state.datasets[ds_name_viz]
    
    try:
        # Basic correlation matrix
        numeric_df = df_viz.select_dtypes(include=[np.number])
        if len(numeric_df.columns) > 1:
            st.markdown("##### Correlation Matrix")
            corr = numeric_df.corr()
            fig_corr = px.imshow(corr, text_auto=".2f", aspect="auto", 
                               color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
            fig_corr.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("Need at least 2 numeric columns for correlation matrix")
        
        # Feature importance if model is trained
        if f"current_pipeline__{ds_name_viz}" in st.session_state:
            pipeline = st.session_state[f"current_pipeline__{ds_name_viz}"]
            if hasattr(pipeline.named_steps['model'], 'feature_importances_'):
                importances = pipeline.named_steps['model'].feature_importances_
                feature_names = st.session_state[f"feature_cols__{ds_name_viz}"]
                
                fi_df = pd.DataFrame({
                    'feature': feature_names,
                    'importance': importances
                }).sort_values('importance', ascending=True)
                
                st.markdown("##### Feature Importance")
                fig_fi = go.Figure(go.Bar(
                    x=fi_df["importance"], 
                    y=fi_df["feature"], 
                    orientation="h"
                ))
                fig_fi.update_layout(
                    xaxis_title="Importance", 
                    yaxis_title="Feature",
                    margin=dict(l=0, r=0, t=10, b=0)
                )
                st.plotly_chart(fig_fi, use_container_width=True)
        
    except Exception as e:
        st.error(f"Visualization error: {e}")

    # ========================= IMPROVED PREDICTION ============================
    st.divider()
    st.markdown('<h3 style="margin-top:0;color:#000;">🎯 Predict</h3>', unsafe_allow_html=True)
    
    ds_name_pred = st.selectbox("Dataset for prediction", list(st.session_state.datasets.keys()), key="ds_pred")
    df_pred = st.session_state.datasets[ds_name_pred]
    
    # Check if model is trained
    if f"current_pipeline__{ds_name_pred}" not in st.session_state:
        st.warning("⚠️ Please train a model first using the Model Training section above")
        st.stop()
    
    pipeline = st.session_state[f"current_pipeline__{ds_name_pred}"]
    feature_cols = st.session_state[f"feature_cols__{ds_name_pred}"]
    target_col = df_pred.columns[-1]
    currency_pred = get_currency_symbol(df_pred, target_col)
    
    # SIMPLIFIED: Remove WBS Level 1 inputs, keep only SST and other cost factors
    st.markdown('<h4 style="margin:0;color:#000;">Cost Factors</h4><p>Adjust cost percentages</p>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Cost Factors (use +/-)**")
        sst_pct = st.number_input("SST (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.5, key="pred_sst")
        owners_pct = st.number_input("Owner's Cost (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.5, key="pred_owner")
    with c2:
        st.markdown("**Contingency & Escalation**")
        cont_pct = st.number_input("Contingency (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.5, key="pred_cont")
        esc_pct = st.number_input("Escalation & Inflation (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.5, key="pred_esc")
    
    # Project input
    st.markdown('<h4 style="margin:0;color:#000;">Project Details</h4>', unsafe_allow_html=True)
    project_name = st.text_input("Project Name", placeholder="e.g., Offshore Pipeline Replacement 2026", key="pred_project_name")
    
    # Feature inputs
    st.markdown("##### Feature Values")
    st.caption(f"Enter values for {len(feature_cols)} features. Leave blank for NaN.")
    
    # Create input fields
    input_values = {}
    cols_per_row = 3
    features = list(feature_cols)
    
    for i in range(0, len(features), cols_per_row):
        cols = st.columns(cols_per_row)
        row_features = features[i:i + cols_per_row]
        
        for j, feature in enumerate(row_features):
            with cols[j]:
                # Get current value if exists
                default_val = st.session_state.get(f"input_{feature}", "")
                
                # Create input with better labeling
                value = st.text_input(
                    label=feature,
                    value=default_val,
                    key=f"input_{feature}_{ds_name_pred}",
                    help=f"Enter value for {feature}"
                )
                
                # Parse value
                if value.strip() == "" or value.lower() == "nan":
                    input_values[feature] = np.nan
                else:
                    try:
                        input_values[feature] = float(value)
                    except:
                        input_values[feature] = np.nan
    
    # Prediction button
    if st.button("Run Prediction", key="run_pred_btn", type="primary"):
        try:
            # Prepare input data
            pred_input = ModelPipeline.prepare_prediction_input(feature_cols, input_values)
            
            # Make prediction
            base_pred = float(pipeline.predict(pred_input)[0])
            
            # Calculate cost breakdown (SIMPLIFIED - no EPRR)
            owners_cost, sst_cost, contingency_cost, escalation_cost, grand_total = cost_breakdown(
                base_pred, sst_pct, owners_pct, cont_pct, esc_pct
            )
            
            # Create result entry
            result = {
                "Project Name": project_name,
                "Base CAPEX": round(base_pred, 2),
                "Owner's Cost": owners_cost,
                "SST Cost": sst_cost,
                "Contingency": contingency_cost,
                "Escalation": escalation_cost,
                "Grand Total": grand_total,
                "Target": round(base_pred, 2)  # Same as Base CAPEX for compatibility
            }
            
            # Add feature values
            for feature in feature_cols:
                result[feature] = input_values.get(feature, np.nan)
            
            # Store prediction
            st.session_state.predictions.setdefault(ds_name_pred, []).append(result)
            
            toast("✅ Prediction added!")
            
            # Display results
            st.markdown("##### Prediction Results")
            res_cols = st.columns(5)
            with res_cols[0]:
                st.metric("Base CAPEX", f"{currency_pred} {base_pred:,.2f}")
            with res_cols[1]:
                st.metric("Owner's Cost", f"{currency_pred} {owners_cost:,.2f}")
            with res_cols[2]:
                st.metric("SST", f"{currency_pred} {sst_cost:,.2f}")
            with res_cols[3]:
                st.metric("Contingency", f"{currency_pred} {contingency_cost:,.2f}")
            with res_cols[4]:
                st.metric("Grand Total", f"{currency_pred} {grand_total:,.2f}")
            
            # Store input values for next prediction
            for feature, value in input_values.items():
                st.session_state[f"input_{feature}"] = str(value) if not np.isnan(value) else ""
            
        except Exception as e:
            st.error(f"Prediction failed: {str(e)}")
    
    # ========================= BATCH PREDICTION ===============================
    st.markdown("---")
    st.markdown('<h4 style="margin:0;color:#000;">Batch Prediction (Excel)</h4>', unsafe_allow_html=True)
    
    excel_file = st.file_uploader("Upload Excel file for batch prediction", 
                                  type=["xlsx"], 
                                  key=f"batch_excel_{st.session_state.widget_nonce}")
    
    if excel_file:
        file_id = f"{excel_file.name}_{excel_file.size}_{ds_name_pred}"
        
        if file_id not in st.session_state.processed_excel_files:
            try:
                batch_df = pd.read_excel(excel_file)
                
                # Validate columns
                missing_cols = [col for col in feature_cols if col not in batch_df.columns]
                if missing_cols:
                    st.error(f"Missing required columns in Excel: {missing_cols}")
                else:
                    # Prepare data for prediction
                    X_batch = DataPreprocessor.validate_feature_columns(batch_df[feature_cols])
                    
                    # Make predictions
                    predictions = pipeline.predict(X_batch)
                    
                    # Process each row
                    for i, (idx, row) in enumerate(batch_df.iterrows()):
                        # Get project name
                        project_name_batch = row.get("Project Name", f"Project {i+1}")
                        
                        # Calculate cost breakdown
                        base_pred_batch = float(predictions[i])
                        owners_cost_batch, sst_cost_batch, contingency_cost_batch, escalation_cost_batch, grand_total_batch = cost_breakdown(
                            base_pred_batch, sst_pct, owners_pct, cont_pct, esc_pct
                        )
                        
                        # Create result
                        result_batch = {
                            "Project Name": str(project_name_batch),
                            "Base CAPEX": round(base_pred_batch, 2),
                            "Owner's Cost": owners_cost_batch,
                            "SST Cost": sst_cost_batch,
                            "Contingency": contingency_cost_batch,
                            "Escalation": escalation_cost_batch,
                            "Grand Total": grand_total_batch,
                            "Target": round(base_pred_batch, 2)
                        }
                        
                        # Add feature values
                        for feature in feature_cols:
                            result_batch[feature] = row.get(feature, np.nan)
                        
                        # Store
                        st.session_state.predictions.setdefault(ds_name_pred, []).append(result_batch)
                    
                    st.session_state.processed_excel_files.add(file_id)
                    st.success(f"✅ Processed {len(batch_df)} rows")
                    
            except Exception as e:
                st.error(f"Batch processing failed: {str(e)}")
        else:
            st.info("This file has already been processed.")

    # ========================= RESULTS / EXPORT ==============================
    st.divider()
    st.markdown('<h3 style="margin-top:0;color:#000;">📄 Results</h3>', unsafe_allow_html=True)
    
    ds_name_res = st.selectbox("Dataset for results", list(st.session_state.datasets.keys()), key="ds_results")
    preds = st.session_state.predictions.get(ds_name_res, [])
    
    if preds:
        # Display predictions
        df_preds = pd.DataFrame(preds)
        
        # Format numeric columns
        display_cols = ["Project Name", "Base CAPEX", "Owner's Cost", "SST Cost", 
                       "Contingency", "Escalation", "Grand Total"]
        
        df_display = df_preds[display_cols].copy()
        
        # Format numbers
        for col in display_cols[1:]:  # Skip Project Name
            df_display[col] = df_display[col].apply(lambda x: f"{x:,.2f}" if not pd.isna(x) else "")
        
        st.dataframe(df_display, use_container_width=True, height=300)
        
        # Export options
        st.markdown("##### Export Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Excel export
            bio_xlsx = io.BytesIO()
            df_preds.to_excel(bio_xlsx, index=False, engine="openpyxl")
            bio_xlsx.seek(0)
            
            st.download_button(
                "⬇️ Download Excel",
                data=bio_xlsx,
                file_name=f"{ds_name_res}_predictions.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel_btn"
            )
        
        with col2:
            # CSV export
            csv_data = df_preds.to_csv(index=False)
            st.download_button(
                "⬇️ Download CSV",
                data=csv_data,
                file_name=f"{ds_name_res}_predictions.csv",
                mime="text/csv",
                key="download_csv_btn"
            )
        
        # Clear button
        if st.button("🗑️ Clear all predictions", key="clear_predictions_btn"):
            st.session_state.predictions[ds_name_res] = []
            st.rerun()
    
    else:
        st.info("No predictions yet. Make some predictions above.")

# =======================================================================================
# PROJECT BUILDER TAB - SIMPLIFIED
# =======================================================================================
with tab_pb:
    st.markdown('<h4 style="margin-top:0;color:#000;">🏗️ Project Builder</h4>', unsafe_allow_html=True)
    st.caption("Assemble multi-component CAPEX projects")
    
    if not st.session_state.datasets:
        st.info("No datasets loaded. Please load data in the Data tab first.")
        st.stop()
    
    # Project creation
    colA, colB = st.columns([2, 1])
    with colA:
        new_project_name = st.text_input("New Project Name", placeholder="e.g., CAPEX 2026", key="pb_new_project_name")
    with colB:
        if new_project_name and new_project_name not in st.session_state.projects:
            if st.button("Create Project", key="pb_create_project_btn"):
                st.session_state.projects[new_project_name] = {
                    "components": [], 
                    "totals": {}, 
                    "currency": "",
                    "cost_factors": {
                        "sst_pct": 0.0,
                        "owners_pct": 0.0,
                        "cont_pct": 0.0,
                        "esc_pct": 0.0
                    }
                }
                toast(f"Project '{new_project_name}' created.")
                st.rerun()
    
    if not st.session_state.projects:
        st.info("Create a project above, then add components.")
        st.stop()
    
    # Project selection
    existing_projects = list(st.session_state.projects.keys())
    proj_sel = st.selectbox("Select project", existing_projects, key="pb_project_select")
    proj = st.session_state.projects[proj_sel]
    
    # Project cost factors
    st.markdown("##### Project Cost Factors")
    cf1, cf2 = st.columns(2)
    with cf1:
        proj["cost_factors"]["sst_pct"] = st.number_input("SST (%)", 0.0, 100.0, 
                                                         value=proj["cost_factors"].get("sst_pct", 0.0),
                                                         step=0.5, key=f"pb_sst_{proj_sel}")
        proj["cost_factors"]["owners_pct"] = st.number_input("Owner's Cost (%)", 0.0, 100.0,
                                                            value=proj["cost_factors"].get("owners_pct", 0.0),
                                                            step=0.5, key=f"pb_owners_{proj_sel}")
    with cf2:
        proj["cost_factors"]["cont_pct"] = st.number_input("Contingency (%)", 0.0, 100.0,
                                                          value=proj["cost_factors"].get("cont_pct", 0.0),
                                                          step=0.5, key=f"pb_cont_{proj_sel}")
        proj["cost_factors"]["esc_pct"] = st.number_input("Escalation & Inflation (%)", 0.0, 100.0,
                                                         value=proj["cost_factors"].get("esc_pct", 0.0),
                                                         step=0.5, key=f"pb_esc_{proj_sel}")
    
    # Component addition
    st.markdown("##### Add Component")
    
    ds_names = sorted(st.session_state.datasets.keys())
    dataset_for_comp = st.selectbox("Dataset for component", ds_names, key="pb_dataset_for_component")
    df_comp = st.session_state.datasets[dataset_for_comp]
    
    # Check if model is trained for this dataset
    if f"current_pipeline__{dataset_for_comp}" not in st.session_state:
        st.warning(f"Please train a model for '{dataset_for_comp}' in the Data tab first.")
        st.stop()
    
    pipeline = st.session_state[f"current_pipeline__{dataset_for_comp}"]
    feature_cols = st.session_state[f"feature_cols__{dataset_for_comp}"]
    target_col = df_comp.columns[-1]
    curr_ds = get_currency_symbol(df_comp, target_col)
    
    # Component details
    component_type = st.text_input(
        "Component type",
        placeholder="e.g., Pipeline, Platform, Subsea",
        key=f"pb_component_type_{proj_sel}"
    )
    
    # Feature inputs for component
    st.markdown("###### Component Features")
    comp_inputs = {}
    
    # Create input fields for features
    for i in range(0, len(feature_cols), 2):
        cols = st.columns(2)
        row_features = feature_cols[i:i+2]
        
        for j, feature in enumerate(row_features):
            with cols[j]:
                value = st.text_input(
                    feature,
                    placeholder="Enter value",
                    key=f"pb_{feature}_{proj_sel}_{dataset_for_comp}"
                )
                
                if value.strip() == "" or value.lower() == "nan":
                    comp_inputs[feature] = np.nan
                else:
                    try:
                        comp_inputs[feature] = float(value)
                    except:
                        comp_inputs[feature] = np.nan
    
    # Add component button
    if st.button("➕ Add Component to Project", key=f"pb_add_comp_{proj_sel}"):
        if not component_type:
            st.error("Please enter a component type")
        else:
            try:
                # Prepare input
                pred_input = ModelPipeline.prepare_prediction_input(feature_cols, comp_inputs)
                
                # Make prediction
                base_pred = float(pipeline.predict(pred_input)[0])
                
                # Get cost factors
                sst_pct = proj["cost_factors"]["sst_pct"]
                owners_pct = proj["cost_factors"]["owners_pct"]
                cont_pct = proj["cost_factors"]["cont_pct"]
                esc_pct = proj["cost_factors"]["esc_pct"]
                
                # Calculate costs
                owners_cost, sst_cost, contingency_cost, escalation_cost, grand_total = cost_breakdown(
                    base_pred, sst_pct, owners_pct, cont_pct, esc_pct
                )
                
                # Create component entry
                comp_entry = {
                    "component_type": component_type,
                    "dataset": dataset_for_comp,
                    "prediction": base_pred,
                    "breakdown": {
                        "owners_cost": owners_cost,
                        "sst_cost": sst_cost,
                        "contingency_cost": contingency_cost,
                        "escalation_cost": escalation_cost,
                        "grand_total": grand_total
                    }
                }
                
                # Add to project
                proj["components"].append(comp_entry)
                proj["currency"] = curr_ds
                
                toast(f"Component '{component_type}' added to project.")
                st.rerun()
                
            except Exception as e:
                st.error(f"Failed to add component: {str(e)}")
    
    # ========================= PROJECT OVERVIEW ==============================
    st.markdown("---")
    st.markdown("##### Project Overview")
    
    comps = proj.get("components", [])
    
    if not comps:
        st.info("No components yet. Add components above.")
    else:
        # Display components
        df_components = pd.DataFrame([
            {
                "Component": c["component_type"],
                "Dataset": c["dataset"],
                "Base CAPEX": f"{curr_ds} {c['prediction']:,.2f}",
                "Grand Total": f"{curr_ds} {c['breakdown']['grand_total']:,.2f}"
            }
            for c in comps
        ])
        
        st.dataframe(df_components, use_container_width=True)
        
        # Calculate totals
        totals = project_totals(proj)
        
        # Display totals
        st.markdown("##### Project Totals")
        tcol1, tcol2, tcol3 = st.columns(3)
        with tcol1:
            st.metric("Total Base CAPEX", f"{curr_ds} {totals['capex_sum']:,.2f}")
        with tcol2:
            st.metric("Total SST", f"{curr_ds} {totals['sst']:,.2f}")
        with tcol3:
            st.metric("Total Grand Total", f"{curr_ds} {totals['grand_total']:,.2f}")
        
        # Component management
        st.markdown("##### Component Management")
        for idx, comp in enumerate(comps):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"**{comp['component_type']}**")
                st.caption(f"{comp['dataset']} | Base: {curr_ds} {comp['prediction']:,.2f}")
            with col2:
                st.write(f"Grand Total: {curr_ds} {comp['breakdown']['grand_total']:,.2f}")
            with col3:
                if st.button("🗑️", key=f"del_comp_{proj_sel}_{idx}"):
                    comps.pop(idx)
                    st.rerun()
    
    # ========================= EXPORT ========================================
    st.markdown("---")
    st.markdown("##### Export Project")
    
    if comps:
        # Simple JSON export
        project_json = json.dumps(proj, indent=2, default=float)
        
        st.download_button(
            "⬇️ Download Project (JSON)",
            data=project_json,
            file_name=f"{proj_sel}.json",
            mime="application/json",
            key=f"dl_json_{proj_sel}"
        )
    
    # Import project
    st.markdown("##### Import Project")
    up_json = st.file_uploader("Upload project JSON", type=["json"], 
                              key=f"import_{proj_sel}")
    
    if up_json:
        try:
            imported_data = json.load(up_json)
            st.session_state.projects[proj_sel] = imported_data
            toast("Project imported successfully.")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to import project: {str(e)}")

# =======================================================================================
# SIMPLIFIED MONTE CARLO TAB
# =======================================================================================
with tab_mc:
    st.markdown('<h3 style="margin-top:0;color:#000;">🎲 Monte Carlo Analysis</h3>', unsafe_allow_html=True)
    st.caption("Simple uncertainty analysis for project costs")
    
    if not st.session_state.projects:
        st.info("No projects found. Create a project in the Project Builder tab first.")
        st.stop()
    
    proj_names = list(st.session_state.projects.keys())
    proj_sel_mc = st.selectbox("Select project", proj_names, key="mc_project_select")
    proj = st.session_state.projects[proj_sel_mc]
    
    comps = proj.get("components", [])
    if not comps:
        st.warning("This project has no components. Add components in the Project Builder.")
        st.stop()
    
    # Simple Monte Carlo settings
    st.markdown("##### Simulation Settings")
    
    mc1, mc2 = st.columns(2)
    with mc1:
        n_simulations = st.number_input("Number of simulations", 100, 10000, 1000, 100, key="mc_n_sims")
        feature_uncertainty = st.slider("Feature uncertainty (%)", 0.0, 50.0, 10.0, 1.0, key="mc_feat_unc")
    with mc2:
        cost_uncertainty = st.slider("Cost uncertainty (%)", 0.0, 30.0, 5.0, 1.0, key="mc_cost_unc")
        budget = st.number_input("Budget threshold", min_value=0.0, value=1000000.0, step=10000.0, key="mc_budget")
    
    if st.button("Run Monte Carlo", type="primary", key="mc_run"):
        try:
            with st.spinner("Running simulations..."):
                # Collect all component simulations
                all_simulations = []
                
                for comp in comps:
                    ds_name = comp["dataset"]
                    
                    # Get trained model
                    if f"current_pipeline__{ds_name}" not in st.session_state:
                        st.warning(f"No trained model for {ds_name}")
                        continue
                    
                    pipeline = st.session_state[f"current_pipeline__{ds_name}"]
                    feature_cols = st.session_state[f"feature_cols__{ds_name}"]
                    
                    # Run simulations
                    sim_results = monte_carlo_simulation(
                        pipeline,
                        feature_cols,
                        {},  # Would need base values here
                        n_simulations=n_simulations,
                        feature_uncertainty=feature_uncertainty/100
                    )
                    
                    all_simulations.append(sim_results["prediction"].values)
                
                if all_simulations:
                    # Sum across components
                    total_simulations = np.sum(all_simulations, axis=0)
                    
                    # Calculate statistics
                    p50 = np.percentile(total_simulations, 50)
                    p80 = np.percentile(total_simulations, 80)
                    p90 = np.percentile(total_simulations, 90)
                    
                    exceed_prob = (total_simulations > budget).mean() * 100
                    
                    # Display results
                    st.markdown("##### Results")
                    
                    rcol1, rcol2, rcol3, rcol4 = st.columns(4)
                    with rcol1:
                        st.metric("P50", f"${p50:,.0f}")
                    with rcol2:
                        st.metric("P80", f"${p80:,.0f}")
                    with rcol3:
                        st.metric("P90", f"${p90:,.0f}")
                    with rcol4:
                        st.metric(f"P(>${budget:,.0f})", f"{exceed_prob:.1f}%")
                    
                    # Histogram
                    fig = px.histogram(
                        x=total_simulations,
                        nbins=50,
                        title="Total Cost Distribution",
                        labels={"x": "Total Cost", "y": "Frequency"}
                    )
                    
                    # Add budget line
                    fig.add_vline(
                        x=budget,
                        line_dash="dash",
                        line_color="red",
                        annotation_text=f"Budget: ${budget:,.0f}"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                else:
                    st.warning("No valid simulations were generated")
                    
        except Exception as e:
            st.error(f"Monte Carlo failed: {str(e)}")

# =======================================================================================
# COMPARE PROJECTS TAB
# =======================================================================================
with tab_compare:
    st.markdown('<h3 style="margin-top:0;color:#000;">🔀 Compare Projects</h3>', unsafe_allow_html=True)
    
    if len(st.session_state.projects) < 2:
        st.info("Create at least 2 projects in the Project Builder to compare.")
        st.stop()
    
    project_names = list(st.session_state.projects.keys())
    selected_projects = st.multiselect(
        "Select projects to compare",
        project_names,
        default=project_names[:2] if len(project_names) >= 2 else project_names
    )
    
    if len(selected_projects) < 2:
        st.warning("Please select at least 2 projects")
        st.stop()
    
    # Collect project data
    comparison_data = []
    for proj_name in selected_projects:
        proj = st.session_state.projects[proj_name]
        totals = project_totals(proj)
        
        comparison_data.append({
            "Project": proj_name,
            "Components": len(proj.get("components", [])),
            "Base CAPEX": totals["capex_sum"],
            "SST": totals["sst"],
            "Owner's Cost": totals["owners"],
            "Contingency": totals["cont"],
            "Escalation": totals["esc"],
            "Grand Total": totals["grand_total"]
        })
    
    df_comparison = pd.DataFrame(comparison_data)
    
    # Display comparison table
    st.markdown("##### Project Comparison")
    st.dataframe(
        df_comparison.style.format({
            "Base CAPEX": "{:,.2f}",
            "SST": "{:,.2f}",
            "Owner's Cost": "{:,.2f}",
            "Contingency": "{:,.2f}",
            "Escalation": "{:,.2f}",
            "Grand Total": "{:,.2f}"
        }),
        use_container_width=True
    )
    
    # Visualization
    st.markdown("##### Visualization")
    
    viz_type = st.selectbox("Chart type", ["Bar Chart", "Stacked Bar"], key="viz_type")
    
    if viz_type == "Bar Chart":
        fig = px.bar(
            df_comparison,
            x="Project",
            y="Grand Total",
            title="Grand Total by Project",
            text="Grand Total"
        )
        fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    else:
        # Stacked bar
        melt_df = df_comparison.melt(
            id_vars=["Project"],
            value_vars=["Base CAPEX", "SST", "Owner's Cost", "Contingency", "Escalation"],
            var_name="Cost Type",
            value_name="Amount"
        )
        
        fig = px.bar(
            melt_df,
            x="Project",
            y="Amount",
            color="Cost Type",
            title="Cost Breakdown by Project",
            barmode="stack"
        )
    
    st.plotly_chart(fig, use_container_width=True)
