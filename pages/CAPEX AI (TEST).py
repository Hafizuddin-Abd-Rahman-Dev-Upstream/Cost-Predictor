# ======================================================================================

# CAPEX AI RT2026 — FULL APP

# Models : Random Forest + Gradient Boosting only (lecturer recommendation)

# Features: Adjustable train/test split, side-by-side model comparison,

# actual vs predicted scatter, feature importance for both models

# ======================================================================================

import io
import json
import re
import requests
import numpy as np
import pandas as pd
import streamlit as st

try:
from sklearn.impute import KNNImputer, SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
except Exception as e:
st.error(
        "❌ Missing dependency: **scikit-learn**.\n\n"
        "Add `scikit-learn` to requirements.txt and redeploy.\n\n"
        f"Details: {e}"
    )
    st.stop()


import plotly.express as px
import plotly.graph_objects as go

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ── page config ──────────────────────────────────────────────────────────────

st.set_page_config(
page_title=“CAPEX AI RT2026”,
page_icon=“💠”,
layout=“wide”,
initial_sidebar_state=“expanded”,
)

# ── brand colours ─────────────────────────────────────────────────────────────

PETRONAS = {
“teal”:      “#00A19B”,
“teal_dark”: “#008C87”,
“purple”:    “#6C4DD3”,
“white”:     “#FFFFFF”,
“black”:     “#0E1116”,
“border”:    “rgba(0,0,0,0.10)”,
}

# ── SharePoint links ──────────────────────────────────────────────────────────

SHAREPOINT_LINKS = {
“Shallow Water”: “https://petronas.sharepoint.com/sites/your-site/shallow-water”,
“Deep Water”:    “https://petronas.sharepoint.com/sites/your-site/deep-water”,
“Onshore”:       “https://petronas.sharepoint.com/sites/your-site/onshore”,
“Uncon”:         “https://petronas.sharepoint.com/sites/your-site/uncon”,
“CCS”:           “https://petronas.sharepoint.com/sites/your-site/ccs”,
}

# ── global CSS ────────────────────────────────────────────────────────────────

st.markdown(
f”””

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body{{font-family:'Inter',sans-serif;}}
[data-testid="stAppViewContainer"]{{background:{PETRONAS["white"]};color:{PETRONAS["black"]};padding-top:.5rem;}}
#MainMenu,footer{{visibility:hidden;}}
[data-testid="stSidebar"]{{
  background:linear-gradient(180deg,{PETRONAS["teal"]} 0%,{PETRONAS["teal_dark"]} 100%) !important;
  color:#fff !important;border-top-right-radius:16px;border-bottom-right-radius:16px;
  box-shadow:0 6px 20px rgba(0,0,0,.15);}}
[data-testid="stSidebar"] *{{color:#fff !important;}}
[data-testid="collapsedControl"]{{position:fixed !important;top:50% !important;left:10px !important;
  transform:translateY(-50%) !important;z-index:9999 !important;}}
.petronas-hero{{border-radius:20px;padding:28px 32px;margin:6px 0 18px 0;color:#fff;
  background:linear-gradient(135deg,{PETRONAS["teal"]},{PETRONAS["purple"]},{PETRONAS["black"]});
  background-size:200% 200%;
  animation:heroGradient 8s ease-in-out infinite,fadeIn .8s ease-in-out,heroPulse 5s ease-in-out infinite;
  box-shadow:0 10px 24px rgba(0,0,0,.12);}}
@keyframes heroGradient{{0%{{background-position:0% 50%}}50%{{background-position:100% 50%}}100%{{background-position:0% 50%}}}}
@keyframes fadeIn{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes heroPulse{{
  0%{{box-shadow:0 0 16px rgba(0,161,155,.45)}}25%{{box-shadow:0 0 26px rgba(108,77,211,.55)}}
  50%{{box-shadow:0 0 36px rgba(0,161,155,.55)}}75%{{box-shadow:0 0 26px rgba(108,77,211,.55)}}
  100%{{box-shadow:0 0 16px rgba(0,161,155,.45)}}}}
.petronas-hero h1{{margin:0 0 5px;font-weight:800;letter-spacing:.3px;}}
.petronas-hero p{{margin:0;opacity:.9;font-weight:500;}}
.stButton>button,.stDownloadButton>button,.petronas-button{{
  border-radius:10px;padding:.6rem 1.1rem;font-weight:600;color:#fff !important;border:none;
  background:linear-gradient(to right,{PETRONAS["teal"]},{PETRONAS["purple"]});
  background-size:200% auto;
  transition:background-position .85s ease,transform .2s ease,box-shadow .25s ease;
  text-decoration:none;display:inline-block;}}
.stButton>button:hover,.stDownloadButton>button:hover,.petronas-button:hover{{
  background-position:right center;transform:translateY(-1px);box-shadow:0 6px 16px rgba(0,0,0,.18);}}
.stTabs [role="tablist"]{{display:flex;gap:8px;border-bottom:none;padding-bottom:6px;}}
.stTabs [role="tab"]{{background:#fff;color:{PETRONAS["black"]};border-radius:8px;padding:10px 18px;
  border:1px solid {PETRONAS["border"]};font-weight:600;transition:all .3s ease;position:relative;}}
.stTabs [role="tab"]:hover{{background:linear-gradient(to right,{PETRONAS["teal"]},{PETRONAS["purple"]});color:#fff;}}
.stTabs [role="tab"][aria-selected="true"]{{
  background:linear-gradient(to right,{PETRONAS["teal"]},{PETRONAS["purple"]});
  color:#fff;border-color:transparent;box-shadow:0 4px 16px rgba(0,0,0,.15);}}
.stTabs [role="tab"][aria-selected="true"]::after{{
  content:"";position:absolute;left:10%;bottom:-3px;width:80%;height:3px;
  background:linear-gradient(90deg,{PETRONAS["teal"]},{PETRONAS["purple"]},{PETRONAS["teal"]});
  background-size:200% 100%;border-radius:2px;animation:glowSlide 2.5s linear infinite;}}
@keyframes glowSlide{{0%{{background-position:0% 50%}}50%{{background-position:100% 50%}}100%{{background-position:0% 50%}}}}
</style>

“””,
unsafe_allow_html=True,
)

# ── hero ──────────────────────────────────────────────────────────────────────

st.markdown(
“””

<div class="petronas-hero">
  <h1>CAPEX AI RT2026</h1>
  <p>Data-driven CAPEX prediction · Random Forest &amp; Gradient Boosting</p>
</div>
""",
    unsafe_allow_html=True,
)

# ── auth ──────────────────────────────────────────────────────────────────────

if “authenticated” not in st.session_state:
st.session_state.authenticated = False

APPROVED_EMAILS   = [str(e).strip().lower() for e in st.secrets.get(“emails”, [])]
correct_password  = st.secrets.get(“password”, None)

if not st.session_state.authenticated:
with st.form(“login_form”):
st.markdown(”#### 🔐 Access Required”)
email    = (st.text_input(“Email Address”, key=“login_email”) or “”).strip().lower()
password = st.text_input(“Access Password”, type=“password”, key=“login_pwd”)
if st.form_submit_button(“Login”):
if (email in APPROVED_EMAILS) and (password == correct_password):
st.session_state.authenticated = True
st.success(“✅ Access granted.”)
st.rerun()
else:
st.error(“❌ Invalid credentials.”)
st.stop()

# ── session state ─────────────────────────────────────────────────────────────

for key, default in [
(“datasets”,              {}),
(“predictions”,           {}),
(“processed_excel_files”, set()),
(”_last_metrics”,         None),
(“projects”,              {}),
(“uploader_nonce”,        0),
(“widget_nonce”,          0),
]:
if key not in st.session_state:
st.session_state[key] = default

# ── helpers ───────────────────────────────────────────────────────────────────

def toast(msg, icon=“✅”):
try:
st.toast(f”{icon} {msg}”)
except Exception:
st.success(msg)

def format_with_commas(num):
try:    return f”{float(num):,.2f}”
except: return str(num)

def is_junk_col(colname: str) -> bool:
h = str(colname).strip().upper()
return (not h) or h.startswith(“UNNAMED”) or h in {“INDEX”, “IDX”}

def currency_from_header(header: str) -> str:
h = (header or “”).strip().upper()
if “€” in h: return “€”
if “£” in h: return “£”
if “$” in h: return “$”
if re.search(r”\bUSD\b”, h): return “USD”
if re.search(r”\b(MYR|RM)\b”, h): return “RM”
return “”

def get_currency_symbol(df: pd.DataFrame, target_col=None) -> str:
if df is None or df.empty: return “”
if target_col and target_col in df.columns:
return currency_from_header(str(target_col))
for c in reversed(df.columns):
if not is_junk_col(c):
return currency_from_header(str(c))
return “”

def cost_breakdown(base_pred, sst_pct, owners_pct, cont_pct, esc_pct):
base_pred     = float(base_pred)
owners_cost   = round(base_pred * (owners_pct / 100), 2)
sst_cost      = round(base_pred * (sst_pct   / 100), 2)
contingency   = round((base_pred + owners_cost) * (cont_pct / 100), 2)
escalation    = round((base_pred + owners_cost) * (esc_pct  / 100), 2)
grand_total   = round(base_pred + owners_cost + sst_cost + contingency + escalation, 2)
return owners_cost, sst_cost, contingency, escalation, grand_total

def project_components_df(proj):
rows = []
for c in proj.get(“components”, []):
rows.append({
“Component”:   c[“component_type”],
“Dataset”:     c[“dataset”],
“Base CAPEX”:  float(c[“prediction”]),
“Owner’s Cost”:float(c[“breakdown”][“owners_cost”]),
“Contingency”: float(c[“breakdown”][“contingency_cost”]),
“Escalation”:  float(c[“breakdown”][“escalation_cost”]),
“SST”:         float(c[“breakdown”][“sst_cost”]),
“Grand Total”: float(c[“breakdown”][“grand_total”]),
})
return pd.DataFrame(rows)

def project_totals(proj):
dfc = project_components_df(proj)
if dfc.empty:
return {k: 0.0 for k in (“capex_sum”,“owners”,“cont”,“esc”,“sst”,“grand_total”)}
return {
“capex_sum”:   float(dfc[“Base CAPEX”].sum()),
“owners”:      float(dfc[“Owner’s Cost”].sum()),
“cont”:        float(dfc[“Contingency”].sum()),
“esc”:         float(dfc[“Escalation”].sum()),
“sst”:         float(dfc[“SST”].sum()),
“grand_total”: float(dfc[“Grand Total”].sum()),
}

# ── GitHub data source ────────────────────────────────────────────────────────

GITHUB_USER  = “Hafizuddin-Abd-Rahman-Dev-Upstream”
REPO_NAME    = “Cost-Predictor”
BRANCH       = “main”
DATA_FOLDER  = “pages/data_CAPEX”

@st.cache_data(ttl=600, show_spinner=False)
def fetch_json(url):
r = requests.get(url, timeout=15)
r.raise_for_status()
return r.json()

@st.cache_data(ttl=600, show_spinner=False)
def list_csvs_from_manifest(folder_path):
url = (f”https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}”
f”/{BRANCH}/{folder_path}/files.json”)
try:
data = fetch_json(url)
return [str(x) for x in data] if isinstance(data, list) else []
except Exception as e:
st.error(f”Failed to load CSV manifest: {e}”)
return []

# =============================================================================

# DATA PREPROCESSOR

# =============================================================================

class DataPreprocessor:

```
@staticmethod
def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    bad = [c for c in df.columns if is_junk_col(c)]
    if bad:
        df = df.drop(columns=bad)
    return df

@staticmethod
def extract_features_target(df: pd.DataFrame):
    if df is None or df.empty:
        raise ValueError("Empty dataset")
    target_col   = df.columns[-1]
    feature_cols = [c for c in df.columns if c != target_col]
    if not feature_cols:
        raise ValueError("No feature columns found")
    X = df[feature_cols].copy()
    y = pd.to_numeric(df[target_col], errors="coerce")
    if y.isna().sum() / len(y) > 0.8:
        raise ValueError(f"Target column '{target_col}' has too many missing values")
    return X, y, target_col

@staticmethod
def validate_feature_columns(X: pd.DataFrame) -> pd.DataFrame:
    X = X.copy()
    for col in X.columns:
        if X[col].dtype == object:
            X[col] = pd.to_numeric(X[col], errors="coerce")
    return X
```

# =============================================================================

# MODEL PIPELINE  — RF + GB only

# =============================================================================

class ModelPipeline:

```
MODEL_CANDIDATES = {
    "RandomForest": lambda rs=42: RandomForestRegressor(
        n_estimators=200,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        random_state=rs,
        n_jobs=-1,
    ),
    "GradientBoosting": lambda rs=42: GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=4,
        subsample=0.8,
        random_state=rs,
    ),
}

@classmethod
def create_pipeline(cls, model_name: str, random_state: int = 42) -> Pipeline:
    if model_name not in cls.MODEL_CANDIDATES:
        model_name = "RandomForest"
    ctor = cls.MODEL_CANDIDATES[model_name]
    try:
        model = ctor(random_state)
    except TypeError:
        model = ctor()
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("model",   model),
    ])

@classmethod
@st.cache_resource(show_spinner=False)
def train_both_cached(
    _cls,
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.20,
    random_state: int = 42,
) -> dict:
    """Train RF and GB, auto-select winner by R²."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    results = {}
    for name in ("RandomForest", "GradientBoosting"):
        pipe = _cls.create_pipeline(name, random_state)
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)
        results[name] = {
            "pipeline": pipe,
            "r2":    round(float(r2_score(y_test, y_pred)), 4),
            "rmse":  round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 4),
            "mae":   round(float(mean_absolute_error(y_test, y_pred)), 4),
            "y_test":  y_test.values,
            "y_pred":  y_pred,
        }

    best = max(results, key=lambda k: results[k]["r2"])
    return {
        "rf":           results["RandomForest"],
        "gb":           results["GradientBoosting"],
        "best":         best,
        "pipeline":     results[best]["pipeline"],
        "feature_cols": list(X.columns),
        "model":        best,
        "r2":           results[best]["r2"],
        "rmse":         results[best]["rmse"],
        "mae":          results[best]["mae"],
    }

@staticmethod
def prepare_prediction_input(feature_cols: list, payload: dict) -> pd.DataFrame:
    row = {}
    for col in feature_cols:
        val = payload.get(col, np.nan)
        if val is None or (isinstance(val, str) and val.strip() == ""):
            row[col] = np.nan
        elif isinstance(val, (int, float, np.number)):
            row[col] = float(val)
        else:
            try:    row[col] = float(val)
            except: row[col] = np.nan
    return pd.DataFrame([row], columns=feature_cols)
```

# =============================================================================

# MONTE CARLO

# =============================================================================

def monte_carlo_simulation(pipeline, feature_cols, base_values,
n_simulations=1000, feature_uncertainty=0.05):
np.random.seed(42)
base_array = np.array([float(base_values.get(c, np.nan)) for c in feature_cols])
preds = []
for _ in range(n_simulations):
noise     = np.random.normal(0, feature_uncertainty, len(base_array))
sim_feats = base_array * (1 + noise)
sim_df    = pd.DataFrame([sim_feats], columns=feature_cols)
try:    preds.append(float(pipeline.predict(sim_df)[0]))
except: preds.append(0.0)
return pd.DataFrame({“prediction”: preds})

# ── nav bar ───────────────────────────────────────────────────────────────────

nav_labels = [“SHALLOW WATER”, “DEEP WATER”, “ONSHORE”, “UNCON”, “CCS”]
for col, label in zip(st.columns(len(nav_labels)), nav_labels):
with col:
url = SHAREPOINT_LINKS.get(label.title(), “#”)
st.markdown(
f’<a href=”{url}” target=”_blank” rel=“noopener” class=“petronas-button”’
f’ style=“width:100%;text-align:center;display:inline-block;”>{label}</a>’,
unsafe_allow_html=True,
)

# ── top-level tabs ────────────────────────────────────────────────────────────

tab_data, tab_pb, tab_mc, tab_compare = st.tabs([
“📊 Data”, “🏗️ Project Builder”, “🎲 Monte Carlo”, “🔀 Compare Projects”
])

# =============================================================================

# TAB 1 — DATA

# =============================================================================

with tab_data:
st.markdown(’<h3 style="margin-top:0;color:#000;">📁 Data</h3>’, unsafe_allow_html=True)

```
# ── source selection ──────────────────────────────────────────────────────
c1, c2 = st.columns([1.2, 1])
with c1:
    data_source = st.radio("Choose data source", ["Upload CSV", "Load from Server"],
                           horizontal=True, key="data_source")
with c2:
    st.caption("Enterprise Storage (SharePoint)")
    data_link = (
        "https://petronas.sharepoint.com/sites/ecm_ups_coe/confidential/"
        "DFE%20Cost%20Engineering/Forms/AllItems.aspx"
    )
    st.markdown(
        f'<a href="{data_link}" target="_blank" rel="noopener" class="petronas-button">'
        f'Open Enterprise Storage</a>',
        unsafe_allow_html=True,
    )

uploaded_files = []
if data_source == "Upload CSV":
    uploaded_files = st.file_uploader(
        "Upload CSV files (max 200 MB)",
        type="csv", accept_multiple_files=True,
        key=f"csv_uploader_{st.session_state.uploader_nonce}",
    )
else:
    github_csvs = list_csvs_from_manifest(DATA_FOLDER)
    if github_csvs:
        sel = st.selectbox("Choose CSV from GitHub", github_csvs, key="github_csv_select")
        if st.button("Load selected CSV", key="load_github_csv_btn"):
            raw_url = (f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}"
                       f"/{BRANCH}/{DATA_FOLDER}/{sel}")
            try:
                df = DataPreprocessor.clean_dataframe(pd.read_csv(raw_url))
                st.session_state.datasets[sel] = df
                st.session_state.predictions.setdefault(sel, [])
                toast(f"Loaded: {sel}")
                st.rerun()
            except Exception as e:
                st.error(f"Error loading CSV: {e}")
    else:
        st.info("No CSV files found in GitHub folder.")

if uploaded_files:
    for up in uploaded_files:
        if up.name not in st.session_state.datasets:
            try:
                df = DataPreprocessor.clean_dataframe(pd.read_csv(up))
                st.session_state.datasets[up.name] = df
                st.session_state.predictions.setdefault(up.name, [])
            except Exception as e:
                st.error(f"Failed to read {up.name}: {e}")
    toast("Dataset(s) added.")

st.divider()

# ── control buttons ───────────────────────────────────────────────────────
cA, cB, cC, cD = st.columns(4)
with cA:
    if st.button("🧹 Clear predictions", key="clear_preds_btn"):
        st.session_state.predictions = {k: [] for k in st.session_state.predictions}
        toast("Predictions cleared.", "🧹"); st.rerun()
with cB:
    if st.button("🧺 Clear history", key="clear_processed_btn"):
        st.session_state.processed_excel_files = set()
        toast("History cleared.", "🧺"); st.rerun()
with cC:
    if st.button("🔁 Refresh", key="refresh_manifest_btn"):
        list_csvs_from_manifest.clear(); fetch_json.clear()
        toast("Refreshed.", "🔁"); st.rerun()
with cD:
    if st.button("🗂️ Clear all data", key="clear_datasets_btn"):
        st.session_state.datasets              = {}
        st.session_state.predictions           = {}
        st.session_state.processed_excel_files = set()
        st.session_state._last_metrics         = None
        st.session_state.uploader_nonce       += 1
        st.session_state.widget_nonce         += 1
        toast("All data cleared.", "🗂️"); st.rerun()

st.divider()

if not st.session_state.datasets:
    st.info("Upload or load a dataset to proceed.")
    st.stop()

# ── active dataset preview ────────────────────────────────────────────────
ds_name_data = st.selectbox("Active dataset", list(st.session_state.datasets.keys()),
                            key="active_dataset_data")
df_active    = st.session_state.datasets[ds_name_data]
target_col_active = df_active.columns[-1]
currency_active   = get_currency_symbol(df_active, target_col_active)

colA, colB, colC, colD2 = st.columns(4)
colA.metric("Rows",     f"{df_active.shape[0]:,}")
colB.metric("Columns",  f"{df_active.shape[1]:,}")
colC.metric("Currency", currency_active or "—")
colD2.caption(f"Target column: **{target_col_active}**")

with st.expander("Preview (first 10 rows)", expanded=False):
    st.dataframe(df_active.head(10), use_container_width=True)

# =========================================================================
# MODEL TRAINING  — RF + GB with adjustable split
# =========================================================================
st.divider()
st.markdown('<h3 style="margin-top:0;color:#000;">⚙️ Model Training</h3>',
            unsafe_allow_html=True)

ds_name_model = st.selectbox("Dataset for training",
                             list(st.session_state.datasets.keys()), key="ds_model")
df_model = st.session_state.datasets[ds_name_model]

try:
    X, y, target_col = DataPreprocessor.extract_features_target(df_model)
    st.success(f"✅ Ready — **{X.shape[1]} features**, target: **{target_col}**")
    col1, col2, col3 = st.columns(3)
    col1.metric("Features",      X.shape[1])
    col2.metric("Samples",       X.shape[0])
    valid_n = int(y.notna().sum())
    col3.metric("Valid targets", f"{valid_n} ({valid_n/len(y)*100:.1f}%)")
except Exception as e:
    st.error(f"Data preparation failed: {e}")
    st.stop()

# ── train/test split slider ───────────────────────────────────────────────
st.markdown("##### Train / Test Split")
split_col, btn_col = st.columns([3, 1])

with split_col:
    test_size = st.slider(
        "Test set size",
        min_value=0.10, max_value=0.40,
        value=0.20, step=0.05,
        key="train_test_size",
        help="Proportion of data held out for evaluation (remainder used for training)",
    )
    train_pct = round((1 - test_size) * 100)
    test_pct  = round(test_size * 100)
    n_total   = len(X)
    n_train   = int(n_total * (1 - test_size))
    n_test    = n_total - n_train

    # visual split bar
    st.markdown(
        f"""
        <div style="display:flex;height:14px;border-radius:7px;overflow:hidden;margin-top:4px;">
          <div style="width:{train_pct}%;background:#00A19B;"></div>
          <div style="width:{test_pct}%;background:#6C4DD3;"></div>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:12px;margin-top:4px;">
          <span style="color:#00A19B;font-weight:600;">🟦 Train {train_pct}% &nbsp;({n_train} rows)</span>
          <span style="color:#6C4DD3;font-weight:600;">🟪 Test {test_pct}% &nbsp;({n_test} rows)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with btn_col:
    st.write("")  # spacer
    st.write("")
    run_train = st.button("🚀 Train RF & GB", key="run_training_btn", type="primary")

# ── training ──────────────────────────────────────────────────────────────
if run_train:
    try:
        with st.spinner("Training Random Forest and Gradient Boosting…"):
            metrics = ModelPipeline.train_both_cached(
                X, y,
                test_size=float(test_size),
                random_state=42,
            )

        # persist
        st.session_state._last_metrics = metrics
        st.session_state[f"trained_model__{ds_name_model}"]    = metrics
        st.session_state[f"current_pipeline__{ds_name_model}"] = metrics["pipeline"]
        st.session_state[f"feature_cols__{ds_name_model}"]     = metrics["feature_cols"]

        knn_imputer = KNNImputer(n_neighbors=5)
        knn_imputer.fit(X)
        st.session_state[f"knn_imputer_{ds_name_model}"] = knn_imputer

        toast("Training complete! 🎉")

        # ── comparison table ──────────────────────────────────────────────
        st.markdown("##### Model Comparison")
        rf = metrics["rf"]
        gb = metrics["gb"]

        compare_df = pd.DataFrame({
            "Metric":            ["R² Score ↑", "RMSE ↓", "MAE ↓"],
            "Random Forest":     [rf["r2"],   rf["rmse"],  rf["mae"]],
            "Gradient Boosting": [gb["r2"],   gb["rmse"],  gb["mae"]],
        })

        def highlight_best(row):
            rf_v, gb_v = row["Random Forest"], row["Gradient Boosting"]
            best = "Random Forest" if (
                (row["Metric"].endswith("↑") and rf_v >= gb_v) or
                (row["Metric"].endswith("↓") and rf_v <= gb_v)
            ) else "Gradient Boosting"
            return [
                "background-color:#d4f5f3;font-weight:700" if c == best else ""
                for c in row.index
            ]

        styled = (
            compare_df.style
            .apply(highlight_best, axis=1)
            .format({"Random Forest": "{:.4f}", "Gradient Boosting": "{:.4f}"})
        )
        st.dataframe(styled, use_container_width=True, hide_index=True)

        winner = metrics["best"]
        st.success(f"✅ **{winner}** selected as active model (highest R²)")

        # ── KPI row ───────────────────────────────────────────────────────
        st.markdown("##### Active Model Performance")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Model",  winner)
        m2.metric("R²",     f"{metrics['r2']:.4f}")
        m3.metric("RMSE",   f"{metrics['rmse']:,.2f}")
        m4.metric("MAE",    f"{metrics['mae']:,.2f}")

        # ── Actual vs Predicted scatter ───────────────────────────────────
        st.markdown(f"##### Actual vs Predicted — {winner}")
        bk = "rf" if winner == "RandomForest" else "gb"
        y_test_arr = metrics[bk]["y_test"]
        y_pred_arr = metrics[bk]["y_pred"]

        lo = float(min(y_test_arr.min(), y_pred_arr.min()))
        hi = float(max(y_test_arr.max(), y_pred_arr.max()))

        fig_scatter = go.Figure()
        fig_scatter.add_trace(go.Scatter(
            x=y_test_arr, y=y_pred_arr, mode="markers",
            marker=dict(color="#00A19B", opacity=0.6, size=6),
            name="Predictions",
        ))
        fig_scatter.add_trace(go.Scatter(
            x=[lo, hi], y=[lo, hi], mode="lines",
            line=dict(color="#6C4DD3", dash="dash", width=2),
            name="Perfect fit",
        ))
        fig_scatter.update_layout(
            xaxis_title="Actual CAPEX (MM USD)",
            yaxis_title="Predicted CAPEX (MM USD)",
            height=380, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="white", plot_bgcolor="white",
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

        # ── Feature importance side by side ───────────────────────────────
        st.markdown("##### Feature Importance — RF vs GB")
        fi_left, fi_right = st.columns(2)
        for container, (label, bkey) in zip(
            [fi_left, fi_right],
            [("Random Forest", "rf"), ("Gradient Boosting", "gb")],
        ):
            pipe = metrics[bkey]["pipeline"]
            importances = pipe.named_steps["model"].feature_importances_
            fi_df = pd.DataFrame({
                "Feature":    metrics["feature_cols"],
                "Importance": importances,
            }).sort_values("Importance", ascending=True)

            fig_fi = go.Figure(go.Bar(
                x=fi_df["Importance"], y=fi_df["Feature"],
                orientation="h",
                marker_color="#00A19B" if bkey == "rf" else "#6C4DD3",
            ))
            fig_fi.update_layout(
                title=label,
                xaxis_title="Importance",
                height=max(260, 32 * len(fi_df)),
                margin=dict(l=0, r=0, t=35, b=0),
                paper_bgcolor="white", plot_bgcolor="white",
            )
            with container:
                st.plotly_chart(fig_fi, use_container_width=True)

    except Exception as e:
        st.error(f"Training failed: {e}")

# =========================================================================
# VISUALIZATION
# =========================================================================
st.divider()
st.markdown('<h3 style="margin-top:0;color:#000;">📈 Visualization</h3>',
            unsafe_allow_html=True)

ds_name_viz = st.selectbox("Dataset for visualization",
                           list(st.session_state.datasets.keys()), key="ds_viz")
df_viz = st.session_state.datasets[ds_name_viz]

try:
    numeric_df = df_viz.select_dtypes(include=[np.number])
    if len(numeric_df.columns) > 1:
        st.markdown("##### Correlation Matrix")
        corr    = numeric_df.corr()
        fig_cor = px.imshow(corr, text_auto=".2f", aspect="auto",
                            color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
        fig_cor.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_cor, use_container_width=True)
    else:
        st.info("Need at least 2 numeric columns for correlation matrix.")
except Exception as e:
    st.error(f"Visualization error: {e}")

# =========================================================================
# PREDICT
# =========================================================================
st.divider()
st.markdown('<h3 style="margin-top:0;color:#000;">🎯 Predict</h3>',
            unsafe_allow_html=True)

ds_name_pred = st.selectbox("Dataset for prediction",
                            list(st.session_state.datasets.keys()), key="ds_pred")
df_pred = st.session_state.datasets[ds_name_pred]

if f"current_pipeline__{ds_name_pred}" not in st.session_state:
    st.warning("⚠️ Please train a model first using the Model Training section above.")
    st.stop()

pipeline     = st.session_state[f"current_pipeline__{ds_name_pred}"]
feature_cols = st.session_state[f"feature_cols__{ds_name_pred}"]
target_col   = df_pred.columns[-1]
currency_pred= get_currency_symbol(df_pred, target_col)

# active model badge
trained_meta = st.session_state.get(f"trained_model__{ds_name_pred}", {})
active_model = trained_meta.get("best", "—")
st.info(f"🤖 Active model: **{active_model}**")

# ── cost factors ──────────────────────────────────────────────────────────
st.markdown("##### Cost Factors")
cf1, cf2 = st.columns(2)
with cf1:
    sst_pct    = st.number_input("SST (%)",         0.0, 100.0, 0.0, 0.5, key="pred_sst")
    owners_pct = st.number_input("Owner's Cost (%)",0.0, 100.0, 0.0, 0.5, key="pred_owner")
with cf2:
    cont_pct   = st.number_input("Contingency (%)", 0.0, 100.0, 0.0, 0.5, key="pred_cont")
    esc_pct    = st.number_input("Escalation (%)",  0.0, 100.0, 0.0, 0.5, key="pred_esc")

project_name = st.text_input("Project Name",
                             placeholder="e.g., Offshore Pipeline Replacement 2026",
                             key="pred_project_name")

# ── feature inputs ────────────────────────────────────────────────────────
st.markdown("##### Feature Values")
st.caption(f"Enter values for **{len(feature_cols)}** features. Leave blank = NaN (will be imputed).")

input_values = {}
for i in range(0, len(feature_cols), 3):
    cols = st.columns(3)
    for j, feat in enumerate(feature_cols[i:i+3]):
        with cols[j]:
            val = st.text_input(feat, value="",
                                key=f"input_{feat}_{ds_name_pred}",
                                help=f"Enter value for {feat}")
            if val.strip() in ("", "nan"):
                input_values[feat] = np.nan
            else:
                try:    input_values[feat] = float(val)
                except: input_values[feat] = np.nan

use_knn = st.checkbox(
    "🔮 Use KNN imputation for missing features",
    value=False, key=f"use_knn_{ds_name_pred}",
    help="Estimates missing values from similar training rows",
)

if st.button("Run Prediction", key="run_pred_btn", type="primary"):
    try:
        pred_input     = ModelPipeline.prepare_prediction_input(feature_cols, input_values)
        original_inputs= input_values.copy()
        imputation_method = "pipeline median"

        if use_knn:
            knn_key = f"knn_imputer_{ds_name_pred}"
            if knn_key in st.session_state:
                arr = st.session_state[knn_key].transform(pred_input)
                pred_input = pd.DataFrame(arr, columns=feature_cols)
                imputation_method = "KNN"
            else:
                st.warning("KNN imputer unavailable — using median fallback.")

        base_pred = float(pipeline.predict(pred_input)[0])

        # ── imputed values table ──────────────────────────────────────────
        st.markdown("##### Feature Values Used")
        st.caption(f"Imputation: **{imputation_method}**")
        comp_rows = []
        for col in feature_cols:
            u = original_inputs.get(col)
            v = pred_input[col].iloc[0]
            comp_rows.append({
                "Feature":   col,
                "Your Input": f"{u:,.2f}" if (u is not None and not pd.isna(u)) else "—",
                "Value Used": f"{v:,.2f}" if isinstance(v, (int, float)) else str(v),
                "Source":    "User provided" if (u is not None and not pd.isna(u))
                             else f"Imputed ({imputation_method})",
            })
        st.dataframe(pd.DataFrame(comp_rows), use_container_width=True,
                     height=min(400, 35*len(feature_cols)))

        # breakdown
        owners_cost, sst_cost, contingency, escalation, grand_total = cost_breakdown(
            base_pred, sst_pct, owners_pct, cont_pct, esc_pct
        )

        result = {
            "Project Name":  project_name,
            "Model Used":    active_model,
            "Base CAPEX":    round(base_pred, 2),
            "Owner's Cost":  owners_cost,
            "SST Cost":      sst_cost,
            "Contingency":   contingency,
            "Escalation":    escalation,
            "Grand Total":   grand_total,
            "Target":        round(base_pred, 2),
        }
        for col in feature_cols:
            result[col] = pred_input[col].iloc[0]

        st.session_state.predictions.setdefault(ds_name_pred, []).append(result)
        toast("Prediction added!")

        st.markdown("##### Results")
        r1, r2, r3, r4, r5 = st.columns(5)
        r1.metric("Base CAPEX",   f"{currency_pred} {base_pred:,.2f}")
        r2.metric("Owner's Cost", f"{currency_pred} {owners_cost:,.2f}")
        r3.metric("SST",          f"{currency_pred} {sst_cost:,.2f}")
        r4.metric("Contingency",  f"{currency_pred} {contingency:,.2f}")
        r5.metric("Grand Total",  f"{currency_pred} {grand_total:,.2f}")

    except Exception as e:
        st.error(f"Prediction failed: {e}")

# ── batch prediction ──────────────────────────────────────────────────────
st.markdown("---")
st.markdown("##### Batch Prediction (Excel)")
excel_file = st.file_uploader("Upload Excel for batch prediction", type=["xlsx"],
                              key=f"batch_excel_{st.session_state.widget_nonce}")

if excel_file:
    file_id = f"{excel_file.name}_{excel_file.size}_{ds_name_pred}"
    if file_id not in st.session_state.processed_excel_files:
        try:
            batch_df     = pd.read_excel(excel_file)
            missing_cols = [c for c in feature_cols if c not in batch_df.columns]
            if missing_cols:
                st.error(f"Missing columns in Excel: {missing_cols}")
            else:
                X_batch = DataPreprocessor.validate_feature_columns(batch_df[feature_cols])
                preds_batch = pipeline.predict(X_batch)
                for i, (_, row) in enumerate(batch_df.iterrows()):
                    bp = float(preds_batch[i])
                    oc, sc, cc, ec, gt = cost_breakdown(bp, sst_pct, owners_pct, cont_pct, esc_pct)
                    r = {
                        "Project Name": str(row.get("Project Name", f"Project {i+1}")),
                        "Model Used":   active_model,
                        "Base CAPEX":   round(bp, 2),
                        "Owner's Cost": oc, "SST Cost": sc,
                        "Contingency":  cc, "Escalation": ec,
                        "Grand Total":  gt, "Target": round(bp, 2),
                    }
                    for feat in feature_cols:
                        r[feat] = row.get(feat, np.nan)
                    st.session_state.predictions.setdefault(ds_name_pred, []).append(r)
                st.session_state.processed_excel_files.add(file_id)
                st.success(f"✅ Processed {len(batch_df)} rows")
        except Exception as e:
            st.error(f"Batch processing failed: {e}")
    else:
        st.info("This file has already been processed.")

# ── results & export ──────────────────────────────────────────────────────
st.divider()
st.markdown('<h3 style="margin-top:0;color:#000;">📄 Results</h3>', unsafe_allow_html=True)

ds_name_res = st.selectbox("Dataset for results",
                           list(st.session_state.datasets.keys()), key="ds_results")
preds = st.session_state.predictions.get(ds_name_res, [])

if preds:
    df_preds = pd.DataFrame(preds)
    display_cols = ["Project Name", "Model Used", "Base CAPEX", "Owner's Cost",
                    "SST Cost", "Contingency", "Escalation", "Grand Total"]
    display_cols = [c for c in display_cols if c in df_preds.columns]
    df_display   = df_preds[display_cols].copy()
    for col in display_cols[2:]:
        df_display[col] = df_display[col].apply(
            lambda x: f"{x:,.2f}" if pd.notna(x) else "")
    st.dataframe(df_display, use_container_width=True, height=300)

    col1, col2 = st.columns(2)
    with col1:
        bio = io.BytesIO()
        df_preds.to_excel(bio, index=False, engine="openpyxl")
        bio.seek(0)
        st.download_button("⬇️ Download Excel", data=bio,
                           file_name=f"{ds_name_res}_predictions.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           key="download_excel_btn")
    with col2:
        st.download_button("⬇️ Download CSV", data=df_preds.to_csv(index=False),
                           file_name=f"{ds_name_res}_predictions.csv",
                           mime="text/csv", key="download_csv_btn")

    if st.button("🗑️ Clear predictions", key="clear_predictions_btn"):
        st.session_state.predictions[ds_name_res] = []
        st.rerun()
else:
    st.info("No predictions yet.")
```

# =============================================================================

# TAB 2 — PROJECT BUILDER

# =============================================================================

with tab_pb:
st.markdown(’<h4 style="margin-top:0;color:#000;">🏗️ Project Builder</h4>’,
unsafe_allow_html=True)
st.caption(“Assemble multi-component CAPEX projects from trained models.”)

```
if not st.session_state.datasets:
    st.info("No datasets loaded. Please load data in the Data tab first.")
    st.stop()

colA, colB = st.columns([2, 1])
with colA:
    new_proj = st.text_input("New Project Name", placeholder="e.g., CAPEX 2026",
                             key="pb_new_project_name")
with colB:
    if new_proj and new_proj not in st.session_state.projects:
        if st.button("Create Project", key="pb_create_project_btn"):
            st.session_state.projects[new_proj] = {
                "components": [],
                "currency":   "",
                "cost_factors": {"sst_pct": 0.0, "owners_pct": 0.0,
                                 "cont_pct": 0.0, "esc_pct": 0.0},
            }
            toast(f"Project '{new_proj}' created.")
            st.rerun()

if not st.session_state.projects:
    st.info("Create a project above, then add components.")
    st.stop()

proj_sel = st.selectbox("Select project", list(st.session_state.projects.keys()),
                        key="pb_project_select")
proj = st.session_state.projects[proj_sel]

st.markdown("##### Project Cost Factors")
cf1, cf2 = st.columns(2)
with cf1:
    proj["cost_factors"]["sst_pct"]    = st.number_input("SST (%)",          0.0, 100.0,
        proj["cost_factors"].get("sst_pct", 0.0),    0.5, key=f"pb_sst_{proj_sel}")
    proj["cost_factors"]["owners_pct"] = st.number_input("Owner's Cost (%)", 0.0, 100.0,
        proj["cost_factors"].get("owners_pct", 0.0), 0.5, key=f"pb_owners_{proj_sel}")
with cf2:
    proj["cost_factors"]["cont_pct"]   = st.number_input("Contingency (%)",  0.0, 100.0,
        proj["cost_factors"].get("cont_pct", 0.0),   0.5, key=f"pb_cont_{proj_sel}")
    proj["cost_factors"]["esc_pct"]    = st.number_input("Escalation (%)",   0.0, 100.0,
        proj["cost_factors"].get("esc_pct", 0.0),    0.5, key=f"pb_esc_{proj_sel}")

st.markdown("##### Add Component")
dataset_for_comp = st.selectbox("Dataset for component",
                                sorted(st.session_state.datasets.keys()),
                                key="pb_dataset_for_component")
df_comp = st.session_state.datasets[dataset_for_comp]

if f"current_pipeline__{dataset_for_comp}" not in st.session_state:
    st.warning(f"Please train a model for '{dataset_for_comp}' in the Data tab first.")
    st.stop()

pipeline_comp = st.session_state[f"current_pipeline__{dataset_for_comp}"]
feat_comp     = st.session_state[f"feature_cols__{dataset_for_comp}"]
curr_comp     = get_currency_symbol(df_comp, df_comp.columns[-1])

# model badge
meta_comp = st.session_state.get(f"trained_model__{dataset_for_comp}", {})
st.info(f"🤖 Model: **{meta_comp.get('best','—')}** | "
        f"R²: **{meta_comp.get('r2', 0):.4f}**")

component_type = st.text_input("Component type",
                               placeholder="e.g., Pipeline, Platform, FPSO",
                               key=f"pb_component_type_{proj_sel}")

comp_inputs = {}
for i in range(0, len(feat_comp), 2):
    cols = st.columns(2)
    for j, feat in enumerate(feat_comp[i:i+2]):
        with cols[j]:
            val = st.text_input(feat, placeholder="Enter value",
                                key=f"pb_{feat}_{proj_sel}_{dataset_for_comp}")
            if val.strip() in ("", "nan"):
                comp_inputs[feat] = np.nan
            else:
                try:    comp_inputs[feat] = float(val)
                except: comp_inputs[feat] = np.nan

if st.button("➕ Add Component", key=f"pb_add_comp_{proj_sel}"):
    if not component_type:
        st.error("Please enter a component type.")
    else:
        try:
            pi = ModelPipeline.prepare_prediction_input(feat_comp, comp_inputs)
            bp = float(pipeline_comp.predict(pi)[0])
            cf = proj["cost_factors"]
            oc, sc, cc, ec, gt = cost_breakdown(
                bp, cf["sst_pct"], cf["owners_pct"], cf["cont_pct"], cf["esc_pct"]
            )
            proj["components"].append({
                "component_type": component_type,
                "dataset":        dataset_for_comp,
                "model_used":     meta_comp.get("best", "—"),
                "prediction":     bp,
                "breakdown":      {
                    "owners_cost":      oc, "sst_cost":        sc,
                    "contingency_cost": cc, "escalation_cost": ec,
                    "grand_total":      gt,
                },
            })
            proj["currency"] = curr_comp
            toast(f"Component '{component_type}' added.")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to add component: {e}")

# ── project overview ──────────────────────────────────────────────────────
st.markdown("---")
comps = proj.get("components", [])
if comps:
    st.markdown("##### Components")
    df_comps = pd.DataFrame([{
        "Component": c["component_type"],
        "Dataset":   c["dataset"],
        "Model":     c.get("model_used", "—"),
        "Base CAPEX":f"{curr_comp} {c['prediction']:,.2f}",
        "Grand Total":f"{curr_comp} {c['breakdown']['grand_total']:,.2f}",
    } for c in comps])
    st.dataframe(df_comps, use_container_width=True)

    totals = project_totals(proj)
    t1, t2, t3 = st.columns(3)
    t1.metric("Total Base CAPEX",  f"{curr_comp} {totals['capex_sum']:,.2f}")
    t2.metric("Total SST",         f"{curr_comp} {totals['sst']:,.2f}")
    t3.metric("Total Grand Total", f"{curr_comp} {totals['grand_total']:,.2f}")

    st.markdown("##### Manage Components")
    for idx, comp in enumerate(comps):
        c1, c2, c3 = st.columns([3, 2, 1])
        c1.write(f"**{comp['component_type']}** — {comp.get('model_used','—')}")
        c1.caption(f"{comp['dataset']} | Base: {curr_comp} {comp['prediction']:,.2f}")
        c2.write(f"Grand Total: {curr_comp} {comp['breakdown']['grand_total']:,.2f}")
        with c3:
            if st.button("🗑️", key=f"del_comp_{proj_sel}_{idx}"):
                comps.pop(idx); st.rerun()

    st.markdown("---")
    proj_json = json.dumps(proj, indent=2, default=float)
    st.download_button("⬇️ Download Project (JSON)", data=proj_json,
                       file_name=f"{proj_sel}.json", mime="application/json",
                       key=f"dl_json_{proj_sel}")
else:
    st.info("No components yet.")

st.markdown("##### Import Project")
up_json = st.file_uploader("Upload project JSON", type=["json"],
                           key=f"import_{proj_sel}")
if up_json:
    try:
        st.session_state.projects[proj_sel] = json.load(up_json)
        toast("Project imported."); st.rerun()
    except Exception as e:
        st.error(f"Import failed: {e}")
```

# =============================================================================

# TAB 3 — MONTE CARLO

# =============================================================================

with tab_mc:
st.markdown(’<h3 style="margin-top:0;color:#000;">🎲 Monte Carlo Analysis</h3>’,
unsafe_allow_html=True)

```
if not st.session_state.projects:
    st.info("Create a project in the Project Builder tab first.")
    st.stop()

proj_sel_mc = st.selectbox("Select project", list(st.session_state.projects.keys()),
                           key="mc_project_select")
proj_mc     = st.session_state.projects[proj_sel_mc]
comps_mc    = proj_mc.get("components", [])

if not comps_mc:
    st.warning("This project has no components.")
    st.stop()

mc1, mc2 = st.columns(2)
with mc1:
    n_sims     = st.number_input("Simulations", 100, 10000, 1000, 100, key="mc_n_sims")
    feat_unc   = st.slider("Feature uncertainty (%)", 0.0, 50.0, 10.0, 1.0, key="mc_feat_unc")
with mc2:
    budget     = st.number_input("Budget threshold (MM USD)", 0.0, value=1000.0,
                                 step=10.0, key="mc_budget")

if st.button("Run Monte Carlo", type="primary", key="mc_run"):
    try:
        with st.spinner("Running simulations…"):
            all_sims = []
            for comp in comps_mc:
                ds = comp["dataset"]
                if f"current_pipeline__{ds}" not in st.session_state:
                    st.warning(f"No trained model for {ds}"); continue
                pipe = st.session_state[f"current_pipeline__{ds}"]
                fcols= st.session_state[f"feature_cols__{ds}"]
                sims = monte_carlo_simulation(pipe, fcols, {},
                                              int(n_sims), feat_unc/100)
                all_sims.append(sims["prediction"].values)

        if all_sims:
            total_sims  = np.sum(all_sims, axis=0)
            p50 = np.percentile(total_sims, 50)
            p80 = np.percentile(total_sims, 80)
            p90 = np.percentile(total_sims, 90)
            exceed_pct  = (total_sims > budget).mean() * 100

            rc1, rc2, rc3, rc4 = st.columns(4)
            rc1.metric("P50", f"${p50:,.0f}M")
            rc2.metric("P80", f"${p80:,.0f}M")
            rc3.metric("P90", f"${p90:,.0f}M")
            rc4.metric(f"P(>${budget:,.0f}M)", f"{exceed_pct:.1f}%")

            fig_mc = px.histogram(x=total_sims, nbins=50,
                                  title="Total Cost Distribution",
                                  labels={"x":"Total Cost (MM USD)","y":"Frequency"},
                                  color_discrete_sequence=["#00A19B"])
            fig_mc.add_vline(x=budget, line_dash="dash", line_color="red",
                             annotation_text=f"Budget: ${budget:,.0f}M")
            st.plotly_chart(fig_mc, use_container_width=True)
        else:
            st.warning("No valid simulations generated.")
    except Exception as e:
        st.error(f"Monte Carlo failed: {e}")
```

# =============================================================================

# TAB 4 — COMPARE PROJECTS

# =============================================================================

with tab_compare:
st.markdown(’<h3 style="margin-top:0;color:#000;">🔀 Compare Projects</h3>’,
unsafe_allow_html=True)

```
if len(st.session_state.projects) < 2:
    st.info("Create at least 2 projects in the Project Builder to compare.")
    st.stop()

proj_names = list(st.session_state.projects.keys())
sel_projs  = st.multiselect("Select projects to compare", proj_names,
                            default=proj_names[:2])

if len(sel_projs) < 2:
    st.warning("Please select at least 2 projects.")
    st.stop()

cmp_data = []
for pn in sel_projs:
    p  = st.session_state.projects[pn]
    t  = project_totals(p)
    cmp_data.append({
        "Project":     pn,
        "Components":  len(p.get("components", [])),
        "Base CAPEX":  t["capex_sum"],
        "SST":         t["sst"],
        "Owner's Cost":t["owners"],
        "Contingency": t["cont"],
        "Escalation":  t["esc"],
        "Grand Total": t["grand_total"],
    })

df_cmp = pd.DataFrame(cmp_data)
st.markdown("##### Comparison Table")
st.dataframe(
    df_cmp.style.format({c: "{:,.2f}" for c in df_cmp.columns if c not in ("Project","Components")}),
    use_container_width=True,
)

viz_type = st.selectbox("Chart type", ["Bar Chart", "Stacked Bar"], key="viz_type")
if viz_type == "Bar Chart":
    fig_cmp = px.bar(df_cmp, x="Project", y="Grand Total",
                     title="Grand Total by Project", text="Grand Total",
                     color_discrete_sequence=["#00A19B"])
    fig_cmp.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
else:
    melt = df_cmp.melt(id_vars=["Project"],
                       value_vars=["Base CAPEX","SST","Owner's Cost","Contingency","Escalation"],
                       var_name="Cost Type", value_name="Amount")
    fig_cmp = px.bar(melt, x="Project", y="Amount", color="Cost Type",
                     title="Cost Breakdown by Project", barmode="stack")
st.plotly_chart(fig_cmp, use_container_width=True)

