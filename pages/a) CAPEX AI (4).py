# pages/a) CAPEX AI.py
# CAPEX AI – Datasets & Models | Project Builder | Compare Projects
# This page assumes Home.py sets st.session_state.authenticated = True after login.

import io
import json
import re
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
from matplotlib.ticker import FuncFormatter

# --- New / updated imports for robust modeling ---
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.compose import TransformedTargetRegressor
from sklearn.model_selection import (
    train_test_split, KFold, cross_val_score
)
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
from sklearn.experimental import enable_hist_gradient_boosting  # noqa: F401
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.dummy import DummyRegressor
from sklearn.inspection import permutation_importance

import requests

# ------------------------- Page Config -------------------------
st.set_page_config(page_title="CAPEX AI – Project Workspace", page_icon="💲", layout="wide")

# ------------------------- Auth check -------------------------
# Expect Home.py to set this. If you don't use auth, set it True once there.
if st.session_state.get("authenticated", True) is False:
    st.info("Please login from **Home** to access this page.")
    st.stop()

# ------------------------- Repo config -------------------------
GITHUB_USER = "Hafizuddin-Abd-Rahman-Dev-Upstream"
REPO_NAME = "Cost-Predictor"
BRANCH = "main"
DATA_FOLDER = "pages/data_CAPEX"

@st.cache_data(ttl=600)
def list_csvs_from_manifest(folder_path: str):
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{folder_path}/files.json"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Failed to load CSV manifest: {e}")
        return []

# ------------------------- Utilities -------------------------
def human_format(num, pos=None):
    try:
        num = float(num)
    except Exception:
        return str(num)
    if num >= 1e9:
        return f'{num/1e9:.1f}B'
    elif num >= 1e6:
        return f'{num/1e6:.1f}M'
    elif num >= 1e3:
        return f'{num/1e3:.1f}K'
    else:
        return f'{num:.0f}'

def format_with_commas(num):
    try:
        return f"{float(num):,.2f}"
    except Exception:
        return str(num)

def get_currency_symbol(df: pd.DataFrame) -> str:
    symbols = ["$", "€", "£", "RM", "IDR", "SGD"]
    for col in df.columns:
        u = str(col).upper()
        for sym in symbols:
            if sym in u:
                return sym
    return ""

def make_widget_key(*parts):
    """
    Build a unique, Streamlit-safe widget key from arbitrary parts (deterministic).
    - Adds a tab/context prefix (e.g., 'TAB1', 'TAB2').
    - Normalizes spaces and special chars.
    """
    cleaned = []
    for p in parts:
        s = str(p).strip()
        s = re.sub(r"\s+", "_", s)  # normalize spaces
        s = re.sub(r"[^\w\-\.:]", "_", s)  # keep letters, numbers, _, -, ., :
        cleaned.append(s)
    return ":".join(cleaned)

def download_all_predictions():
    preds_all = st.session_state.get("predictions", {})
    if not preds_all or all(len(v) == 0 for v in preds_all.values()):
        st.sidebar.error("No predictions available to download")
        return

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary_data = []
        for dataset_name, preds in preds_all.items():
            if not preds:
                continue
            for pred in preds:
                row = pred.copy()
                row["Dataset"] = dataset_name.replace(".csv", "")
                summary_data.append(row)
        if summary_data:
            pd.DataFrame(summary_data).to_excel(writer, sheet_name="All Predictions", index=False)
        for dataset_name, preds in preds_all.items():
            if preds:
                sheet = dataset_name.replace(".csv", "")[:31]
                pd.DataFrame(preds).to_excel(writer, sheet_name=sheet, index=False)
    output.seek(0)
    st.sidebar.download_button(
        "📥 Download All Predictions",
        data=output,
        file_name="All_Predictions.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

# ------------------------- VISUAL HELPERS -------------------------
def _label_bars(ax, fmt="{:,.0f}"):
    for p in ax.patches:
        if p.get_height() > 0:
            ax.annotate(fmt.format(p.get_height()),
                        (p.get_x() + p.get_width()/2, p.get_y() + p.get_height()/2),
                        ha='center', va='center', fontsize=9, color='white')

def plot_component_stack(dfc_stack, title="Component Composition (Grand Total)", currency=""):
    """
    dfc_stack columns:
    Component, CAPEX, Owners, Contingency, Escalation, PreDev
    """
    cats = ["CAPEX", "Owners", "Contingency", "Escalation", "PreDev"]
    colors = ["#2E86AB", "#6C757D", "#C0392B", "#17A589", "#9B59B6"]
    x = np.arange(len(dfc_stack["Component"]))
    fig, ax = plt.subplots(figsize=(min(12, 1.2*len(x)+6), 6))
    bottom = np.zeros(len(x))
    for c, col in zip(colors, cats):
        vals = dfc_stack[col].values
        ax.bar(x, vals, bottom=bottom, color=c, label=col)
        bottom += vals
    ax.set_xticks(x); ax.set_xticklabels(dfc_stack["Component"], rotation=30, ha="right")
    ax.set_ylabel(f"Cost {currency}".strip())
    ax.set_title(title)
    ax.legend(ncols=5, fontsize=9, loc="upper center", bbox_to_anchor=(0.5, 1.15))
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    return fig

def plot_component_pie(labels, sizes, title="Cost Share by Component", currency=""):
    fig, ax = plt.subplots(figsize=(7, 7))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct=lambda p: f"{p:.1f}%" if p > 0 else "",
        startangle=140, pctdistance=0.8, textprops={"fontsize": 10}
    )
    centre_circle = plt.Circle((0,0), 0.60, fc='white')
    fig.gca().add_artist(centre_circle)
    ax.set_title(title)
    fig.tight_layout()
    return fig

def plot_epcic_stack(epcic_df, title="EPCIC Breakdown per Component", currency=""):
    """
    epcic_df columns:
    Component, Engineering, Procurement, Construction, Installation, Commissioning
    """
    phases = ["Engineering","Procurement","Construction","Installation","Commissioning"]
    colors = ["#1F77B4","#FF7F0E","#2CA02C","#D62728","#9467BD"]
    x = np.arange(len(epcic_df["Component"]))
    fig, ax = plt.subplots(figsize=(min(12, 1.2*len(x)+6), 6))
    bottom = np.zeros(len(x))
    for c, col in zip(colors, phases):
        vals = epcic_df[col].values
        ax.bar(x, vals, bottom=bottom, color=c, label=col)
        bottom += vals
    ax.set_xticks(x); ax.set_xticklabels(epcic_df["Component"], rotation=30, ha="right")
    ax.set_ylabel(f"Cost {currency}".strip())
    ax.set_title(title)
    ax.legend(ncols=5, fontsize=9, loc="upper center", bbox_to_anchor=(0.5, 1.15))
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    return fig

def plot_project_totals_bar(dft, title="Project Grand Totals", currency=""):
    """
    dft: index=Project, column 'Grand Total'
    """
    fig, ax = plt.subplots(figsize=(min(12, 1.2*len(dft)+6), 5))
    bars = ax.bar(dft.index, dft["Grand Total"], color="#2E86AB")
    ax.set_title(title)
    ax.set_ylabel(f"Cost {currency}".strip())
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.tick_params(axis='x', rotation=25)
    for b in bars:
        ax.annotate(f"{b.get_height():,.0f}", (b.get_x()+b.get_width()/2, b.get_height()),
                    ha='center', va='bottom', fontsize=9, rotation=0)
    fig.tight_layout()
    return fig

def plot_projects_composition_stack(comp_df, title="Project Composition (Grand Total)", currency=""):
    """
    comp_df columns: Project, CAPEX, Owners, Contingency, Escalation, PreDev
    """
    cats = ["CAPEX","Owners","Contingency","Escalation","PreDev"]
    colors = ["#2E86AB","#6C757D","#C0392B","#17A589","#9B59B6"]
    x = np.arange(len(comp_df["Project"]))
    fig, ax = plt.subplots(figsize=(min(12, 1.2*len(x)+6), 6))
    bottom = np.zeros(len(x))
    for c, col in zip(colors, cats):
        vals = comp_df[col].values
        ax.bar(x, vals, bottom=bottom, color=c, label=col)
        bottom += vals
    ax.set_xticks(x); ax.set_xticklabels(comp_df["Project"], rotation=25, ha="right")
    ax.set_ylabel(f"Cost {currency}".strip())
    ax.set_title(title)
    ax.legend(ncols=5, fontsize=9, loc="upper center", bbox_to_anchor=(0.5, 1.15))
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    return fig

def plot_two_project_waterfall(delta_dict, title="Δ Grand Total Waterfall", currency=""):
    """
    delta_dict keys: ['CAPEX','Owners','Contingency','Escalation','PreDev'] with signed deltas (P2-P1)
    """
    cats = ["CAPEX","Owners","Contingency","Escalation","PreDev"]
    vals = [delta_dict.get(k,0.0) for k in cats]
    cum = np.cumsum([0]+vals[:-1])
    colors = ["#2E86AB" if v>=0 else "#C0392B" for v in vals]
    fig, ax = plt.subplots(figsize=(8, 5))
    for i,(v, base, c) in enumerate(zip(vals, cum, colors)):
        ax.bar(i, v, bottom=base, color=c)
        ax.annotate(f"{v:+,.0f}", (i, base + v/2), ha="center", va="center", color="white", fontsize=9)
    ax.set_xticks(range(len(cats))); ax.set_xticklabels(cats, rotation=0)
    total = sum(vals)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title(title + f" (Total Δ = {total:+,.0f} {currency})".strip())
    ax.set_ylabel(f"Δ Cost {currency}".strip())
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    return fig

# ------------------------- Modeling helpers -------------------------
def _build_estimator(model_choice: str, random_state: int = 42):
    if model_choice == "RandomForest":
        return RandomForestRegressor(
            n_estimators=500, max_depth=None, min_samples_leaf=1,
            n_jobs=-1, random_state=random_state
        )
    elif model_choice == "ExtraTrees":
        return ExtraTreesRegressor(
            n_estimators=500, max_depth=None, min_samples_leaf=1,
            n_jobs=-1, random_state=random_state
        )
    else:  # HistGradientBoosting
        return HistGradientBoostingRegressor(
            learning_rate=0.05, max_depth=None, max_iter=500,
            random_state=random_state
        )

def train_model_bundle_from_df(
    df: pd.DataFrame,
    target_col: str,
    test_size: float = 0.2,
    random_state: int = 42,
    model_choice: str = "HistGradientBoosting",
    use_log_target: bool = True,
):
    # Split X, y
    y = df[target_col].astype(float)
    X = df.drop(columns=[target_col])

    # Numeric-only pipeline (extend with categorical support if needed)
    num_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    if len(num_cols) == 0:
        raise ValueError("No numeric features found. Please ensure your dataset has numeric predictors.")
    X = X[num_cols]  # drop non-numeric until OneHotEncoder is added

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    # Pipeline: impute -> model (no scaler for trees)
    base_model = _build_estimator(model_choice, random_state)
    pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),  # fitted only on train by pipeline
        ("model", base_model),
    ])

    # Optional log transform on target
    if use_log_target:
        model = TransformedTargetRegressor(
            regressor=pipe, func=np.log1p, inverse_func=np.expm1
        )
    else:
        model = pipe

    # Cross-validation (on training set only)
    cv = KFold(n_splits=5, shuffle=True, random_state=random_state)
    cv_r2 = cross_val_score(model, X_train, y_train, scoring="r2", cv=cv)
    cv_rmse = np.sqrt(-cross_val_score(model, X_train, y_train, scoring="neg_mean_squared_error", cv=cv))

    # Fit and evaluate on holdout
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = float(r2_score(y_test, y_pred))

    # Baseline check
    dummy = DummyRegressor(strategy="mean")
    dummy.fit(X_train, y_train)
    y_dummy = dummy.predict(X_test)
    r2_dummy = float(r2_score(y_test, y_dummy))

    # Permutation importance (model-agnostic, on holdout)
    try:
        # For TransformedTargetRegressor, we permute on the underlying pipeline's "model"
        fitted_estimator = model.regressor_ if isinstance(model, TransformedTargetRegressor) else model
        # Use imputed X_test for importances
        X_test_imputed = fitted_estimator.named_steps["imputer"].transform(X_test)
        importances = permutation_importance(
            fitted_estimator.named_steps["model"],
            X_test_imputed,
            y_test if not isinstance(model, TransformedTargetRegressor) else model.transform(y_test),
            n_repeats=10,
            random_state=random_state,
            scoring="r2"
        )
        fi = pd.DataFrame({
            "feature": num_cols,
            "importance_mean": importances.importances_mean,
            "importance_std": importances.importances_std
        }).sort_values("importance_mean", ascending=False)
    except Exception:
        fi = pd.DataFrame({"feature": num_cols, "importance_mean": 0.0, "importance_std": 0.0})

    bundle = {
        "pipeline": model,          # full trained model (with imputer and optional target transform)
        "features": num_cols,
        "target": target_col,
        "feature_defaults": X_train.median(numeric_only=True).to_dict(),  # for UI fill
        "currency": get_currency_symbol(df),
        "metrics": {
            "rmse": rmse, "r2": r2,
            "cv_r2_mean": float(cv_r2.mean()), "cv_r2_std": float(cv_r2.std()),
            "cv_rmse_mean": float(cv_rmse.mean()),
            "baseline_r2": r2_dummy
        },
        "model_choice": model_choice,
        "use_log_target": use_log_target,
        "feature_importance": fi
    }
    return bundle, X, y, (X_train, X_test, y_train, y_test)

def predict_with_breakdown(dataset_name, user_inputs, epcic_percentages,
                           predev_pct, owners_pct, contingency_pct, escalation_pct):
    bundle = st.session_state["models"].get(dataset_name)
    if not bundle:
        raise ValueError(f"Model for {dataset_name} not available. Train it first.")
    model = bundle["pipeline"]
    features = bundle["features"]
    target_col = bundle["target"]
    defaults = bundle["feature_defaults"]
    currency = bundle.get("currency", "")

    # Prepare row with safe numeric parsing
    row = {}
    for f in features:
        val = user_inputs.get(f, None)
        if val in (None, "", "nan"):
            row[f] = defaults.get(f, 0.0)
        else:
            try:
                row[f] = float(val)
            except Exception:
                row[f] = defaults.get(f, 0.0)

    df_input = pd.DataFrame([row])[features]
    pred = float(model.predict(df_input)[0])

    epcic_breakdown = {}
    result = {"Project Name": user_inputs.get("Project Name", ""), **row, target_col: round(pred, 2)}

    for phase, pct in epcic_percentages.items():
        cost = round(pred * (pct / 100.0), 2)
        epcic_breakdown[phase] = {"cost": cost, "percentage": pct}
        result[f"{phase} Cost"] = cost

    predev_cost = round(pred * (predev_pct / 100.0), 2)
    owners_cost = round(pred * (owners_pct / 100.0), 2)
    contingency_base = pred + owners_cost
    contingency_cost = round(contingency_base * (contingency_pct / 100.0), 2)
    escalation_base = pred + owners_cost
    escalation_cost = round(escalation_base * (escalation_pct / 100.0), 2)
    grand_total = round(pred + owners_cost + contingency_cost + escalation_cost, 2)

    result.update({
        "Pre-Development Cost": predev_cost,
        "Owner's Cost": owners_cost,
        "Cost Contingency": contingency_cost,
        "Escalation & Inflation": escalation_cost,
        "Grand Total": grand_total
    })

    breakdown = {
        "epcic": epcic_breakdown,
        "predev_cost": predev_cost,
        "owners_cost": owners_cost,
        "contingency_cost": contingency_cost,
        "escalation_cost": escalation_cost,
        "grand_total": grand_total,
        "target_col": target_col
    }
    return result, breakdown, currency

# ------------------------- State init -------------------------
def init_state():
    ss = st.session_state
    ss.setdefault("datasets", {})  # dataset_name -> DataFrame
    ss.setdefault("predictions", {})  # dataset_name -> list of dict
    ss.setdefault("processed_excel_files", set())
    ss.setdefault("models", {})  # dataset_name -> bundle
    ss.setdefault("projects", {})  # project_name -> dict
    ss.setdefault("component_labels", {})  # dataset_name -> label
init_state()

# ------------------------- Sidebar -------------------------
st.sidebar.header("Data Controls")
if st.sidebar.button("Clear all predictions"):
    st.session_state["predictions"] = {}
    st.sidebar.success("All predictions cleared!")
if st.sidebar.button("Clear processed files history"):
    st.session_state["processed_excel_files"] = set()
    st.sidebar.success("Processed files history cleared!")
if st.sidebar.button("📥 Download All Predictions"):
    if st.session_state["predictions"]:
        download_all_predictions()
        st.sidebar.success("All predictions compiled successfully!")
    else:
        st.sidebar.warning("No predictions to download.")
st.sidebar.markdown('---')

st.sidebar.header("System Controls")
if st.sidebar.button("🔄 Refresh System"):
    list_csvs_from_manifest.clear()
    st.sidebar.success("Cache cleared.")
st.sidebar.markdown('---')

st.sidebar.subheader("📁 Choose Data Source")
data_source = st.sidebar.radio("Data Source", ["Upload CSV", "Load from Server"], index=0,
                               key=make_widget_key("SIDEBAR", "data_source"))
uploaded_files = []
if data_source == "Upload CSV":
    uploaded_files = st.sidebar.file_uploader(
        "Upload CSV files (max 200MB)", type="csv", accept_multiple_files=True,
        key=make_widget_key("SIDEBAR", "upload_csvs")
    )
    st.sidebar.markdown("### 📁 Or access data from external link")
    data_link = "https://petronas.sharepoint.com/sites/ecm_ups_coe/confidential/DFE%20Cost%20Engineering/Forms/AllItems.aspx?id=%2Fsites%2Fecm%5Fups%5Fcoe%2Fconfidential%2FDFE%20Cost%20Engineering%2F2%2ETemplate%20Tools%2FCost%20Predictor%2FDatabase%2FCAPEX%20%2D%20RT%20Q1%202025&viewid=25092e6d%2D373d%2D41fe%2D8f6f%2D486cd8cdd5b8"
    st.sidebar.markdown(f"{data_link}", unsafe_allow_html=True)
else:
    github_csvs = list_csvs_from_manifest(DATA_FOLDER)
    if github_csvs:
        selected_file = st.sidebar.selectbox("Choose CSV from GitHub", github_csvs,
                                             key=make_widget_key("SIDEBAR", "github_select"))
        if selected_file:
            raw_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{DATA_FOLDER}/{selected_file}"
            try:
                df = pd.read_csv(raw_url)
                fake_file = type('FakeUpload', (), {'name': selected_file})
                uploaded_files.append(fake_file)
                st.session_state["datasets"][selected_file] = df
                st.session_state["predictions"].setdefault(selected_file, [])
                st.success(f"✅ Loaded from GitHub: {selected_file}")
            except Exception as e:
                st.error(f"Error loading CSV: {e}")
    else:
        st.warning("No CSV files found in GitHub folder.")

for uploaded_file in uploaded_files:
    if uploaded_file.name not in st.session_state["datasets"]:
        df = pd.read_csv(uploaded_file)
        st.session_state["datasets"][uploaded_file.name] = df
        st.session_state["predictions"].setdefault(uploaded_file.name, [])

st.sidebar.markdown('---')
if st.sidebar.checkbox("🧹 Cleanup Current Session",
                       value=False,
                       help="Remove datasets not uploaded in this session.",
                       key=make_widget_key("SIDEBAR", "cleanup")):
    uploaded_names = {f.name for f in uploaded_files}
    for name in list(st.session_state["datasets"].keys()):
        if name not in uploaded_names:
            del st.session_state["datasets"][name]
            st.session_state["predictions"].pop(name, None)

# ------------------------- Tabs -------------------------
st.title("💲CAPEX AI – Project Workspace")
tab1, tab2, tab3 = st.tabs(["📁 Datasets & Models", "🏗️ Project Builder", "🅚 Compare Projects"])

# ================= Tab 1: Datasets & Models =====================
with tab1:
    if not st.session_state["datasets"]:
        st.info("Please upload one or more CSV files to begin.")
    else:
        selected_dataset_name = st.selectbox(
            "Select a dataset for prediction",
            list(st.session_state["datasets"].keys()),
            key=make_widget_key("TAB1", "dataset_select")
        )
        df = st.session_state["datasets"][selected_dataset_name]
        clean_name = selected_dataset_name.replace(".csv", "")

        # ---- Target & model selectors ----
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols) == 0:
            st.error("No numeric columns found in the dataset. Please upload a numeric dataset.")
            st.stop()

        selected_target = st.selectbox(
            "Select target column (label)", numeric_cols,
            key=make_widget_key("TAB1", "target_select", selected_dataset_name)
        )
        model_choice = st.selectbox(
            "Select model", ["HistGradientBoosting", "RandomForest", "ExtraTrees"],
            index=0, key=make_widget_key("TAB1", "model_select", selected_dataset_name)
        )
        use_log_target = st.checkbox(
            "Log-transform target (recommended for CAPEX)",
            value=True,
            help="Trains on log1p(target) and reports predictions in original scale.",
            key=make_widget_key("TAB1", "log_target", selected_dataset_name)
        )

        # ---- Train (and visualize) ----
        bundle, X, y, splits = train_model_bundle_from_df(
            df, target_col=selected_target, model_choice=model_choice, use_log_target=use_log_target
        )
        st.session_state["models"][selected_dataset_name] = bundle
        X_train, X_test, y_train, y_test = splits

        with st.expander("Model Training and Performance", expanded=False):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Holdout RMSE", f"{bundle['metrics']['rmse']:,.2f}")
            c2.metric("Holdout R²", f"{bundle['metrics']['r2']:.3f}")
            c3.metric("CV R² (mean ± std)", f"{bundle['metrics']['cv_r2_mean']:.3f} ± {bundle['metrics']['cv_r2_std']:.3f}")
            c4.metric("Baseline R² (Dummy)", f"{bundle['metrics']['baseline_r2']:.3f}")

        with st.expander("Data Overview", expanded=False):
            st.write("Dataset Shape:", df.shape)
            st.dataframe(df.head())

        with st.expander("Data Visualization", expanded=False):
            st.subheader("Correlation Matrix")
            num_df = df.select_dtypes(include=[np.number])
            feature_count = len(num_df.columns)
            corr_height = min(9, max(7, feature_count * 0.5))
            fig, ax = plt.subplots(figsize=(8, corr_height))
            sns.heatmap(num_df.corr(), annot=True, cmap="coolwarm", fmt=".2f", annot_kws={"size": 10})
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

            st.subheader("Permutation Feature Importance (holdout)")
            fi_df = bundle["feature_importance"]
            fi_height = min(8, max(4, len(fi_df) * 0.3))
            fig, ax = plt.subplots(figsize=(8, fi_height))
            sns.barplot(data=fi_df, x="importance_mean", y="feature", orient="h")
            plt.title("Feature Importance (permutation, R² drop)")
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

            st.subheader("Cost Curve (Original Data Only)")
            feature = st.selectbox(
                "Select feature for cost curve (viz)", [c for c in df.columns if c != selected_target],
                key=make_widget_key("TAB1", selected_dataset_name, "cost_curve_feature_viz")
            )
            fig, ax = plt.subplots(figsize=(7, 6))
            x_vals = df[feature].values
            y_vals = df[selected_target].values
            sns.scatterplot(x=x_vals, y=y_vals, label="Original Data", ax=ax)
            ax.set_xlabel(feature)
            ax.set_ylabel(selected_target)
            ax.set_title(f"Cost Curve: {feature} vs {selected_target}")
            ax.legend()
            ax.xaxis.set_major_formatter(FuncFormatter(human_format))
            ax.yaxis.set_major_formatter(FuncFormatter(human_format))
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        # ---- Cost % configuration for single-dataset quick predictions ----
        with st.expander("Cost Breakdown Configuration", expanded=False):
            st.subheader("🛠️ EPCIC Cost Breakdown Percentage Input")
            epcic_percentages = {}
            col_ep1, col_ep2, col_ep3, col_ep4, col_ep5 = st.columns(5)
            epcic_percentages["Engineering"] = col_ep1.number_input(
                "Engineering (%)", 0.0, 100.0, 0.0, key=make_widget_key("TAB1", "epcic_eng")
            )
            epcic_percentages["Procurement"] = col_ep2.number_input(
                "Procurement (%)", 0.0, 100.0, 0.0, key=make_widget_key("TAB1", "epcic_proc")
            )
            epcic_percentages["Construction"] = col_ep3.number_input(
                "Construction (%)", 0.0, 100.0, 0.0, key=make_widget_key("TAB1", "epcic_const")
            )
            epcic_percentages["Installation"] = col_ep4.number_input(
                "Installation (%)", 0.0, 100.0, 0.0, key=make_widget_key("TAB1", "epcic_inst")
            )
            epcic_percentages["Commissioning"] = col_ep5.number_input(
                "Commissioning (%)", 0.0, 100.0, 0.0, key=make_widget_key("TAB1", "epcic_comm")
            )
            epcic_total = sum(epcic_percentages.values())
            if abs(epcic_total - 100.0) > 1e-3 and epcic_total > 0:
                st.warning(f"⚠️ EPCIC total is {epcic_total:.2f}%. Consider summing to 100% if applicable.")

            st.subheader("💼 Pre-Dev and Owner's Cost Percentage Input")
            col_pd1, col_pd2 = st.columns(2)
            predev_percentage = col_pd1.number_input(
                "Pre-Development (%)", 0.0, 100.0, 0.0, key=make_widget_key("TAB1", "predev_pct")
            )
            owners_percentage = col_pd2.number_input(
                "Owner's Cost (%)", 0.0, 100.0, 0.0, key=make_widget_key("TAB1", "owners_pct")
            )
            col_ct1, col_ct2 = st.columns(2)
            contingency_percentage = col_ct1.number_input(
                "Contingency (%)", 0.0, 100.0, 0.0, key=make_widget_key("TAB1", "cont_pct")
            )
            escalation_percentage = col_ct2.number_input(
                "Escalation & Inflation (%)", 0.0, 100.0, 0.0, key=make_widget_key("TAB1", "escal_pct")
            )

        # ---- Quick single-dataset prediction (NaN-safe via pipeline) ----
        st.header(f"Make New Predictions (based on {clean_name})")
        project_name_input = st.text_input(
            "Enter Project Name", key=make_widget_key("TAB1", selected_dataset_name, "project_name")
        )

        # Feature input grid
        feat_cols = bundle["features"]
        num_features = len(feat_cols)
        if num_features <= 2:
            cols_inputs = st.columns(num_features)
        else:
            cols_inputs = []
            for i in range(0, num_features, 2):
                row_cols = st.columns(min(2, num_features - i))
                cols_inputs.extend(row_cols)

        new_data = {}
        for i, col in enumerate(feat_cols):
            col_idx = i % len(cols_inputs) if len(cols_inputs) > 0 else 0
            user_val = cols_inputs[col_idx].text_input(
                f"{col}", key=make_widget_key("TAB1", selected_dataset_name, "single_predict", i, col)
            )
            if str(user_val).strip().lower() in ("", "nan"):
                new_data[col] = np.nan
            else:
                try:
                    new_data[col] = float(user_val)
                except ValueError:
                    new_data[col] = np.nan

        if st.button("Predict", key=make_widget_key("TAB1", selected_dataset_name, "predict_btn")):
            bundle = st.session_state["models"][selected_dataset_name]
            model = bundle["pipeline"]
            defaults = bundle["feature_defaults"]
            target_column = bundle["target"]

            # Fill missing with training medians (defaults)
            row_filled = {col: (new_data[col] if pd.notna(new_data[col]) else defaults.get(col, 0.0))
                          for col in feat_cols}
            df_input = pd.DataFrame([row_filled])[feat_cols]
            pred = float(model.predict(df_input)[0])

            result = {"Project Name": project_name_input, **row_filled, target_column: round(pred, 2)}
            epcic_breakdown = {}
            for phase, percent in epcic_percentages.items():
                cost = round(pred * (percent / 100), 2)
                result[f"{phase} Cost"] = cost
                epcic_breakdown[phase] = {"cost": cost, "percentage": percent}

            predev_cost = round(pred * (predev_percentage / 100), 2)
            owners_cost = round(pred * (owners_percentage / 100), 2)
            contingency_base = pred + owners_cost
            contingency_cost = round(contingency_base * (contingency_percentage / 100), 2)
            escalation_base = pred + owners_cost
            escalation_cost = round(escalation_base * (escalation_percentage / 100), 2)
            grand_total = round(pred + owners_cost + contingency_cost + escalation_cost, 2)

            result.update({
                "Pre-Development Cost": predev_cost,
                "Owner's Cost": owners_cost,
                "Cost Contingency": contingency_cost,
                "Escalation & Inflation": escalation_cost,
                "Grand Total": grand_total
            })

            st.session_state["predictions"][selected_dataset_name].append(result)
            currency = bundle.get("currency", "")
            st.success(
                f"### ✅ Cost Summary of project {project_name_input}\n\n"
                f"**{target_column}:** {currency} {pred:,.2f}\n\n"
                + (f"**Pre-Development:** {currency} {predev_cost:,.2f}\n\n" if predev_percentage > 0 else "")
                + (f"**Owner's Cost:** {currency} {owners_cost:,.2f}\n\n" if owners_percentage > 0 else "")
                + (f"**Contingency:** {currency} {contingency_cost:,.2f}\n\n" if contingency_percentage > 0 else "")
                + (f"**Escalation & Inflation:** {currency} {escalation_cost:,.2f}\n\n" if escalation_percentage > 0 else "")
                + f"**Grand Total:** {currency} {grand_total:,.2f}"
            )

        st.write("Or upload an Excel file:")
        excel_file = st.file_uploader(
            "Upload Excel file", type=["xlsx"],
            key=make_widget_key("TAB1", selected_dataset_name, "batch_excel")
        )
        if excel_file:
            file_id = f"{excel_file.name}_{excel_file.size}_{selected_dataset_name}"
            if file_id not in st.session_state["processed_excel_files"]:
                batch_df = pd.read_excel(excel_file)
                features = st.session_state["models"][selected_dataset_name]["features"]
                target_column = st.session_state["models"][selected_dataset_name]["target"]
                if set(features).issubset(batch_df.columns):
                    model = st.session_state["models"][selected_dataset_name]["pipeline"]
                    preds = model.predict(batch_df[features])
                    batch_df[target_column] = preds
                    for i, row in batch_df.iterrows():
                        name = row.get("Project Name", f"Project {i+1}")
                        entry = {"Project Name": name}
                        entry.update(row[features].to_dict())
                        p = float(preds[i])
                        entry[target_column] = round(p, 2)
                        # breakdown
                        for phase, percent in epcic_percentages.items():
                            entry[f"{phase} Cost"] = round(p * (percent / 100), 2)
                        predev_cost = round(p * (predev_percentage / 100), 2)
                        owners_cost = round(p * (owners_percentage / 100), 2)
                        contingency_base = p + owners_cost
                        contingency_cost = round(contingency_base * (contingency_percentage / 100), 2)
                        escalation_base = p + owners_cost
                        escalation_cost = round(escalation_base * (escalation_percentage / 100), 2)
                        grand_total = round(p + owners_cost + contingency_cost + escalation_cost, 2)
                        entry["Pre-Development Cost"] = predev_cost
                        entry["Owner's Cost"] = owners_cost
                        entry["Cost Contingency"] = contingency_cost
                        entry["Escalation & Inflation"] = escalation_cost
                        entry["Grand Total"] = grand_total
                        st.session_state["predictions"][selected_dataset_name].append(entry)
                    st.session_state["processed_excel_files"].add(file_id)
                    st.success("Batch prediction successful!")
                else:
                    st.error("Excel missing required columns.")

        with st.expander("Simplified Project List", expanded=True):
            preds = st.session_state["predictions"][selected_dataset_name]
            if preds:
                if st.button("Delete All", key=make_widget_key("TAB1", selected_dataset_name, "delete_all")):
                    st.session_state["predictions"][selected_dataset_name] = []
                    to_remove = {fid for fid in st.session_state["processed_excel_files"] if fid.endswith(selected_dataset_name)}
                    for fid in to_remove:
                        st.session_state["processed_excel_files"].remove(fid)
                    st.rerun()
                for i, p in enumerate(preds):
                    c1, c2 = st.columns([3, 1])
                    c1.write(p["Project Name"])
                    if c2.button("Delete", key=make_widget_key("TAB1", selected_dataset_name, "del", i)):
                        preds.pop(i)
                        st.rerun()
            else:
                st.write("No predictions yet.")

        st.header(f"Prediction Summary based on {clean_name}")
        preds = st.session_state["predictions"][selected_dataset_name]
        if preds:
            df_preds = pd.DataFrame(preds)
            num_cols = df_preds.select_dtypes(include=[np.number]).columns
            df_preds_display = df_preds.copy()
            for col in num_cols:
                df_preds_display[col] = df_preds_display[col].apply(lambda x: format_with_commas(x))
            st.dataframe(df_preds_display, use_container_width=True)

            towrite = io.BytesIO()
            df_preds.to_excel(towrite, index=False, engine="openpyxl")
            towrite.seek(0)
            st.download_button(
                "Download Predictions as Excel",
                data=towrite,
                file_name=f"{selected_dataset_name}_predictions.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=make_widget_key("TAB1", selected_dataset_name, "download_preds")
            )
        else:
            st.write("No predictions available.")

# ================= Tab 2: Project Builder =======================
with tab2:
    st.header("🏗️ Project Builder")
    colA, colB = st.columns([3, 2])
    with colA:
        new_project_name = st.text_input(
            "Project Name", placeholder="e.g., Project A",
            key=make_widget_key("TAB2", "project_name_input")
        )
    with colB:
        if new_project_name and new_project_name not in st.session_state["projects"]:
            if st.button("Create Project", key=make_widget_key("TAB2", "create_project_btn")):
                st.session_state["projects"][new_project_name] = {"components": [], "totals": {}, "currency": ""}
                st.success(f"Project '{new_project_name}' created.")

    if not st.session_state["datasets"]:
        st.info("Upload datasets in **Datasets & Models** first.")
    else:
        existing_projects = list(st.session_state["projects"].keys())
        proj_sel = st.selectbox(
            "Choose project",
            ([new_project_name] + existing_projects) if new_project_name else existing_projects,
            key=make_widget_key("TAB2", "project_select")
        )

        ds_names = sorted(st.session_state["datasets"].keys())
        dataset_for_comp = st.selectbox(
            "Dataset for this component", ds_names,
            key=make_widget_key("TAB2", "dataset_for_component")
        )

        # Quick train if missing (with local selectors)
        if dataset_for_comp and dataset_for_comp not in st.session_state["models"]:
            with st.expander("Train model for selected dataset (quick)", expanded=False):
                df_q = st.session_state["datasets"][dataset_for_comp]
                num_cols_q = df_q.select_dtypes(include=[np.number]).columns.tolist()
                target_q = st.selectbox("Target column", num_cols_q,
                                        key=make_widget_key("TAB2", "quick_target", dataset_for_comp))
                model_choice_q = st.selectbox("Model", ["HistGradientBoosting", "RandomForest", "ExtraTrees"],
                                              key=make_widget_key("TAB2", "quick_model", dataset_for_comp))
                log_target_q = st.checkbox("Log-transform target", value=True,
                                           key=make_widget_key("TAB2", "quick_log_target", dataset_for_comp))
                if st.button("⚙️ Train", key=make_widget_key("TAB2", "quick_train_btn", dataset_for_comp)):
                    try:
                        bundle_q, *_ = train_model_bundle_from_df(df_q, target_col=target_q,
                                                                  model_choice=model_choice_q,
                                                                  use_log_target=log_target_q)
                        st.session_state["models"][dataset_for_comp] = bundle_q
                        st.success(
                            f"Model trained for {dataset_for_comp} "
                            f"(RMSE: {bundle_q['metrics']['rmse']:,.2f}, R²: {bundle_q['metrics']['r2']:.3f}, "
                            f"CV R²: {bundle_q['metrics']['cv_r2_mean']:.3f})"
                        )
                    except Exception as e:
                        st.error(f"Training failed: {e}")

        default_label = st.session_state["component_labels"].get(dataset_for_comp, "")
        component_type = st.text_input(
            "Component type (Oil & Gas term)",
            value=(default_label or "FPSO / Pipeline / Wellhead / Subsea"),
            key=make_widget_key("TAB2", "component_type", proj_sel or new_project_name or "NoProject")
        )

        if dataset_for_comp and dataset_for_comp in st.session_state["models"]:
            st.markdown("**Component feature inputs** *(leave blank to auto-fill with training medians)*")
            feat_cols = st.session_state["models"][dataset_for_comp]["features"]
            cols = st.columns(2)
            comp_inputs = {}
            for i, c in enumerate(feat_cols):
                key = make_widget_key("TAB2", "ProjectBuilder", proj_sel or new_project_name or "NoProject",
                                      dataset_for_comp, "feature", i, c)
                comp_inputs[c] = cols[i % 2].text_input(c, key=key)

            st.markdown("---")
            st.markdown("**Cost Percentage Inputs (EPCIC / Pre-Dev / Owner / Contingency / Escalation)**")
            col_ep1, col_ep2, col_ep3, col_ep4, col_ep5 = st.columns(5)
            epcic_percentages = {
                "Engineering": col_ep1.number_input("Engineering (%)", 0.0, 100.0, 0.0,
                                                    key=make_widget_key("TAB2", "pb_eng", proj_sel)),
                "Procurement": col_ep2.number_input("Procurement (%)", 0.0, 100.0, 0.0,
                                                    key=make_widget_key("TAB2", "pb_proc", proj_sel)),
                "Construction": col_ep3.number_input("Construction (%)", 0.0, 100.0, 0.0,
                                                     key=make_widget_key("TAB2", "pb_const", proj_sel)),
                "Installation": col_ep4.number_input("Installation (%)", 0.0, 100.0, 0.0,
                                                     key=make_widget_key("TAB2", "pb_inst", proj_sel)),
                "Commissioning": col_ep5.number_input("Commissioning (%)", 0.0, 100.0, 0.0,
                                                      key=make_widget_key("TAB2", "pb_comm", proj_sel)),
            }
            col_pd1, col_pd2 = st.columns(2)
            predev_pct = col_pd1.number_input("Pre-Development (%)", 0.0, 100.0, 0.0,
                                              key=make_widget_key("TAB2", "pb_predev", proj_sel))
            owners_pct = col_pd2.number_input("Owner's Cost (%)", 0.0, 100.0, 0.0,
                                              key=make_widget_key("TAB2", "pb_owners", proj_sel))
            col_ct1, col_ct2 = st.columns(2)
            contingency_pct = col_ct1.number_input("Contingency (%)", 0.0, 100.0, 0.0,
                                                   key=make_widget_key("TAB2", "pb_cont", proj_sel))
            escalation_pct = col_ct2.number_input("Escalation & Inflation (%)", 0.0, 100.0, 0.0,
                                                  key=make_widget_key("TAB2", "pb_escal", proj_sel))
            epcic_total = sum(epcic_percentages.values())
            if abs(epcic_total - 100.0) > 1e-3 and epcic_total > 0:
                st.warning(f"⚠️ EPCIC total is {epcic_total:.2f}%. Consider summing to 100% if applicable.")

            if proj_sel:
                if st.button("➕ Predict & Add Component",
                             key=make_widget_key("TAB2", "add_component_btn", proj_sel, dataset_for_comp)):
                    if proj_sel not in st.session_state["projects"]:
                        st.error("Please create/select a project first.")
                    else:
                        comp_inputs["Project Name"] = proj_sel
                        try:
                            res, breakdown, currency = predict_with_breakdown(
                                dataset_for_comp, comp_inputs, epcic_percentages,
                                predev_pct, owners_pct, contingency_pct, escalation_pct
                            )
                            st.session_state["component_labels"][dataset_for_comp] = component_type or default_label
                            comp_entry = {
                                "component_type": component_type or default_label or "Component",
                                "dataset": dataset_for_comp,
                                "inputs": {k: v for k, v in comp_inputs.items()},
                                "prediction": res[breakdown["target_col"]],
                                "breakdown": breakdown
                            }
                            st.session_state["projects"][proj_sel]["components"].append(comp_entry)
                            if not st.session_state["projects"][proj_sel]["currency"]:
                                st.session_state["projects"][proj_sel]["currency"] = currency
                            st.success(f"Added {comp_entry['component_type']} ({dataset_for_comp}) to '{proj_sel}'.")
                        except Exception as e:
                            st.error(f"Failed to predict component: {e}")
            else:
                st.info("Train a model for the selected dataset, then add components.")

        st.markdown("---")
        st.subheader("Current Project Overview")
        if st.session_state["projects"]:
            sel = st.selectbox("View/Edit project", list(st.session_state["projects"].keys()),
                               key=make_widget_key("TAB2", "view_project_select"))
            proj = st.session_state["projects"][sel]
            comps = proj.get("components", [])
            currency = proj.get("currency", "")
            if not comps:
                st.info("No components yet. Add one above.")
            else:
                rows = []
                for c in comps:
                    rows.append({
                        "Component": f"{c['component_type']}",
                        "Dataset": c["dataset"],
                        "Predicted CAPEX": c["prediction"],
                        "Grand Total": c["breakdown"]["grand_total"]
                    })
                dfc = pd.DataFrame(rows)
                st.dataframe(dfc, use_container_width=True)
                total_capex = float(sum(r["Predicted CAPEX"] for r in rows))
                total_grand = float(sum(r["Grand Total"] for r in rows))
                proj["totals"] = {"capex_sum": total_capex, "grand_total": total_grand}
                col_t1, col_t2 = st.columns(2)
                col_t1.metric("Project CAPEX (sum of model predictions)", f"{total_capex:,.2f}")
                col_t2.metric("Project Grand Total", f"{total_grand:,.2f}")

                # === VISUALS: Project Builder ===
                currency = currency or ""
                # 1) Component Composition (stacked bar)
                stack_rows = []
                for c in comps:
                    comp_name = c["component_type"]
                    capex = float(c["prediction"])
                    owners = float(c["breakdown"]["owners_cost"])
                    cont = float(c["breakdown"]["contingency_cost"])
                    escal = float(c["breakdown"]["escalation_cost"])
                    predev = float(c["breakdown"]["predev_cost"])
                    stack_rows.append({"Component": comp_name, "CAPEX": capex, "Owners": owners,
                                       "Contingency": cont, "Escalation": escal, "PreDev": predev})
                dfc_stack = pd.DataFrame(stack_rows).groupby("Component", as_index=False).sum()
                st.subheader("📊 Component Composition")
                fig_stack = plot_component_stack(dfc_stack, title="Component Composition (Grand Total)", currency=currency)
                st.pyplot(fig_stack, use_container_width=True)

                # 2) Cost Share by Component (pie of Grand Total)
                labels = dfc["Component"].tolist()
                sizes = dfc["Grand Total"].astype(float).tolist()
                if sum(sizes) > 0:
                    st.subheader("🧁 Cost Share by Component")
                    fig_pie = plot_component_pie(labels, sizes, title="Cost Share by Component", currency=currency)
                    st.pyplot(fig_pie, use_container_width=True)

                # 3) EPCIC Breakdown per Component (stacked)
                ep_rows = []
                for c in comps:
                    comp_name = c["component_type"]
                    ep = c["breakdown"]["epcic"]  # dict of phases with {'cost','percentage'}
                    ep_rows.append({
                        "Component": comp_name,
                        "Engineering": float(ep.get("Engineering", {}).get("cost", 0.0)),
                        "Procurement": float(ep.get("Procurement", {}).get("cost", 0.0)),
                        "Construction": float(ep.get("Construction", {}).get("cost", 0.0)),
                        "Installation": float(ep.get("Installation", {}).get("cost", 0.0)),
                        "Commissioning": float(ep.get("Commissioning", {}).get("cost", 0.0)),
                    })
                epcic_df = pd.DataFrame(ep_rows).groupby("Component", as_index=False).sum()
                if epcic_df.drop(columns=["Component"]).sum().sum() > 0:
                    st.subheader("🏗️ EPCIC Breakdown per Component")
                    fig_ep = plot_epcic_stack(epcic_df, title="EPCIC Breakdown per Component", currency=currency)
                    st.pyplot(fig_ep, use_container_width=True)

                # Remove component controls
                for idx, c in enumerate(comps):
                    cc1, cc2, cc3 = st.columns([6, 3, 1])
                    cc1.write(f"**{c['component_type']}** — *{c['dataset']}*")
                    cc2.write(f"Grand Total: {c['breakdown']['grand_total']:,.2f}")
                    if cc3.button("🗑️", key=make_widget_key("TAB2", "del_comp_btn", sel, idx)):
                        comps.pop(idx)
                        st.rerun()

                # Export project
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    dfc.to_excel(writer, sheet_name="Components", index=False)
                buffer.seek(0)
                st.download_button("⬇️ Download Project (Excel)", buffer,
                                   file_name=f"{sel}_project.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   key=make_widget_key("TAB2", "download_project_excel", sel))
                st.download_button("⬇️ Download Project (JSON)",
                                   data=json.dumps(st.session_state["projects"][sel], indent=2),
                                   file_name=f"{sel}.json", mime="application/json",
                                   key=make_widget_key("TAB2", "download_project_json", sel))
                up = st.file_uploader("Import project JSON", type=["json"],
                                      key=make_widget_key("TAB2", "import_json", sel))
                if up is not None:
                    try:
                        data = json.load(up)
                        st.session_state["projects"][sel] = data
                        st.success("Project imported and replaced.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to import: {e}")

# ================= Tab 3: Compare Projects ======================
with tab3:
    st.header("🅚 Compare Projects")
    proj_names = list(st.session_state["projects"].keys())
    if len(proj_names) < 2:
        st.info("Create at least two projects to compare.")
    else:
        compare = st.multiselect("Pick projects to compare", proj_names, default=proj_names[:2],
                                 key=make_widget_key("TAB3", "compare_select"))
        if len(compare) >= 2:
            comp_rows = []
            for p in compare:
                proj = st.session_state["projects"][p]
                grand_total = proj.get("totals", {}).get("grand_total", 0.0)
                capex_sum = proj.get("totals", {}).get("capex_sum", 0.0)
                comp_rows.append({"Project": p, "CAPEX Sum": capex_sum, "Grand Total": grand_total})
            dft = pd.DataFrame(comp_rows).set_index("Project")
            st.dataframe(dft.style.format("{:,.2f}"), use_container_width=True)

            # === VISUALS: Compare Projects ===
            # 4) Labeled bars for Grand Totals
            st.subheader("📊 Project Grand Totals")
            fig_tot = plot_project_totals_bar(dft[["Grand Total"]], title="Project Grand Totals", currency="")
            st.pyplot(fig_tot, use_container_width=True)

            # 5) Stacked composition per project (sum across components)
            comp_rows = []
            for p in compare:
                proj = st.session_state["projects"][p]
                comps = proj.get("components", [])
                capex = owners = cont = escal = predev = 0.0
                for c in comps:
                    capex += float(c["prediction"])
                    owners += float(c["breakdown"]["owners_cost"])
                    cont += float(c["breakdown"]["contingency_cost"])
                    escal += float(c["breakdown"]["escalation_cost"])
                    predev += float(c["breakdown"]["predev_cost"])
                comp_rows.append({"Project": p, "CAPEX": capex, "Owners": owners,
                                  "Contingency": cont, "Escalation": escal, "PreDev": predev})
            comp_df = pd.DataFrame(comp_rows).set_index("Project")
            comp_df = comp_df.loc[dft.index].reset_index()  # align with visible order
            st.subheader("🏗️ Project Composition (Stacked)")
            fig_pc = plot_projects_composition_stack(comp_df, title="Project Composition (Grand Total)", currency="")
            st.pyplot(fig_pc, use_container_width=True)

            # 6) Two-project Δ waterfall by categories
            if len(compare) == 2:
                p1, p2 = compare
                comp2 = comp_df[comp_df["Project"] == p2].iloc[0]
                comp1 = comp_df[comp_df["Project"] == p1].iloc[0]
                delta_dict = {
                    "CAPEX": float(comp2["CAPEX"] - comp1["CAPEX"]),
                    "Owners": float(comp2["Owners"] - comp1["Owners"]),
                    "Contingency": float(comp2["Contingency"] - comp1["Contingency"]),
                    "Escalation": float(comp2["Escalation"] - comp1["Escalation"]),
                    "PreDev": float(comp2["PreDev"] - comp1["PreDev"]),
                }
                st.subheader(f"🔀 Difference Breakdown: {p2} vs {p1}")
                fig_wf = plot_two_project_waterfall(delta_dict, title=f"Δ Grand Total Waterfall: {p2} – {p1}", currency="")
                st.pyplot(fig_wf, use_container_width=True)