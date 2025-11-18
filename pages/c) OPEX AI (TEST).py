# ======================= ABEX AI — PETRONAS Gradient UI (Full App, Chevron Fixed) =======================
# - Full functional logic (Data • Model • Visualization • Predict • Results)
# - PETRONAS animated gradient hero + glowing buttons & tabs
# - Sidebar expanded by default + universal double-chevron (⟪ / ⟫) toggle visibility
# - "Open Enterprise Storage" styled same as other buttons

import io
import json
import zipfile
import requests
import numpy as np
import pandas as pd
import streamlit as st

# ML/Stats
from sklearn.impute import KNNImputer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from scipy.stats import linregress

# Viz
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------------------------------------
st.set_page_config(
    page_title="OPEX AI RT2025",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded",  # expanded by default
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
# GLOBAL CSS (Hero, Buttons, Tabs, Sidebar, Chevron)  --- CHEVRON BLOCK UPDATED
# ---------------------------------------------------------------------------------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [data-testid="stAppViewContainer"] * {{
  font-family: 'Inter', sans-serif;
}}

[data-testid="stAppViewContainer"] {{
  background: {PETRONAS["white"]};
  color: {PETRONAS["black"]};
  padding-top: 0.5rem;
}}

#MainMenu, footer {{ visibility: hidden; }}

/* ---------------- Sidebar ---------------- */
[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, {PETRONAS["teal"]} 0%, {PETRONAS["teal_dark"]} 100%) !important;
  color: #fff !important;
  border-top-right-radius: 16px;
  border-bottom-right-radius: 16px;
  box-shadow: 0 6px 20px rgba(0,0,0,0.15);
}}
[data-testid="stSidebar"] * {{ color: #fff !important; }}

/* ---------------- Double-chevron toggle (always visible, all versions) ---------------- */
[data-testid="collapsedControl"],
div[title="Toggle sidebar"],
button[aria-label="Toggle sidebar"] {{
  position: fixed !important;
  top: 50% !important;
  left: 8px !important;
  transform: translateY(-50%) !important;
  width: 42px !important;
  height: 42px !important;
  background: linear-gradient(145deg, rgba(0,161,155,0.95), rgba(108,77,211,0.9)) !important;
  border-radius: 50% !important;
  border: 1px solid rgba(255,255,255,0.25);
  z-index: 99999 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  cursor: pointer !important;
  transition: all 0.3s ease-in-out;
  box-shadow: 0 0 12px rgba(0,161,155,0.7);
  opacity: 1 !important;
  visibility: visible !important;
}}
[data-testid="collapsedControl"] * ,
div[title="Toggle sidebar"] *,
button[aria-label="Toggle sidebar"] * {{
  color: transparent !important;
  font-size: 0 !important;
}}
/* Default (expanded) */
[data-testid="collapsedControl"]::before,
div[title="Toggle sidebar"]::before,
button[aria-label="Toggle sidebar"]::before {{
  content: "⟪" !important;
  font-size: 20px !important;
  color: #fff !important;
  text-shadow: 0 0 8px rgba(0,161,155,0.9);
  font-weight: bold !important;
}}
/* Collapsed (when aria-expanded=false) */
[data-testid="collapsedControl"][aria-expanded="false"]::before,
div[title="Toggle sidebar"][aria-expanded="false"]::before,
button[aria-label="Toggle sidebar"][aria-expanded="false"]::before {{
  content: "⟫" !important;
  text-shadow: 0 0 8px rgba(108,77,211,0.9);
}}
/* Hover pulse */
[data-testid="collapsedControl"]:hover,
div[title="Toggle sidebar"]:hover,
button[aria-label="Toggle sidebar"]:hover {{
  transform: translateY(-50%) scale(1.1);
  box-shadow: 0 0 18px rgba(108,77,211,0.8);
}}

/* ---------------- Hero Header ---------------- */
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

/* ---------------- Buttons ---------------- */
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

/* ---------------- Tabs ---------------- */
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
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------------------
# HERO HEADER
# ---------------------------------------------------------------------------------------
st.markdown("""
<div class="petronas-hero">
  <h1>ABEX AI RT2025</h1>
  <p>Data-driven cost prediction •TEST•</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

APPROVED_EMAILS = st.secrets.get("emails", [])
correct_password = st.secrets.get("password", None)

if not st.session_state.authenticated:
    with st.form("login_form"):
        st.markdown("#### 🔐 Access Required", unsafe_allow_html=True)
        email = st.text_input("Email Address")
        password = st.text_input("Access Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if email in APPROVED_EMAILS and password == correct_password:
                st.session_state.authenticated = True
                st.success("✅ Access granted.")
                st.rerun()
            else:
                st.error("❌ Invalid email or password.")
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

# ---------------------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------------------
def toast(msg, icon="✅"):
    try:
        st.toast(f"{icon} {msg}")
    except Exception:
        st.success(msg if icon == "✅" else msg)

def human_format(num, pos=None):
    try:
        num = float(num)
    except Exception:
        return str(num)
    if num >= 1e9: return f'{num/1e9:.1f}B'
    if num >= 1e6: return f'{num/1e6:.1f}M'
    if num >= 1e3: return f'{num/1e3:.1f}K'
    return f'{num:.0f}'

def format_with_commas(num):
    try:
        return f"{float(num):,.2f}"
    except Exception:
        return str(num)

def get_currency_symbol(df: pd.DataFrame):
    for col in df.columns:
        uc = col.upper()
        if "RM" in uc: return "RM"
        if "USD" in uc or "$" in col: return "USD"
        if "€" in col: return "€"
        if "£" in col: return "£"
    try:
        sample_vals = df.iloc[:20].astype(str).values.flatten().tolist()
        if any("RM" in v.upper() for v in sample_vals): return "RM"
        if any("€" in v for v in sample_vals): return "€"
        if any("£" in v for v in sample_vals): return "£"
        if any("$" in v for v in sample_vals): return "USD"
    except Exception:
        pass
    return ""

def cost_breakdown(base_pred: float, eprr: dict, sst_pct: float, owners_pct: float, cont_pct: float, esc_pct: float):
    owners_cost      = round(base_pred * (owners_pct / 100.0), 2)
    sst_cost         = round(base_pred * (sst_pct    / 100.0), 2)
    contingency_cost = round((base_pred + owners_cost) * (cont_pct / 100.0), 2)
    escalation_cost  = round((base_pred + owners_cost) * (esc_pct / 100.0), 2)
    eprr_costs       = {k: round(base_pred * (v / 100.0), 2) for k, v in (eprr or {}).items()}
    grand_total      = round(base_pred + owners_cost + contingency_cost + escalation_cost, 2)
    return owners_cost, sst_cost, contingency_cost, escalation_cost, eprr_costs, grand_total

# Remote data manifest (GitHub)
GITHUB_USER = "Hafizuddin-Abd-Rahman-Dev-Upstream"
REPO_NAME   = "Cost-Predictor"
BRANCH      = "main"
DATA_FOLDER = "pages/data_ABEX"

@st.cache_data(ttl=600)
def list_csvs_from_manifest(folder_path: str):
    manifest_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{folder_path}/files.json"
    try:
        res = requests.get(manifest_url, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"Failed to load CSV manifest: {e}")
        return []

def evaluate_model(X, y, test_size=0.2):
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=test_size, random_state=42)
    scaler = MinMaxScaler().fit(Xtr)
    model = RandomForestRegressor(random_state=42).fit(scaler.transform(Xtr), ytr)
    yhat  = model.predict(scaler.transform(Xte))
    rmse = float(np.sqrt(mean_squared_error(yte, yhat)))
    r2   = float(r2_score(yte, yhat))
    return dict(model=model, scaler=scaler, rmse=rmse, r2=r2)

def single_prediction(X, y, payload: dict):
    scaler = MinMaxScaler().fit(X)
    model  = RandomForestRegressor(random_state=42).fit(scaler.transform(X), y)
    cols = list(X.columns)
    row = {c: np.nan for c in cols}
    for c, v in payload.items():
        try:
            row[c] = float(v) if (v is not None and str(v).strip() != "") else np.nan
        except Exception:
            row[c] = np.nan
    df_in = pd.DataFrame([row], columns=cols)
    pred = float(model.predict(scaler.transform(df_in))[0])
    return pred

# ---------------------------------------------------------------------------------------
# NAV ROW
# ---------------------------------------------------------------------------------------
nav_c1, nav_c2, nav_c3 = st.columns([1, 1, 1])
with nav_c1:
    st.button("📤 Upload Data", key="upload_top")
with nav_c2:
    if st.button("📈 New Prediction", key="predict_top"):
        # Clear only predictions, keep datasets
        for ds in list(st.session_state.predictions.keys()):
            st.session_state.predictions[ds] = []
        st.session_state.processed_excel_files = set()
        st.session_state._last_metrics = None
        # Clear any Predict-tab inputs
        for k in list(st.session_state.keys()):
            if str(k).startswith("in_"):
                del st.session_state[k]
        toast("Ready for a new prediction.")
        st.rerun()
with nav_c3:
    st.button("📥 Download All", disabled=True, help="Use the Results tab once you have predictions.")

# ---------------------------------------------------------------------------------------
# TABS
# ---------------------------------------------------------------------------------------
tab_data, tab_model, tab_viz, tab_predict, tab_results = st.tabs(
    ["📁 Data", "⚙️ Model", "📈 Visualization", "🎯 Predict", "📄 Results"]
)

# ===================================== DATA TAB ========================================
with tab_data:
    st.markdown('<h4 style="margin:0;color:#000;">Data Sources</h4><p></p>', unsafe_allow_html=True)
    c1, c2 = st.columns([1.2, 1])
    with c1:
        data_source = st.radio("Choose data source", ["Upload CSV", "Load from Server"], horizontal=True)
    with c2:
        st.caption("Enterprise Storage (SharePoint)")
        data_link = (
            "https://petronas.sharepoint.com/sites/ecm_ups_coe/confidential/DFE%20Cost%20Engineering/Forms/"
            "AllItems.aspx?id=%2Fsites%2Fecm%5Fups%5Fcoe%2Fconfidential%2FDFE%20Cost%20Engineering%2F2%2ETemplate%20Tools%2F"
            "Cost%20Predictor%2FDatabase%2FABEX%20%28DDRR%29%20%2D%20RT%20Q1%202025&viewid=25092e6d%2D373d%2D41fe%2D8f6f%2D486cd8cdd5b8"
        )
        # Styled like other buttons (consistency)
        st.markdown(
            f'<a href="{data_link}" target="_blank" rel="noopener" class="petronas-button">Open Enterprise Storage</a>',
            unsafe_allow_html=True
        )

    uploaded_files = []
    if data_source == "Upload CSV":
        uploaded_files = st.file_uploader(
            "Upload CSV files (max 200MB)", type="csv", accept_multiple_files=True
        )
    else:
        github_csvs = list_csvs_from_manifest(DATA_FOLDER)
        if github_csvs:
            selected_file = st.selectbox("Choose CSV from GitHub", github_csvs)
            if st.button("Load selected CSV"):
                raw_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{DATA_FOLDER}/{selected_file}"
                try:
                    df = pd.read_csv(raw_url)
                    fake = type("FakeUpload", (), {"name": selected_file})
                    uploaded_files = [fake]
                    st.session_state.datasets[selected_file] = df
                    st.session_state.predictions.setdefault(selected_file, [])
                    toast(f"Loaded from GitHub: {selected_file}")
                except Exception as e:
                    st.error(f"Error loading CSV: {e}")
        else:
            st.info("No CSV files found in GitHub folder.")

    # Ingest uploads
    if uploaded_files:
        for up in uploaded_files:
            if up.name not in st.session_state.datasets:
                if hasattr(up, "read"):
                    df = pd.read_csv(up)
                else:
                    df = st.session_state.datasets.get(up.name, None)
                if df is not None:
                    st.session_state.datasets[up.name] = df
                    st.session_state.predictions.setdefault(up.name, [])
        toast("Dataset(s) added.")

    st.divider()
    cA, cB, cC = st.columns([1, 1, 2])
    with cA:
        if st.button("🧹 Clear all predictions"):
            st.session_state.predictions = {k: [] for k in st.session_state.predictions.keys()}
            toast("All predictions cleared.", "🧹")
    with cB:
        if st.button("🧺 Clear processed files history"):
            st.session_state.processed_excel_files = set()
            toast("Processed files history cleared.", "🧺")
    with cC:
        if st.button("🔁 Refresh server manifest"):
            list_csvs_from_manifest.clear()
            toast("Server manifest refreshed.", "🔁")

    st.divider()

    # Dataset snapshot
    if st.session_state.datasets:
        ds_name = st.selectbox("Active dataset", list(st.session_state.datasets.keys()))
        df = st.session_state.datasets[ds_name]
        currency = get_currency_symbol(df)
        colA, colB, colC = st.columns([1, 1, 1])
        with colA: st.metric("Rows", f"{df.shape[0]:,}")
        with colB: st.metric("Columns", f"{df.shape[1]:,}")
        with colC: st.metric("Currency", f"{currency or '—'}")
        with st.expander("Preview (first 10 rows)", expanded=False):
            st.dataframe(df.head(10), use_container_width=True)
    else:
        st.info("Upload or load a dataset to proceed.")

# ===================================== MODEL TAB =======================================
with tab_model:
    if not st.session_state.datasets:
        st.info("No dataset. Go to **Data** tab to upload or load.")
    else:
        ds_name = st.selectbox("Dataset for model training", list(st.session_state.datasets.keys()), key="ds_model")
        df = st.session_state.datasets[ds_name]

        with st.spinner("Imputing & preparing..."):
            imputed = pd.DataFrame(KNNImputer(n_neighbors=5).fit_transform(df), columns=df.columns)
            X = imputed.iloc[:, :-1]
            y = imputed.iloc[:, -1]
            target_column = y.name

        st.markdown('<h4 style="margin:0;color:#000;">Train & Evaluate</h4><p>Step 2</p>', unsafe_allow_html=True)
        c1, c2 = st.columns([1, 3])
        with c1:
            test_size = st.slider("Test size", 0.1, 0.5, 0.2, 0.05, help="Fraction of data used for testing")
            run = st.button("Run training")
        with c2:
            st.caption("Random Forest on min-max scaled features; reproducible with random_state=42.")
            st.write("")

        if run:
            with st.spinner("Training model..."):
                metrics = evaluate_model(X, y, test_size=test_size)
            c1, c2 = st.columns(2)
            with c1: st.metric("RMSE", f"{metrics['rmse']:,.2f}")
            with c2: st.metric("R²", f"{metrics['r2']:.3f}")
            st.session_state._last_metrics = metrics
            toast("Training complete.")

# ================================== VISUALIZATION TAB =================================
with tab_viz:
    if not st.session_state.datasets:
        st.info("No dataset. Go to **Data** tab to upload or load.")
    else:
        ds_name = st.selectbox("Dataset for visualization", list(st.session_state.datasets.keys()), key="ds_viz")
        df = st.session_state.datasets[ds_name]
        imputed = pd.DataFrame(KNNImputer(n_neighbors=5).fit_transform(df), columns=df.columns)
        X = imputed.iloc[:, :-1]
        y = imputed.iloc[:, -1]
        target_column = y.name

        # Correlation Matrix
        st.markdown('<h4 style="margin:0;color:#000;">Correlation Matrix</h4><p>Exploration</p>', unsafe_allow_html=True)
        corr = imputed.corr(numeric_only=True)
        fig = px.imshow(
            corr, text_auto=".2f", aspect="auto",
            color_continuous_scale="RdBu_r", zmin=-1, zmax=1
        )
        fig.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor=PETRONAS["white"], plot_bgcolor=PETRONAS["white"],
            font=dict(color=PETRONAS["black"]),
            xaxis=dict(color=PETRONAS["black"]), yaxis=dict(color=PETRONAS["black"])
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # Feature Importance
        st.markdown('<h4 style="margin:0;color:#000;">Feature Importance</h4><p>Model</p>', unsafe_allow_html=True)
        scaler = MinMaxScaler().fit(X)
        model = RandomForestRegressor(random_state=42).fit(scaler.transform(X), y)
        importances = model.feature_importances_
        fi = pd.DataFrame({"feature": X.columns, "importance": importances}).sort_values("importance", ascending=True)
        fig2 = go.Figure(go.Bar(
            x=fi["importance"], y=fi["feature"], orientation='h',
            marker_color=PETRONAS["teal"]
        ))
        fig2.update_layout(
            xaxis_title="Importance", yaxis_title="Feature",
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor=PETRONAS["white"], plot_bgcolor=PETRONAS["white"],
            font=dict(color=PETRONAS["black"]),
            xaxis=dict(color=PETRONAS["black"]), yaxis=dict(color=PETRONAS["black"])
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # Cost Curve (linregress)
        st.markdown('<h4 style="margin:0;color:#000;">Cost Curve</h4><p>Trend</p>', unsafe_allow_html=True)
        feat = st.selectbox("Select feature for cost curve", X.columns)
        x_vals = imputed[feat].values
        y_vals = y.values
        mask = (~np.isnan(x_vals)) & (~np.isnan(y_vals))

        scatter_df = pd.DataFrame({feat: x_vals[mask], target_column: y_vals[mask]})
        fig3 = px.scatter(scatter_df, x=feat, y=target_column, opacity=0.65)
        fig3.update_traces(marker=dict(color=PETRONAS["teal"]))

        if mask.sum() >= 2 and np.unique(x_vals[mask]).size >= 2:
            xv = scatter_df[feat].to_numpy(dtype=float)
            yv = scatter_df[target_column].to_numpy(dtype=float)
            slope, intercept, r_value, p_value, std_err = linregress(xv, yv)
            x_line = np.linspace(xv.min(), xv.max(), 100)
            y_line = slope * x_line + intercept
            fig3.add_trace(go.Scatter(
                x=x_line, y=y_line, mode="lines",
                name=f"Fit: y={slope:.2f}x+{intercept:.2f} (R²={r_value**2:.3f})",
                line=dict(color=PETRONAS["purple"])
            ))
        else:
            st.warning("Not enough valid/variable data to compute regression.")

        fig3.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor=PETRONAS["white"], plot_bgcolor=PETRONAS["white"],
            font=dict(color=PETRONAS["black"]),
            xaxis=dict(color=PETRONAS["black"]), yaxis=dict(color=PETRONAS["black"])
        )
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

# ===================================== PREDICT TAB =====================================
with tab_predict:
    if not st.session_state.datasets:
        st.info("No dataset. Go to **Data** tab to upload or load.")
    else:
        ds_name = st.selectbox("Dataset for prediction", list(st.session_state.datasets.keys()), key="ds_pred")
        df = st.session_state.datasets[ds_name]
        currency = get_currency_symbol(df)

        # Build model on full data (for single predictions)
        imputed = pd.DataFrame(KNNImputer(n_neighbors=5).fit_transform(df), columns=df.columns)
        X, y = imputed.iloc[:, :-1], imputed.iloc[:, -1]
        target_column = y.name

        # Config card
        st.markdown('<h4 style="margin:0;color:#000;">Configuration (EPRR • Taxes • Owner • Risk)</h4><p>Step 3</p>', unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("**EPRR Breakdown (%)**")
            eng  = st.slider("Engineering", 0, 100, 12)
            prep = st.slider("Preparation", 0, 100, 7)
            remv = st.slider("Removal", 0, 100, 54)
            remd = st.slider("Remediation", 0, 100, 27)
        with c2:
            st.markdown("**Financial (%)**")
            sst_pct    = st.slider("SST", 0, 100, 0)
            owners_pct = st.slider("Owner's Cost", 0, 100, 0)
            cont_pct   = st.slider("Contingency", 0, 100, 0)
            esc_pct    = st.slider("Escalation & Inflation", 0, 100, 0)

        eprr = {"Engineering": eng, "Preparation": prep, "Removal": remv, "Remediation": remd}
        eprr_total = sum(eprr.values())
        if abs(eprr_total - 100) > 1e-6 and eprr_total > 0:
            st.warning(f"EPRR total is {eprr_total}%. Consider normalizing to 100% for reporting consistency.")

        # Single prediction inputs
        st.markdown('<h4 style="margin:0;color:#000;">Predict (Single)</h4><p>Step 4</p>', unsafe_allow_html=True)
        project_name = st.text_input("Project Name", placeholder="e.g., Offshore Pipeline Replacement 2025")
        st.caption("Provide feature values (leave blank for NaN).")

        cols_per_row = 3
        new_data = {}
        cols = list(X.columns)
        rows = (len(cols) + cols_per_row - 1) // cols_per_row
        for r in range(rows):
            row_cols = st.columns(cols_per_row)
            for i in range(cols_per_row):
                idx = r * cols_per_row + i
                if idx < len(cols):
                    col_name = cols[idx]
                    with row_cols[i]:
                        val = st.text_input(col_name, key=f"in_{col_name}")
                        new_data[col_name] = val

        if st.button("Run Prediction"):
            pred = single_prediction(X, y, new_data)
            owners_cost, sst_cost, contingency_cost, escalation_cost, eprr_costs, grand_total = cost_breakdown(
                pred, eprr, sst_pct, owners_pct, cont_pct, esc_pct
            )

            # Store
            result = {"Project Name": project_name, **{c: new_data[c] for c in cols}, target_column: round(pred, 2)}
            for k, v in eprr_costs.items(): result[f"{k} Cost"] = v
            result["SST Cost"] = sst_cost
            result["Owner's Cost"] = owners_cost
            result["Cost Contingency"] = contingency_cost
            result["Escalation & Inflation"] = escalation_cost
            result["Grand Total"] = grand_total
            st.session_state.predictions.setdefault(ds_name, []).append(result)
            toast("Prediction added to Results.")

            # Summary metrics
            cA, cB, cC, cD, cE = st.columns(5)
            with cA: st.metric("Predicted", f"{currency} {pred:,.2f}")
            with cB: st.metric("Owner's", f"{currency} {owners_cost:,.2f}")
            with cC: st.metric("Contingency", f"{currency} {contingency_cost:,.2f}")
            with cD: st.metric("Escalation", f"{currency} {escalation_cost:,.2f}")
            with cE: st.metric("Grand Total", f"{currency} {grand_total:,.2f}")

        # Batch (Excel)
        st.markdown('<h4 style="margin:0;color:#000;">Batch (Excel)</h4>', unsafe_allow_html=True)
        xls = st.file_uploader("Upload Excel for batch prediction", type=["xlsx"])
        if xls:
            file_id = f"{xls.name}_{xls.size}_{ds_name}"
            if file_id not in st.session_state.processed_excel_files:
                batch_df = pd.read_excel(xls)
                missing = [c for c in X.columns if c not in batch_df.columns]
                if missing:
                    st.error(f"Missing required columns in Excel: {missing}")
                else:
                    scaler_b = MinMaxScaler().fit(X)
                    model_b  = RandomForestRegressor(random_state=42).fit(scaler_b.transform(X), y)
                    preds = model_b.predict(scaler_b.transform(batch_df[X.columns]))
                    batch_df[target_column] = preds

                    for i, row in batch_df.iterrows():
                        name = row.get("Project Name", f"Project {i+1}")
                        entry = {"Project Name": name}
                        entry.update(row[X.columns].to_dict())
                        entry[target_column] = round(float(preds[i]), 2)
                        owners_cost, sst_cost, contingency_cost, escalation_cost, eprr_costs, grand_total = cost_breakdown(
                            float(preds[i]), eprr, sst_pct, owners_pct, cont_pct, esc_pct
                        )
                        for k, v in eprr_costs.items(): entry[f"{k} Cost"] = v
                        entry["SST Cost"] = sst_cost
                        entry["Owner's Cost"] = owners_cost
                        entry["Cost Contingency"] = contingency_cost
                        entry["Escalation & Inflation"] = escalation_cost
                        entry["Grand Total"] = grand_total
                        st.session_state.predictions.setdefault(ds_name, []).append(entry)

                    st.session_state.processed_excel_files.add(file_id)
                    toast("Batch prediction complete.")

# ===================================== RESULTS TAB =====================================
with tab_results:
    if not st.session_state.datasets:
        st.info("No dataset. Go to **Data** tab to upload or load.")
    else:
        ds_name = st.selectbox("Dataset", list(st.session_state.datasets.keys()), key="ds_results")
        preds = st.session_state.predictions.get(ds_name, [])

        st.markdown(f'<h4 style="margin:0;color:#000;">Project Entries</h4><p>{len(preds)} saved</p>', unsafe_allow_html=True)
        if preds:
            # delete all
            if st.button("🗑️ Delete all entries"):
                st.session_state.predictions[ds_name] = []
                to_remove = {fid for fid in st.session_state.processed_excel_files if fid.endswith(ds_name)}
                for fid in to_remove:
                    st.session_state.processed_excel_files.remove(fid)
                toast("All entries removed.", "🗑️")
                st.rerun()

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        st.markdown('<h4 style="margin:0;color:#000;">Summary Table & Export</h4><p>Download</p>', unsafe_allow_html=True)
        if preds:
            df_preds = pd.DataFrame(preds)
            df_disp = df_preds.copy()
            num_cols = df_disp.select_dtypes(include=[np.number]).columns
            for col in num_cols:
                df_disp[col] = df_disp[col].apply(lambda x: format_with_commas(x))
            st.dataframe(df_disp, use_container_width=True, height=420)

            # Build ZIP with predictions.xlsx + metrics.json
            # Excel
            bio_xlsx = io.BytesIO()
            df_preds.to_excel(bio_xlsx, index=False, engine="openpyxl")
            bio_xlsx.seek(0)
            # Metrics JSON
            metrics = st.session_state._last_metrics
            metrics_json = json.dumps(metrics if metrics else {"info": "No metrics"}, indent=2, default=float)
            # ZIP
            zip_bio = io.BytesIO()
            with zipfile.ZipFile(zip_bio, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(f"{ds_name}_predictions.xlsx", bio_xlsx.getvalue())
                zf.writestr(f"{ds_name}_metrics.json", metrics_json)
            zip_bio.seek(0)

            st.download_button(
                "⬇️ Download All (ZIP)",
                data=zip_bio.getvalue(),
                file_name=f"{ds_name}_abex_all.zip",
                mime="application/zip",
            )
        else:
            st.info("No data to export yet.")
