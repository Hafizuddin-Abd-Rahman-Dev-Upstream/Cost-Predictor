import io
import json
import zipfile
import requests
import numpy as np
import pandas as pd
import streamlit as st

# ML/Stats
from sklearn.impute import KNNImputer, SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, Lasso
from sklearn.svm import SVR
from sklearn.tree import DecisionTreeRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score
from scipy.stats import linregress

# Viz in-app
import plotly.express as px
import plotly.graph_objects as go

# Viz for PPT
import matplotlib.pyplot as plt

# PPT export
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

# Excel export helpers
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.utils import get_column_letter

# ---------------------------------------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------------------------------------
st.set_page_config(
    page_title="CAPEX AI RT2025",
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

html, body {{
  font-family: 'Inter', sans-serif;
}}

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
  <h1>CAPEX AI RT2025</h1>
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
if "projects" not in st.session_state:
    st.session_state.projects = {}
if "component_labels" not in st.session_state:
    st.session_state.component_labels = {}
if "best_model_name_per_dataset" not in st.session_state:
    st.session_state.best_model_name_per_dataset = {}

# IMPORTANT: uploader reset nonce (so "clear uploaded files" truly clears the widget)
if "uploader_nonce" not in st.session_state:
    st.session_state.uploader_nonce = 0

# Optional: "market index" cache
if "market_index" not in st.session_state:
    st.session_state.market_index = {"mode": "Manual", "value": 1.0, "series": None}

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


def get_currency_symbol(df: pd.DataFrame):
    for col in df.columns:
        uc = col.upper()
        if "RM" in uc:
            return "RM"
        if "USD" in uc or "$" in col:
            return "USD"
        if "€" in col:
            return "€"
        if "£" in col:
            return "£"
    try:
        sample_vals = df.iloc[:20].astype(str).values.flatten().tolist()
        if any("RM" in v.upper() for v in sample_vals):
            return "RM"
        if any("€" in v for v in sample_vals):
            return "€"
        if any("£" in v for v in sample_vals):
            return "£"
        if any("$" in v for v in sample_vals):
            return "USD"
    except Exception:
        pass
    return ""


def normalize_to_100(d: dict):
    total = sum(float(v) for v in d.values())
    if total <= 0:
        return d, total
    out = {k: float(v) * 100.0 / total for k, v in d.items()}
    # Keep sum close to 100 with rounding adjustment
    # (optional, but helps UI)
    keys = list(out.keys())
    rounded = {k: round(out[k], 2) for k in keys}
    diff = 100.0 - sum(rounded.values())
    if keys:
        rounded[keys[-1]] = round(rounded[keys[-1]] + diff, 2)
    return rounded, total


def cost_breakdown(
    base_pred: float,
    eprr: dict,
    sst_pct: float,
    owners_pct: float,
    cont_pct: float,
    esc_pct: float,
    market_index: float = 1.0,
):
    """
    base_pred: model output (base CAPEX)
    market_index: adjustment factor (e.g., 1.08 means +8% “realtime” market adjustment)
    """
    adj_base = float(base_pred) * float(market_index)

    owners_cost = round(adj_base * (owners_pct / 100.0), 2)
    sst_cost = round(adj_base * (sst_pct / 100.0), 2)
    contingency_cost = round((adj_base + owners_cost) * (cont_pct / 100.0), 2)
    escalation_cost = round((adj_base + owners_cost) * (esc_pct / 100.0), 2)

    eprr_costs = {k: round(adj_base * (float(v) / 100.0), 2) for k, v in (eprr or {}).items()}

    grand_total = round(adj_base + owners_cost + contingency_cost + escalation_cost, 2)

    return {
        "market_index": float(market_index),
        "base_capex_raw": float(base_pred),
        "base_capex_adjusted": float(adj_base),
        "owners_cost": owners_cost,
        "sst_cost": sst_cost,
        "contingency_cost": contingency_cost,
        "escalation_cost": escalation_cost,
        "eprr_costs": eprr_costs,
        "grand_total": grand_total,
    }


def project_components_df(proj):
    comps = proj.get("components", [])
    rows = []
    for c in comps:
        rows.append(
            {
                "Component": c["component_type"],
                "Dataset": c["dataset"],
                "Base CAPEX (Adj)": float(c["breakdown"]["base_capex_adjusted"]),
                "Owner's Cost": float(c["breakdown"]["owners_cost"]),
                "Contingency": float(c["breakdown"]["contingency_cost"]),
                "Escalation": float(c["breakdown"]["escalation_cost"]),
                "SST": float(c["breakdown"]["sst_cost"]),
                "Grand Total": float(c["breakdown"]["grand_total"]),
                "Market Index": float(c["breakdown"].get("market_index", 1.0)),
            }
        )
    return pd.DataFrame(rows)


def create_project_excel_report_capex(project_name, proj, currency=""):
    output = io.BytesIO()
    comps_df = project_components_df(proj)

    if comps_df.empty:
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            pd.DataFrame({"Info": [f"No components for project {project_name}"]}).to_excel(
                writer, sheet_name="Summary", index=False
            )
        output.seek(0)
        return output

    total_capex = comps_df["Base CAPEX (Adj)"].sum()
    total_grand = comps_df["Grand Total"].sum()

    summary_df = comps_df.copy()
    summary_df.loc[len(summary_df)] = {
        "Component": "TOTAL",
        "Dataset": "",
        "Base CAPEX (Adj)": total_capex,
        "Owner's Cost": comps_df["Owner's Cost"].sum(),
        "Contingency": comps_df["Contingency"].sum(),
        "Escalation": comps_df["Escalation"].sum(),
        "SST": comps_df["SST"].sum(),
        "Grand Total": total_grand,
        "Market Index": "",
    }

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        ws = writer.sheets["Summary"]

        max_row = ws.max_row
        max_col = ws.max_column

        for col_idx in range(3, max_col):  # numeric cols (exclude Market Index last col)
            col_letter = get_column_letter(col_idx)
            ws.conditional_formatting.add(
                f"{col_letter}2:{col_letter}{max_row-1}",
                ColorScaleRule(
                    start_type="percentile",
                    start_value=10,
                    start_color="FFE0F7FA",
                    mid_type="percentile",
                    mid_value=50,
                    mid_color="FF80DEEA",
                    end_type="percentile",
                    end_value=90,
                    end_color="FF00838F",
                ),
            )

        # Bar chart: Grand Total by component
        chart = BarChart()
        chart.title = "Grand Total by Component"
        data = Reference(ws, min_col=8, max_col=8, min_row=1, max_row=max_row - 1)
        cats = Reference(ws, min_col=1, min_row=2, max_row=max_row - 1)
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)
        chart.y_axis.title = f"Cost ({currency})".strip()
        chart.x_axis.title = "Component"
        chart.height = 10
        chart.width = 18
        ws.add_chart(chart, "K2")

        # Line chart: Base CAPEX trend
        line = LineChart()
        line.title = "Base CAPEX (Adjusted) Trend"
        data_capex = Reference(ws, min_col=3, max_col=3, min_row=1, max_row=max_row - 1)
        line.add_data(data_capex, titles_from_data=True)
        line.set_categories(cats)
        line.y_axis.title = f"Base CAPEX ({currency})".strip()
        line.height = 10
        line.width = 18
        ws.add_chart(line, "K20")

        comps_df.to_excel(writer, sheet_name="Components Detail", index=False)

    output.seek(0)
    return output


def create_project_pptx_report_capex(project_name, proj, currency=""):
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    # Use safe layouts
    layout_title_only = prs.slide_layouts[5]  # title only
    layout_title_content = prs.slide_layouts[1]  # title + content

    # Title slide
    slide = prs.slides.add_slide(layout_title_only)
    title = slide.shapes.title
    title.text = f"CAPEX Project Report\n{project_name}"
    p = title.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = RGBColor(0, 161, 155)

    comps_df = project_components_df(proj)
    comps = proj.get("components", [])
    total_capex = comps_df["Base CAPEX (Adj)"].sum() if not comps_df.empty else 0.0
    total_grand = comps_df["Grand Total"].sum() if not comps_df.empty else 0.0

    # Summary slide
    slide = prs.slides.add_slide(layout_title_content)
    slide.shapes.title.text = "Executive Summary"
    body = slide.shapes.placeholders[1].text_frame
    body.clear()

    lines = [
        f"Project: {project_name}",
        f"Total Components: {len(comps)}",
        f"Total Base CAPEX (Adjusted): {currency} {total_capex:,.2f}",
        f"Total Grand Total: {currency} {total_grand:,.2f}",
        "",
        "Components:",
    ]
    for c in comps:
        lines.append(f"• {c['component_type']}: {currency} {c['breakdown']['grand_total']:,.2f}")

    for i, line in enumerate(lines):
        para = body.paragraphs[0] if i == 0 else body.add_paragraph()
        para.text = line
        para.font.size = Pt(16)

    # Charts slides
    if not comps_df.empty:
        # Grand Total by Component
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(comps_df["Component"], comps_df["Grand Total"])
        ax.set_title("Grand Total by Component")
        ax.set_ylabel(f"Cost ({currency})".strip())
        ax.tick_params(axis="x", rotation=25)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        fig.tight_layout()

        img_stream = io.BytesIO()
        fig.savefig(img_stream, format="png", dpi=200, bbox_inches="tight")
        plt.close(fig)
        img_stream.seek(0)

        slide = prs.slides.add_slide(layout_title_only)
        slide.shapes.title.text = "Grand Total by Component"
        slide.shapes.add_picture(img_stream, Inches(0.7), Inches(1.5), width=Inches(8.6))

        # Stacked cost composition
        fig2, ax2 = plt.subplots(figsize=(7, 4))
        labels = comps_df["Component"]
        base = comps_df["Base CAPEX (Adj)"]
        owners = comps_df["Owner's Cost"]
        cont = comps_df["Contingency"]
        esc = comps_df["Escalation"]
        sst = comps_df["SST"]

        bottom = np.zeros(len(labels))
        for vals, lab in [
            (base, "Base CAPEX (Adj)"),
            (owners, "Owner"),
            (cont, "Contingency"),
            (esc, "Escalation"),
            (sst, "SST"),
        ]:
            ax2.bar(labels, vals, bottom=bottom, label=lab)
            bottom += np.array(vals)

        ax2.set_title("Cost Composition by Component")
        ax2.set_ylabel(f"Cost ({currency})".strip())
        ax2.tick_params(axis="x", rotation=25)
        ax2.grid(axis="y", linestyle="--", alpha=0.4)
        ax2.legend(fontsize=8, ncol=3)
        fig2.tight_layout()

        img_stream2 = io.BytesIO()
        fig2.savefig(img_stream2, format="png", dpi=200, bbox_inches="tight")
        plt.close(fig2)
        img_stream2.seek(0)

        slide2 = prs.slides.add_slide(layout_title_only)
        slide2.shapes.title.text = "Cost Composition by Component"
        slide2.shapes.add_picture(img_stream2, Inches(0.7), Inches(1.5), width=Inches(8.6))

    output = io.BytesIO()
    prs.save(output)
    output.seek(0)
    return output


def create_comparison_excel_report_capex(projects_dict, currency=""):
    output = io.BytesIO()

    summary_rows = []
    for name, proj in projects_dict.items():
        dfc = project_components_df(proj)
        capex = dfc["Base CAPEX (Adj)"].sum() if not dfc.empty else 0.0
        owners = dfc["Owner's Cost"].sum() if not dfc.empty else 0.0
        cont = dfc["Contingency"].sum() if not dfc.empty else 0.0
        esc = dfc["Escalation"].sum() if not dfc.empty else 0.0
        sst = dfc["SST"].sum() if not dfc.empty else 0.0
        grand = dfc["Grand Total"].sum() if not dfc.empty else 0.0
        summary_rows.append(
            {
                "Project": name,
                "Components": len(proj.get("components", [])),
                "CAPEX Sum (Adj)": capex,
                "Owner": owners,
                "Contingency": cont,
                "Escalation": esc,
                "SST": sst,
                "Grand Total": grand,
            }
        )

    summary_df = pd.DataFrame(summary_rows)

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Projects Summary", index=False)
        ws = writer.sheets["Projects Summary"]

        max_row = ws.max_row
        max_col = ws.max_column

        for col_idx in range(3, max_col + 1):
            col_letter = get_column_letter(col_idx)
            ws.conditional_formatting.add(
                f"{col_letter}2:{col_letter}{max_row}",
                ColorScaleRule(
                    start_type="percentile",
                    start_value=10,
                    start_color="FFE3F2FD",
                    mid_type="percentile",
                    mid_value=50,
                    mid_color="FF90CAF9",
                    end_type="percentile",
                    end_value=90,
                    end_color="FF1565C0",
                ),
            )

        chart = BarChart()
        chart.title = "Grand Total by Project"
        data = Reference(ws, min_col=8, max_col=8, min_row=1, max_row=max_row)
        cats = Reference(ws, min_col=1, min_row=2, max_row=max_row)
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)
        chart.y_axis.title = f"Cost ({currency})".strip()
        chart.x_axis.title = "Project"
        chart.height = 10
        chart.width = 18
        ws.add_chart(chart, "J2")

        for name, proj in projects_dict.items():
            dfc = project_components_df(proj)
            if dfc.empty:
                continue
            sheet_name = name[:31]
            dfc.to_excel(writer, sheet_name=sheet_name, index=False)

    output.seek(0)
    return output


def create_comparison_pptx_report_capex(projects_dict, currency=""):
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    layout_title_only = prs.slide_layouts[5]

    slide = prs.slides.add_slide(layout_title_only)
    title = slide.shapes.title
    title.text = "CAPEX Project Comparison"
    p = title.text_frame.paragraphs[0]
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = RGBColor(0, 161, 155)

    rows = []
    for name, proj in projects_dict.items():
        dfc = project_components_df(proj)
        capex = dfc["Base CAPEX (Adj)"].sum() if not dfc.empty else 0.0
        owners = dfc["Owner's Cost"].sum() if not dfc.empty else 0.0
        cont = dfc["Contingency"].sum() if not dfc.empty else 0.0
        esc = dfc["Escalation"].sum() if not dfc.empty else 0.0
        sst = dfc["SST"].sum() if not dfc.empty else 0.0
        grand = dfc["Grand Total"].sum() if not dfc.empty else 0.0
        rows.append({"Project": name, "CAPEX Sum (Adj)": capex, "Owner": owners, "Contingency": cont, "Escalation": esc, "SST": sst, "Grand Total": grand})
    df_proj = pd.DataFrame(rows)

    if not df_proj.empty:
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(df_proj["Project"], df_proj["Grand Total"])
        ax.set_title("Grand Total by Project")
        ax.set_ylabel(f"Cost ({currency})".strip())
        ax.tick_params(axis="x", rotation=25)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        fig.tight_layout()

        img_stream = io.BytesIO()
        fig.savefig(img_stream, format="png", dpi=200, bbox_inches="tight")
        plt.close(fig)
        img_stream.seek(0)

        slide = prs.slides.add_slide(layout_title_only)
        slide.shapes.title.text = "Grand Total by Project"
        slide.shapes.add_picture(img_stream, Inches(0.7), Inches(1.5), width=Inches(8.6))

        fig2, ax2 = plt.subplots(figsize=(7, 4))
        labels = df_proj["Project"]
        base = df_proj["CAPEX Sum (Adj)"]
        owners = df_proj["Owner"]
        cont = df_proj["Contingency"]
        esc = df_proj["Escalation"]
        sst = df_proj["SST"]

        bottom = np.zeros(len(labels))
        for vals, lab in [(base, "Base CAPEX (Adj)"), (owners, "Owner"), (cont, "Contingency"), (esc, "Escalation"), (sst, "SST")]:
            ax2.bar(labels, vals, bottom=bottom, label=lab)
            bottom += np.array(vals)

        ax2.set_title("Cost Composition by Project")
        ax2.set_ylabel(f"Cost ({currency})".strip())
        ax2.tick_params(axis="x", rotation=25)
        ax2.grid(axis="y", linestyle="--", alpha=0.4)
        ax2.legend(fontsize=8, ncol=3)
        fig2.tight_layout()

        img_stream2 = io.BytesIO()
        fig2.savefig(img_stream2, format="png", dpi=200, bbox_inches="tight")
        plt.close(fig2)
        img_stream2.seek(0)

        slide2 = prs.slides.add_slide(layout_title_only)
        slide2.shapes.title.text = "Cost Composition by Project"
        slide2.shapes.add_picture(img_stream2, Inches(0.7), Inches(1.5), width=Inches(8.6))

    output = io.BytesIO()
    prs.save(output)
    output.seek(0)
    return output


# ---------------------------------------------------------------------------------------
# DATA / MODEL HELPERS
# ---------------------------------------------------------------------------------------
GITHUB_USER = "Hafizuddin-Abd-Rahman-Dev-Upstream"
REPO_NAME = "Cost-Predictor"
BRANCH = "main"
DATA_FOLDER = "pages/data_CAPEX"

MODEL_CANDIDATES = {
    "RandomForest": lambda rs=42: RandomForestRegressor(random_state=rs),
    "GradientBoosting": lambda rs=42: GradientBoostingRegressor(random_state=rs),
    "Ridge": lambda rs=42: Ridge(),
    "Lasso": lambda rs=42: Lasso(),
    "SVR": lambda rs=42: SVR(),
    "DecisionTree": lambda rs=42: DecisionTreeRegressor(random_state=rs),
}


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


def evaluate_model(X, y, test_size=0.2, random_state=42):
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=test_size, random_state=random_state)

    rows = []
    best_name = None
    best_r2 = -np.inf
    best_rmse = None

    for name, ctor in MODEL_CANDIDATES.items():
        try:
            base_model = ctor(random_state)
        except TypeError:
            base_model = ctor()

        pipe = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", MinMaxScaler()),
                ("model", base_model),
            ]
        )
        pipe.fit(Xtr, ytr)
        yhat = pipe.predict(Xte)
        rmse = float(np.sqrt(mean_squared_error(yte, yhat)))
        r2 = float(r2_score(yte, yhat))
        rows.append({"model": name, "rmse": rmse, "r2": r2})
        if r2 > best_r2:
            best_r2 = r2
            best_rmse = rmse
            best_name = name

    rows_sorted = sorted(rows, key=lambda d: d["r2"], reverse=True)
    metrics = {"best_model": best_name, "rmse": best_rmse, "r2": best_r2, "models": rows_sorted}
    return metrics


def get_trained_model_for_dataset(X, y, dataset_name: str, random_state=42):
    best_name = st.session_state.best_model_name_per_dataset.get(dataset_name)

    if not best_name:
        metrics = evaluate_model(X, y, test_size=0.2, random_state=random_state)
        best_name = metrics.get("best_model", "RandomForest")
        st.session_state.best_model_name_per_dataset[dataset_name] = best_name
        st.session_state._last_metrics = metrics

    ctor = MODEL_CANDIDATES.get(best_name, MODEL_CANDIDATES["RandomForest"])
    try:
        base_model = ctor(random_state)
    except TypeError:
        base_model = ctor()

    pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", MinMaxScaler()),
            ("model", base_model),
        ]
    )
    pipe.fit(X, y)
    return pipe, best_name


def single_prediction(X, y, payload: dict, dataset_name: str = "default"):
    model_pipe, _ = get_trained_model_for_dataset(X, y, dataset_name=dataset_name)
    cols = list(X.columns)
    row = {c: np.nan for c in cols}
    for c, v in payload.items():
        if c not in row:
            continue
        try:
            row[c] = float(v) if (v is not None and str(v).strip() != "") else np.nan
        except Exception:
            row[c] = np.nan
    df_in = pd.DataFrame([row], columns=cols)
    pred = float(model_pipe.predict(df_in)[0])
    return pred


# ---------------------------------------------------------------------------------------
# NAV ROW — FIVE SHAREPOINT BUTTONS
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
tab_data, tab_pb, tab_compare = st.tabs(["📊 Data", "🏗️ Project Builder", "🔀 Compare Projects"])


# =======================================================================================
# DATA TAB
# =======================================================================================
with tab_data:
    st.markdown('<h3 style="margin-top:0;color:#000;">📁 Data</h3>', unsafe_allow_html=True)

    st.markdown('<h4 style="margin:0;color:#000;">Data Sources</h4><p></p>', unsafe_allow_html=True)
    c1, c2 = st.columns([1.2, 1])
    with c1:
        data_source = st.radio("Choose data source", ["Upload CSV", "Load from Server"], horizontal=True)

    with c2:
        st.caption("Enterprise Storage (SharePoint)")
        data_link = (
            "https://petronas.sharepoint.com/sites/ecm_ups_coe/confidential/"
            "DFE%20Cost%20Engineering/Forms/AllItems.aspx?"
            "id=%2Fsites%2Fecm%5Fups%5Fcoe%2Fconfidential%2FDFE%20Cost%20Engineering"
            "%2F2%2ETemplate%20Tools%2FCost%20Predictor%2FDatabase%2FCAPEX%20%2D%20RT%20Q1%202025"
            "&viewid=25092e6d%2D373d%2D41fe%2D8f6f%2D486cd8cdd5b8"
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
            selected_file = st.selectbox("Choose CSV from GitHub", github_csvs)
            if st.button("Load selected CSV"):
                raw_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{DATA_FOLDER}/{selected_file}"
                try:
                    df = pd.read_csv(raw_url)
                    st.session_state.datasets[selected_file] = df
                    st.session_state.predictions.setdefault(selected_file, [])
                    toast(f"Loaded from GitHub: {selected_file}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error loading CSV: {e}")
        else:
            st.info("No CSV files found in GitHub folder.")

    # If user uploaded
    if uploaded_files:
        for up in uploaded_files:
            if up.name not in st.session_state.datasets:
                try:
                    df = pd.read_csv(up)
                    st.session_state.datasets[up.name] = df
                    st.session_state.predictions.setdefault(up.name, [])
                except Exception as e:
                    st.error(f"Failed to read {up.name}: {e}")
        toast("Dataset(s) added.")

    st.divider()

    cA, cB, cC, cD = st.columns([1, 1, 1, 2])
    with cA:
        if st.button("🧹 Clear all predictions"):
            st.session_state.predictions = {k: [] for k in st.session_state.predictions.keys()}
            toast("All predictions cleared.", "🧹")
            st.rerun()

    with cB:
        if st.button("🧺 Clear processed files history"):
            st.session_state.processed_excel_files = set()
            toast("Processed files history cleared.", "🧺")
            st.rerun()

    with cC:
        if st.button("🔁 Refresh server manifest"):
            list_csvs_from_manifest.clear()
            toast("Server manifest refreshed.", "🔁")
            st.rerun()

    with cD:
        # NEW: Clear uploaded/loaded datasets WITHOUT deleting projects
        if st.button("🗂️ Clear all uploaded / loaded files (keep projects)"):
            st.session_state.datasets = {}
            st.session_state.predictions = {}
            st.session_state.processed_excel_files = set()
            st.session_state._last_metrics = None
            st.session_state.best_model_name_per_dataset = {}

            # Reset dataset selectors so UI stops referencing previous dataset keys
            for k in ["ds_model", "ds_viz", "ds_pred", "ds_results"]:
                if k in st.session_state:
                    del st.session_state[k]

            # Force uploader widget to reset
            st.session_state.uploader_nonce += 1

            toast("All datasets cleared. Projects preserved.", "🗂️")
            st.rerun()

    st.divider()

    # -------------------- OPTIONAL: "Realtime" Market Index / Price Adjustment --------------------
    st.markdown('<h3 style="margin-top:0;color:#000;">📡 Market Index (Realtime Adjustment)</h3>', unsafe_allow_html=True)
    st.caption(
        "This DOES NOT change model training. It adjusts displayed CAPEX outputs by a market index factor (e.g., 1.08 = +8%). "
        "Useful when your lecturer asks for a 'realtime price' overlay."
    )

    mi_mode = st.radio("Index mode", ["Manual", "Upload index CSV"], horizontal=True, key="mi_mode")
    if mi_mode == "Manual":
        mi_val = st.number_input("Market Index Factor", min_value=0.1, max_value=5.0, value=float(st.session_state.market_index["value"]), step=0.01)
        st.session_state.market_index = {"mode": "Manual", "value": float(mi_val), "series": None}
        st.info(f"All predicted base CAPEX will be multiplied by **{mi_val:.3f}** before cost add-ons.")
    else:
        idx_file = st.file_uploader("Upload index CSV (columns: date, index)", type=["csv"], key="idx_uploader")
        if idx_file is not None:
            try:
                idx_df = pd.read_csv(idx_file)
                # normalize col names
                cols = {c.lower().strip(): c for c in idx_df.columns}
                if "date" not in cols or "index" not in cols:
                    st.error("Index CSV must contain columns named: date, index")
                else:
                    dfi = idx_df.rename(columns={cols["date"]: "date", cols["index"]: "index"}).copy()
                    dfi["date"] = pd.to_datetime(dfi["date"], errors="coerce")
                    dfi["index"] = pd.to_numeric(dfi["index"], errors="coerce")
                    dfi = dfi.dropna(subset=["date", "index"]).sort_values("date")
                    if dfi.empty:
                        st.error("Index CSV parsed but ended up empty after cleaning.")
                    else:
                        latest_idx = float(dfi["index"].iloc[-1])
                        st.session_state.market_index = {"mode": "Upload", "value": latest_idx, "series": dfi}
                        st.success(f"Loaded index series. Latest index = {latest_idx:.3f}")
                        fig_idx = px.line(dfi, x="date", y="index", title="Market Index Over Time")
                        st.plotly_chart(fig_idx, use_container_width=True)
            except Exception as e:
                st.error(f"Failed to read index CSV: {e}")

    st.divider()

    # -------------------- Active dataset preview --------------------
    if st.session_state.datasets:
        ds_name_data = st.selectbox("Active dataset", list(st.session_state.datasets.keys()))
        df_active = st.session_state.datasets[ds_name_data]
        currency_active = get_currency_symbol(df_active)
        colA, colB, colC = st.columns([1, 1, 1])
        with colA:
            st.metric("Rows", f"{df_active.shape[0]:,}")
        with colB:
            st.metric("Columns", f"{df_active.shape[1]:,}")
        with colC:
            st.metric("Currency", f"{currency_active or '—'}")
        with st.expander("Preview (first 10 rows)", expanded=False):
            st.dataframe(df_active.head(10), use_container_width=True)
    else:
        st.info("Upload or load a dataset to proceed.")

    # ========================= SECTION: MODEL TRAINING =================================
    st.divider()
    st.markdown('<h3 style="margin-top:0;color:#000;">⚙️ Model</h3>', unsafe_allow_html=True)

    if not st.session_state.datasets:
        st.info("No dataset. Use the Data section above to upload or load.")
    else:
        ds_name_model = st.selectbox("Dataset for model training", list(st.session_state.datasets.keys()), key="ds_model")
        df_model = st.session_state.datasets[ds_name_model]

        with st.spinner("Imputing & preparing..."):
            imputed_model = pd.DataFrame(KNNImputer(n_neighbors=5).fit_transform(df_model), columns=df_model.columns)
            X_model = imputed_model.iloc[:, :-1]
            y_model = imputed_model.iloc[:, -1]

        st.markdown('<h4 style="margin:0;color:#000;">Train & Evaluate</h4><p>Step 2</p>', unsafe_allow_html=True)
        m1, m2 = st.columns([1, 3])
        with m1:
            test_size = st.slider("Test size", 0.1, 0.5, 0.2, 0.05)
            run_train = st.button("Run training")
        with m2:
            st.caption("Automatic best-model selection over 6 regressors (with scaling & imputation).")

        if run_train:
            with st.spinner("Training model..."):
                metrics = evaluate_model(X_model, y_model, test_size=test_size)
            m3, m4 = st.columns(2)
            with m3:
                st.metric("RMSE (best)", f"{metrics['rmse']:,.2f}")
            with m4:
                st.metric("R² (best)", f"{metrics['r2']:.3f}")

            st.session_state._last_metrics = metrics
            st.session_state.best_model_name_per_dataset[ds_name_model] = metrics.get("best_model")

            toast("Training complete.")
            st.caption(f"Best model selected: **{metrics.get('best_model', 'RandomForest')}**")

            try:
                models_list = metrics.get("models", [])
                if models_list:
                    df_models = pd.DataFrame(models_list).set_index("model")
                    st.markdown("##### Model comparison (6-model pool)")
                    styled = (
                        df_models.style.format({"rmse": "{:,.2f}", "r2": "{:.3f}"})
                        .background_gradient(subset=["r2"], cmap="YlGn")
                        .background_gradient(subset=["rmse"], cmap="OrRd_r")
                    )
                    st.dataframe(styled, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not render model comparison table: {e}")

    # ========================= SECTION: VISUALIZATION ==================================
    st.divider()
    st.markdown('<h3 style="margin-top:0;color:#000;">📈 Visualization</h3>', unsafe_allow_html=True)

    if not st.session_state.datasets:
        st.info("No dataset. Use the Data section above to upload or load.")
    else:
        ds_name_viz = st.selectbox("Dataset for visualization", list(st.session_state.datasets.keys()), key="ds_viz")
        df_viz = st.session_state.datasets[ds_name_viz]
        imputed_viz = pd.DataFrame(KNNImputer(n_neighbors=5).fit_transform(df_viz), columns=df_viz.columns)
        X_viz = imputed_viz.iloc[:, :-1]
        y_viz = imputed_viz.iloc[:, -1]
        target_column_viz = y_viz.name

        st.markdown('<h4 style="margin:0;color:#000;">Correlation Matrix</h4><p>Exploration</p>', unsafe_allow_html=True)
        corr = imputed_viz.corr(numeric_only=True)
        fig_corr = px.imshow(corr, text_auto=".2f", aspect="auto", color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
        fig_corr.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_corr, use_container_width=True)

        st.markdown('<h4 style="margin:0;color:#000;">Feature Importance</h4><p>Model</p>', unsafe_allow_html=True)
        scaler_viz = MinMaxScaler().fit(X_viz)
        model_viz = RandomForestRegressor(random_state=42).fit(scaler_viz.transform(X_viz), y_viz)
        importances = model_viz.feature_importances_
        fi = pd.DataFrame({"feature": X_viz.columns, "importance": importances}).sort_values("importance", ascending=True)
        fig_fi = go.Figure(go.Bar(x=fi["importance"], y=fi["feature"], orientation="h"))
        fig_fi.update_layout(xaxis_title="Importance", yaxis_title="Feature", margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_fi, use_container_width=True)

        st.markdown('<h4 style="margin:0;color:#000;">Cost Curve</h4><p>Trend</p>', unsafe_allow_html=True)
        feat = st.selectbox("Select feature for cost curve", X_viz.columns)
        x_vals = imputed_viz[feat].values
        y_vals = y_viz.values
        mask = (~np.isnan(x_vals)) & (~np.isnan(y_vals))
        scatter_df = pd.DataFrame({feat: x_vals[mask], target_column_viz: y_vals[mask]})
        fig_cc = px.scatter(scatter_df, x=feat, y=target_column_viz, opacity=0.65)

        if mask.sum() >= 2 and np.unique(x_vals[mask]).size >= 2:
            xv = scatter_df[feat].to_numpy(dtype=float)
            yv = scatter_df[target_column_viz].to_numpy(dtype=float)
            slope, intercept, r_value, p_value, std_err = linregress(xv, yv)
            x_line = np.linspace(xv.min(), xv.max(), 100)
            y_line = slope * x_line + intercept
            fig_cc.add_trace(
                go.Scatter(
                    x=x_line,
                    y=y_line,
                    mode="lines",
                    name=f"Fit: y={slope:.2f}x+{intercept:.2f} (R²={r_value**2:.3f})",
                )
            )
        else:
            st.warning("Not enough valid/variable data to compute regression.")
        fig_cc.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_cc, use_container_width=True)

    # ========================= SECTION: PREDICT =======================================
    st.divider()
    st.markdown('<h3 style="margin-top:0;color:#000;">🎯 Predict</h3>', unsafe_allow_html=True)

    if not st.session_state.datasets:
        st.info("No dataset. Use the Data section above to upload or load.")
    else:
        ds_name_pred = st.selectbox("Dataset for prediction", list(st.session_state.datasets.keys()), key="ds_pred")
        df_pred = st.session_state.datasets[ds_name_pred]
        currency_pred = get_currency_symbol(df_pred)

        imputed_pred = pd.DataFrame(KNNImputer(n_neighbors=5).fit_transform(df_pred), columns=df_pred.columns)
        X_pred, y_pred = imputed_pred.iloc[:, :-1], imputed_pred.iloc[:, -1]
        target_column_pred = y_pred.name

        st.markdown('<h4 style="margin:0;color:#000;">Configuration (EPRR • Financial)</h4><p>Step 3</p>', unsafe_allow_html=True)

        # Plus/minus style: number_input with step (shows +/- controls)
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("**EPRR Breakdown (%)**")
            eng = st.number_input("Engineering (%)", min_value=0.0, max_value=100.0, value=12.0, step=1.0)
            prep = st.number_input("Preparation (%)", min_value=0.0, max_value=100.0, value=7.0, step=1.0)
            remv = st.number_input("Removal (%)", min_value=0.0, max_value=100.0, value=54.0, step=1.0)
            remd = st.number_input("Remediation (%)", min_value=0.0, max_value=100.0, value=27.0, step=1.0)

            eprr = {"Engineering": eng, "Preparation": prep, "Removal": remv, "Remediation": remd}
            eprr_total = sum(eprr.values())
            st.caption(f"EPRR total: **{eprr_total:.2f}%**")

            ncol1, ncol2 = st.columns(2)
            with ncol1:
                if st.button("Normalize EPRR to 100%"):
                    normed, _ = normalize_to_100(eprr)
                    # Re-run by storing into session state inputs is complex; instead we apply normalization at compute time:
                    st.session_state["_eprr_normalize_now"] = True
                    st.success("Normalization will be applied for this run.")
            with ncol2:
                if st.button("Stop normalization"):
                    st.session_state["_eprr_normalize_now"] = False

        with c2:
            st.markdown("**Financial (%)**")
            sst_pct = st.number_input("SST (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
            owners_pct = st.number_input("Owner's Cost (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
            cont_pct = st.number_input("Contingency (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
            esc_pct = st.number_input("Escalation & Inflation (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)

        # Apply normalization at compute-time if user asked for it
        apply_norm = bool(st.session_state.get("_eprr_normalize_now", False))
        if apply_norm and eprr_total > 0 and abs(eprr_total - 100.0) > 1e-6:
            eprr, _ = normalize_to_100(eprr)

        st.markdown('<h4 style="margin:0;color:#000;">Predict (Single)</h4><p>Step 4</p>', unsafe_allow_html=True)

        project_name = st.text_input("Project Name", placeholder="e.g., Offshore Pipeline Replacement 2025")
        st.caption("Provide feature values (leave blank for NaN).")

        cols_per_row = 3
        new_data = {}
        cols_pred = list(X_pred.columns)
        rows = (len(cols_pred) + cols_per_row - 1) // cols_per_row
        for r in range(rows):
            row_cols = st.columns(cols_per_row)
            for i in range(cols_per_row):
                idx = r * cols_per_row + i
                if idx < len(cols_pred):
                    col_name = cols_pred[idx]
                    with row_cols[i]:
                        val = st.text_input(col_name, key=f"in_{ds_name_pred}_{col_name}")
                        new_data[col_name] = val

        if st.button("Run Prediction"):
            market_index = float(st.session_state.market_index.get("value", 1.0))
            pred_val = single_prediction(X_pred, y_pred, new_data, dataset_name=ds_name_pred)

            breakdown = cost_breakdown(
                pred_val,
                eprr=eprr,
                sst_pct=sst_pct,
                owners_pct=owners_pct,
                cont_pct=cont_pct,
                esc_pct=esc_pct,
                market_index=market_index,
            )

            result = {"Project Name": project_name}
            result.update({c: new_data.get(c, "") for c in cols_pred})
            result[target_column_pred] = round(breakdown["base_capex_adjusted"], 2)

            for k, v in breakdown["eprr_costs"].items():
                result[f"{k} Cost"] = v

            result["SST Cost"] = breakdown["sst_cost"]
            result["Owner's Cost"] = breakdown["owners_cost"]
            result["Cost Contingency"] = breakdown["contingency_cost"]
            result["Escalation & Inflation"] = breakdown["escalation_cost"]
            result["Grand Total"] = breakdown["grand_total"]
            result["Market Index"] = breakdown["market_index"]
            result["Base CAPEX (Raw)"] = breakdown["base_capex_raw"]

            st.session_state.predictions.setdefault(ds_name_pred, []).append(result)
            toast("Prediction added to Results.")

            cA, cB, cC, cD, cE = st.columns(5)
            with cA:
                st.metric("Base CAPEX (Adj)", f"{currency_pred} {breakdown['base_capex_adjusted']:,.2f}")
            with cB:
                st.metric("Owner's", f"{currency_pred} {breakdown['owners_cost']:,.2f}")
            with cC:
                st.metric("Contingency", f"{currency_pred} {breakdown['contingency_cost']:,.2f}")
            with cD:
                st.metric("Escalation", f"{currency_pred} {breakdown['escalation_cost']:,.2f}")
            with cE:
                st.metric("Grand Total", f"{currency_pred} {breakdown['grand_total']:,.2f}")

            # Optional: show realtime/market overlay if index series exists
            if st.session_state.market_index.get("series") is not None:
                df_i = st.session_state.market_index["series"]
                overlay = df_i.copy()
                overlay["Base CAPEX (Raw)"] = breakdown["base_capex_raw"]
                overlay["Base CAPEX (Adj)"] = overlay["Base CAPEX (Raw)"] * overlay["index"]
                fig_overlay = px.line(overlay, x="date", y="Base CAPEX (Adj)", title="Base CAPEX adjusted by market index over time")
                st.plotly_chart(fig_overlay, use_container_width=True)

        st.markdown('<h4 style="margin:0;color:#000;">Batch (Excel)</h4>', unsafe_allow_html=True)
        xls = st.file_uploader("Upload Excel for batch prediction", type=["xlsx"], key="batch_xlsx")
        if xls:
            file_id = f"{xls.name}_{xls.size}_{ds_name_pred}"
            if file_id not in st.session_state.processed_excel_files:
                batch_df = pd.read_excel(xls)
                missing = [c for c in X_pred.columns if c not in batch_df.columns]
                if missing:
                    st.error(f"Missing required columns in Excel: {missing}")
                else:
                    market_index = float(st.session_state.market_index.get("value", 1.0))
                    model_pipe, best_name = get_trained_model_for_dataset(X_pred, y_pred, dataset_name=ds_name_pred)
                    preds = model_pipe.predict(batch_df[X_pred.columns])

                    for i, row in batch_df.iterrows():
                        name = row.get("Project Name", f"Project {i+1}")

                        breakdown = cost_breakdown(
                            float(preds[i]),
                            eprr=eprr,
                            sst_pct=sst_pct,
                            owners_pct=owners_pct,
                            cont_pct=cont_pct,
                            esc_pct=esc_pct,
                            market_index=market_index,
                        )

                        entry = {"Project Name": name}
                        entry.update(row[X_pred.columns].to_dict())
                        entry[target_column_pred] = round(breakdown["base_capex_adjusted"], 2)

                        for k, v in breakdown["eprr_costs"].items():
                            entry[f"{k} Cost"] = v
                        entry["SST Cost"] = breakdown["sst_cost"]
                        entry["Owner's Cost"] = breakdown["owners_cost"]
                        entry["Cost Contingency"] = breakdown["contingency_cost"]
                        entry["Escalation & Inflation"] = breakdown["escalation_cost"]
                        entry["Grand Total"] = breakdown["grand_total"]
                        entry["Market Index"] = breakdown["market_index"]
                        entry["Base CAPEX (Raw)"] = breakdown["base_capex_raw"]

                        st.session_state.predictions.setdefault(ds_name_pred, []).append(entry)

                    st.session_state.processed_excel_files.add(file_id)
                    toast("Batch prediction complete.")
                    st.rerun()
            else:
                st.info("This batch file was already processed (history prevents duplicates).")

    # ========================= SECTION: RESULTS / EXPORT ==============================
    st.divider()
    st.markdown('<h3 style="margin-top:0;color:#000;">📄 Results</h3>', unsafe_allow_html=True)

    if not st.session_state.datasets:
        st.info("No dataset. Use the Data section above to upload or load.")
    else:
        ds_name_res = st.selectbox("Dataset", list(st.session_state.datasets.keys()), key="ds_results")
        preds = st.session_state.predictions.get(ds_name_res, [])

        st.markdown(f'<h4 style="margin:0;color:#000;">Project Entries</h4><p>{len(preds)} saved</p>', unsafe_allow_html=True)
        if preds:
            if st.button("🗑️ Delete all entries"):
                st.session_state.predictions[ds_name_res] = []
                to_remove = {fid for fid in st.session_state.processed_excel_files if fid.endswith(ds_name_res)}
                for fid in to_remove:
                    st.session_state.processed_excel_files.remove(fid)
                toast("All entries removed.", "🗑️")
                st.rerun()

        st.markdown('<h4 style="margin:0;color:#000;">Summary Table & Export</h4><p>Download</p>', unsafe_allow_html=True)

        if preds:
            df_preds = pd.DataFrame(preds)
            df_disp = df_preds.copy()
            num_cols = df_disp.select_dtypes(include=[np.number]).columns
            for col in num_cols:
                df_disp[col] = df_disp[col].apply(lambda x: format_with_commas(x))
            st.dataframe(df_disp, use_container_width=True, height=420)

            # Extra graph: "realtime adjusted vs raw" for your lecturer
            if "Base CAPEX (Raw)" in df_preds.columns and "Market Index" in df_preds.columns:
                try:
                    gdf = df_preds.copy()
                    gdf["Base CAPEX (Raw)"] = pd.to_numeric(gdf["Base CAPEX (Raw)"], errors="coerce")
                    gdf["Market Index"] = pd.to_numeric(gdf["Market Index"], errors="coerce")
                    gdf["Base CAPEX (Adj)"] = gdf["Base CAPEX (Raw)"] * gdf["Market Index"]
                    gdf = gdf.dropna(subset=["Base CAPEX (Raw)", "Base CAPEX (Adj)"])
                    if not gdf.empty:
                        fig_rt = px.bar(
                            gdf,
                            x="Project Name",
                            y=["Base CAPEX (Raw)", "Base CAPEX (Adj)"],
                            barmode="group",
                            title="Base CAPEX Raw vs Market-Adjusted (Realtime Overlay)",
                        )
                        st.plotly_chart(fig_rt, use_container_width=True)
                except Exception:
                    pass

            bio_xlsx = io.BytesIO()
            df_preds.to_excel(bio_xlsx, index=False, engine="openpyxl")
            bio_xlsx.seek(0)

            metrics = st.session_state._last_metrics
            metrics_json = json.dumps(metrics if metrics else {"info": "No metrics"}, indent=2, default=float)

            zip_bio = io.BytesIO()
            with zipfile.ZipFile(zip_bio, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(f"{ds_name_res}_predictions.xlsx", bio_xlsx.getvalue())
                zf.writestr(f"{ds_name_res}_metrics.json", metrics_json)
            zip_bio.seek(0)

            st.download_button(
                "⬇️ Download All (ZIP)",
                data=zip_bio.getvalue(),
                file_name=f"{ds_name_res}_capex_all.zip",
                mime="application/zip",
            )
        else:
            st.info("No data to export yet.")


# =======================================================================================
# PROJECT BUILDER TAB
# =======================================================================================
with tab_pb:
    st.markdown('<h4 style="margin:0;color:#000;">Project Builder</h4><p>Assemble multi-component CAPEX projects</p>', unsafe_allow_html=True)

    if not st.session_state.datasets:
        st.info("No dataset. Go to **Data** tab to upload or load.")
    else:
        colA, colB = st.columns([2, 1])
        with colA:
            new_project_name = st.text_input("New Project Name", placeholder="e.g., CAPEX 2026", key="pb_new_project_name")
        with colB:
            if new_project_name and new_project_name not in st.session_state.projects:
                if st.button("Create Project", key="pb_create_project_btn"):
                    st.session_state.projects[new_project_name] = {"components": [], "totals": {}, "currency": ""}
                    toast(f"Project '{new_project_name}' created.")
                    st.rerun()

        if not st.session_state.projects:
            st.info("Create a project above, then add components.")
        else:
            existing_projects = list(st.session_state.projects.keys())
            proj_sel = st.selectbox("Select project to work on", existing_projects, key="pb_project_select")

            ds_names = sorted(st.session_state.datasets.keys())
            dataset_for_comp = st.selectbox("Dataset for this component", ds_names, key="pb_dataset_for_component")

            df_comp = st.session_state.datasets[dataset_for_comp]
            currency_ds = get_currency_symbol(df_comp)

            imputed_comp = pd.DataFrame(KNNImputer(n_neighbors=5).fit_transform(df_comp), columns=df_comp.columns)
            X_comp = imputed_comp.iloc[:, :-1]
            y_comp = imputed_comp.iloc[:, -1]
            target_column_comp = y_comp.name

            default_label = st.session_state.component_labels.get(dataset_for_comp, "")
            component_type = st.text_input(
                "Component type (Asset / Scope)",
                value=(default_label or "Platform / Pipeline / Subsea / Well"),
                key=f"pb_component_type_{proj_sel}",
            )

            st.markdown("**Component Feature Inputs**")
            feat_cols = list(X_comp.columns)
            comp_inputs = {}
            cols_per_row = 2
            rows = (len(feat_cols) + cols_per_row - 1) // cols_per_row
            for r in range(rows):
                row_cols = st.columns(cols_per_row)
                for i in range(cols_per_row):
                    idx = r * cols_per_row + i
                    if idx < len(feat_cols):
                        col_name = feat_cols[idx]
                        with row_cols[i]:
                            key = f"pb_{proj_sel}_{dataset_for_comp}_feat_{col_name}"
                            comp_inputs[col_name] = st.text_input(col_name, key=key)

            st.markdown("---")
            st.markdown("**Cost Percentage Inputs**")
            cp1, cp2 = st.columns(2)
            with cp1:
                st.markdown("EPRR (%) — use +/-")
                eng_pb = st.number_input("Engineering", 0.0, 100.0, 12.0, 1.0, key=f"pb_eng_{proj_sel}")
                prep_pb = st.number_input("Preparation", 0.0, 100.0, 7.0, 1.0, key=f"pb_prep_{proj_sel}")
                remv_pb = st.number_input("Removal", 0.0, 100.0, 54.0, 1.0, key=f"pb_remv_{proj_sel}")
                remd_pb = st.number_input("Remediation", 0.0, 100.0, 27.0, 1.0, key=f"pb_remd_{proj_sel}")

                eprr_pb = {"Engineering": eng_pb, "Preparation": prep_pb, "Removal": remv_pb, "Remediation": remd_pb}
                eprr_total_pb = sum(eprr_pb.values())
                st.caption(f"EPRR total: **{eprr_total_pb:.2f}%**")
                apply_norm_pb = st.checkbox("Normalize to 100% for this component", value=False, key=f"pb_norm_{proj_sel}")
                if apply_norm_pb and eprr_total_pb > 0 and abs(eprr_total_pb - 100.0) > 1e-6:
                    eprr_pb, _ = normalize_to_100(eprr_pb)

            with cp2:
                st.markdown("Financial (%) — use +/-")
                sst_pb = st.number_input("SST", 0.0, 100.0, 0.0, 0.5, key=f"pb_sst_{proj_sel}")
                owners_pb = st.number_input("Owner's Cost", 0.0, 100.0, 0.0, 0.5, key=f"pb_owners_{proj_sel}")
                cont_pb = st.number_input("Contingency", 0.0, 100.0, 0.0, 0.5, key=f"pb_cont_{proj_sel}")
                esc_pb = st.number_input("Escalation & Inflation", 0.0, 100.0, 0.0, 0.5, key=f"pb_esc_{proj_sel}")

            if st.button("➕ Predict & Add Component", key=f"pb_add_comp_{proj_sel}_{dataset_for_comp}"):
                row_payload = {}
                for f in feat_cols:
                    v = comp_inputs.get(f, "")
                    if v is None or str(v).strip() == "":
                        row_payload[f] = np.nan
                    else:
                        try:
                            row_payload[f] = float(v)
                        except Exception:
                            row_payload[f] = np.nan

                try:
                    market_index = float(st.session_state.market_index.get("value", 1.0))
                    base_pred_raw = single_prediction(X_comp, y_comp, row_payload, dataset_name=dataset_for_comp)

                    breakdown = cost_breakdown(
                        base_pred_raw,
                        eprr=eprr_pb,
                        sst_pct=sst_pb,
                        owners_pct=owners_pb,
                        cont_pct=cont_pb,
                        esc_pct=esc_pb,
                        market_index=market_index,
                    )

                    _, best_name = get_trained_model_for_dataset(X_comp, y_comp, dataset_name=dataset_for_comp)

                    comp_entry = {
                        "component_type": component_type or default_label or "Component",
                        "dataset": dataset_for_comp,
                        "model_used": best_name,
                        "inputs": {k: row_payload[k] for k in feat_cols},
                        "prediction_raw": base_pred_raw,
                        "breakdown": {
                            **breakdown,
                            "eprr_pct": eprr_pb,
                            "sst_pct": sst_pb,
                            "owners_pct": owners_pb,
                            "cont_pct": cont_pb,
                            "esc_pct": esc_pb,
                            "target_col": target_column_comp,
                        },
                    }

                    st.session_state.projects[proj_sel]["components"].append(comp_entry)
                    st.session_state.component_labels[dataset_for_comp] = component_type or default_label
                    if not st.session_state.projects[proj_sel]["currency"]:
                        st.session_state.projects[proj_sel]["currency"] = currency_ds

                    toast(f"Component added to project '{proj_sel}'.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to predict component CAPEX: {e}")

            st.markdown("---")
            st.markdown("### Current Project Overview")

            proj = st.session_state.projects[proj_sel]
            comps = proj.get("components", [])
            if not comps:
                st.info("No components yet. Add at least one above.")
            else:
                dfc = project_components_df(proj)
                curr = proj.get("currency", "") or currency_ds

                st.dataframe(
                    dfc.style.format(
                        {"Base CAPEX (Adj)": "{:,.2f}", "Grand Total": "{:,.2f}", "Market Index": "{:.3f}"}
                    ),
                    use_container_width=True,
                )

                total_capex = float(dfc["Base CAPEX (Adj)"].sum())
                total_grand = float(dfc["Grand Total"].sum())
                proj["totals"] = {"capex_sum": total_capex, "grand_total": total_grand}

                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    st.metric("Project CAPEX (Adjusted)", f"{curr} {total_capex:,.2f}")
                with col_t2:
                    st.metric("Project Grand Total", f"{curr} {total_grand:,.2f}")

                st.markdown("#### Component Cost Composition")
                comp_cost_rows = []
                for c in comps:
                    comp_cost_rows.append(
                        {
                            "Component": c["component_type"],
                            "CAPEX": float(c["breakdown"]["base_capex_adjusted"]),
                            "Owner": float(c["breakdown"]["owners_cost"]),
                            "Contingency": float(c["breakdown"]["contingency_cost"]),
                            "Escalation": float(c["breakdown"]["escalation_cost"]),
                            "SST": float(c["breakdown"]["sst_cost"]),
                        }
                    )
                df_cost = pd.DataFrame(comp_cost_rows)
                if not df_cost.empty:
                    df_melt = df_cost.melt(id_vars="Component", var_name="Cost Type", value_name="Value")
                    fig_stack = px.bar(
                        df_melt,
                        x="Component",
                        y="Value",
                        color="Cost Type",
                        barmode="stack",
                        labels={"Value": f"Cost ({curr})"},
                    )
                    st.plotly_chart(fig_stack, use_container_width=True)

                st.markdown("#### Components")
                for idx, c in enumerate(comps):
                    col1, col2, col3 = st.columns([4, 2, 1])
                    with col1:
                        st.write(f"**{c['component_type']}** — *{c['dataset']}* — {c.get('model_used', 'N/A')}")
                    with col2:
                        st.write(f"Grand Total: {curr} {c['breakdown']['grand_total']:,.2f}")
                    with col3:
                        if st.button("🗑️", key=f"pb_del_comp_{proj_sel}_{idx}"):
                            comps.pop(idx)
                            toast("Component removed.", "🗑️")
                            st.rerun()

                st.markdown("---")
                st.markdown("#### Export / Import Project")

                col_dl1, col_dl2, col_dl3 = st.columns(3)

                with col_dl1:
                    excel_report = create_project_excel_report_capex(proj_sel, proj, curr)
                    st.download_button(
                        "⬇️ Download Project Excel",
                        data=excel_report,
                        file_name=f"{proj_sel}_CAPEX_Report.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

                with col_dl2:
                    pptx_report = create_project_pptx_report_capex(proj_sel, proj, curr)
                    st.download_button(
                        "⬇️ Download Project PowerPoint",
                        data=pptx_report,
                        file_name=f"{proj_sel}_CAPEX_Report.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    )

                with col_dl3:
                    st.download_button(
                        "⬇️ Download Project (JSON)",
                        data=json.dumps(proj, indent=2, default=float),
                        file_name=f"{proj_sel}.json",
                        mime="application/json",
                    )

                up_json = st.file_uploader("Import project JSON", type=["json"], key=f"pb_import_{proj_sel}")
                if up_json is not None:
                    try:
                        data = json.load(up_json)
                        st.session_state.projects[proj_sel] = data
                        toast("Project imported successfully.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to import project JSON: {e}")


# =======================================================================================
# COMPARE PROJECTS TAB
# =======================================================================================
with tab_compare:
    st.markdown('<h4 style="margin:0;color:#000;">Compare Projects</h4><p>Portfolio-level CAPEX view</p>', unsafe_allow_html=True)

    proj_names = list(st.session_state.projects.keys())
    if len(proj_names) < 2:
        st.info("Create at least two projects in the Project Builder tab to compare.")
    else:
        compare_sel = st.multiselect("Select projects to compare", proj_names, default=proj_names[:2], key="compare_projects_sel")

        if len(compare_sel) < 2:
            st.warning("Select at least two projects for a meaningful comparison.")
        else:
            rows = []
            for p in compare_sel:
                proj = st.session_state.projects[p]
                dfc = project_components_df(proj)
                capex = float(dfc["Base CAPEX (Adj)"].sum()) if not dfc.empty else 0.0
                owners = float(dfc["Owner's Cost"].sum()) if not dfc.empty else 0.0
                cont = float(dfc["Contingency"].sum()) if not dfc.empty else 0.0
                esc = float(dfc["Escalation"].sum()) if not dfc.empty else 0.0
                sst = float(dfc["SST"].sum()) if not dfc.empty else 0.0
                grand_total = float(dfc["Grand Total"].sum()) if not dfc.empty else 0.0

                proj["totals"] = {"capex_sum": capex, "grand_total": grand_total}
                rows.append(
                    {
                        "Project": p,
                        "Components": len(proj.get("components", [])),
                        "CAPEX Sum (Adj)": capex,
                        "Owner": owners,
                        "Contingency": cont,
                        "Escalation": esc,
                        "SST": sst,
                        "Grand Total": grand_total,
                        "Currency": proj.get("currency", ""),
                    }
                )

            df_proj = pd.DataFrame(rows)

            st.dataframe(
                df_proj[["Project", "Components", "CAPEX Sum (Adj)", "Grand Total"]].style.format(
                    {"CAPEX Sum (Adj)": "{:,.2f}", "Grand Total": "{:,.2f}"}
                ),
                use_container_width=True,
            )

            st.markdown("#### Grand Total by Project")
            fig_gt = px.bar(df_proj, x="Project", y="Grand Total", text="Grand Total", barmode="group")
            fig_gt.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
            st.plotly_chart(fig_gt, use_container_width=True)

            st.markdown("#### Stacked Cost Composition by Project")
            df_melt = df_proj.melt(
                id_vars=["Project"],
                value_vars=["CAPEX Sum (Adj)", "Owner", "Contingency", "Escalation", "SST"],
                var_name="Cost Type",
                value_name="Value",
            )
            fig_comp = px.bar(df_melt, x="Project", y="Value", color="Cost Type", barmode="stack")
            st.plotly_chart(fig_comp, use_container_width=True)

            st.markdown("#### Component-Level Details")
            for p in compare_sel:
                proj = st.session_state.projects[p]
                comps = proj.get("components", [])
                if not comps:
                    continue
                with st.expander(f"Project: {p}"):
                    rows_c = []
                    for c in comps:
                        eprr_costs = c["breakdown"].get("eprr_costs", {})
                        eprr_str = ", ".join(f"{k}: {v:,.0f}" for k, v in eprr_costs.items() if float(v) != 0)
                        rows_c.append(
                            {
                                "Component": c["component_type"],
                                "Dataset": c["dataset"],
                                "Base CAPEX (Adj)": c["breakdown"]["base_capex_adjusted"],
                                "Owner": c["breakdown"]["owners_cost"],
                                "Contingency": c["breakdown"]["contingency_cost"],
                                "Escalation": c["breakdown"]["escalation_cost"],
                                "SST": c["breakdown"]["sst_cost"],
                                "Grand Total": c["breakdown"]["grand_total"],
                                "EPRR Costs": eprr_str,
                                "Market Index": c["breakdown"].get("market_index", 1.0),
                            }
                        )
                    df_compd = pd.DataFrame(rows_c)
                    st.dataframe(
                        df_compd.style.format(
                            {
                                "Base CAPEX (Adj)": "{:,.2f}",
                                "Owner": "{:,.2f}",
                                "Contingency": "{:,.2f}",
                                "Escalation": "{:,.2f}",
                                "SST": "{:,.2f}",
                                "Grand Total": "{:,.2f}",
                                "Market Index": "{:.3f}",
                            }
                        ),
                        use_container_width=True,
                    )

            st.markdown("---")
            st.markdown("#### Download Comparison Reports")

            col_c1, col_c2 = st.columns(2)
            projects_to_export = {name: st.session_state.projects[name] for name in compare_sel}
            currency_comp = st.session_state.projects[compare_sel[0]].get("currency", "")

            with col_c1:
                excel_comp = create_comparison_excel_report_capex(projects_to_export, currency_comp)
                st.download_button(
                    "⬇️ Download Comparison Excel",
                    data=excel_comp,
                    file_name="CAPEX_Projects_Comparison.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

            with col_c2:
                pptx_comp = create_comparison_pptx_report_capex(projects_to_export, currency_comp)
                st.download_button(
                    "⬇️ Download Comparison PowerPoint",
                    data=pptx_comp,
                    file_name="CAPEX_Projects_Comparison.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                )
