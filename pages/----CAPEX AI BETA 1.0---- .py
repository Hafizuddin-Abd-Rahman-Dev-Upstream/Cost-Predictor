import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np
from scipy.stats import linregress
from sklearn.impute import KNNImputer
import io
import requests
from matplotlib.ticker import FuncFormatter
import json

#Hide Streamlit header icons (commented out, not executed)
#st.markdown("""
    #<style>
    #[data-testid="stShareButton"],  /* Share button */
    #[data-testid="stFavoriteButton"], /* Star icon */
    #[data-testid="stToolbar"],  /* Toolbar (may include pencil, GitHub, etc.) */
    #.stActionButton {display: none !important;}
    #</style>
#""", unsafe_allow_html=True)

st.set_page_config(
    page_title="CAPEX AI RT2025",
    page_icon="💲",
    initial_sidebar_state="expanded",
    layout="wide"
)

# ---------------------------------------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Load approved emails from file & password from secrets
APPROVED_EMAILS = st.secrets.get("emails", [])
correct_password = st.secrets.get("password", None)

if not st.session_state.authenticated:
    with st.form("login_form"):
        st.markdown("#### 🔐 Access Required", unsafe_allow_html=True)
        email = st.text_input("Email Address")
        password = st.text_input("Enter Access Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if email in APPROVED_EMAILS and password == correct_password:
                st.session_state.authenticated = True
                st.success("✅ Access granted.")
                st.rerun()
            else:
                st.error("❌ Invalid email or password. Please contact Cost Engineering Focal for access")
    st.stop()

# ---------------------------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------------------------------------
if "datasets" not in st.session_state:
    st.session_state.datasets = {}
if "predictions" not in st.session_state:
    st.session_state.predictions = {}
if "processed_excel_files" not in st.session_state:
    st.session_state.processed_excel_files = set()
if "projects" not in st.session_state:
    st.session_state.projects = {}
if "component_labels" not in st.session_state:
    st.session_state.component_labels = {}
if "widget_nonce" not in st.session_state:
    st.session_state.widget_nonce = 0

# ---------------------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------------------
GITHUB_USER = "Hafizuddin-Abd-Rahman-Dev-Upstream"
REPO_NAME = "Cost-Predictor"
BRANCH = "main"
DATA_FOLDER = "pages/data_CAPEX"

@st.cache_data(ttl=600)
def list_csvs_from_manifest(folder_path):
    manifest_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{folder_path}/files.json"
    try:
        res = requests.get(manifest_url)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"Failed to load CSV manifest: {e}")
        return []

def human_format(num, pos=None):
    if num >= 1e9:
        return f'{num/1e9:.1f}B'
    elif num >= 1e6:
        return f'{num/1e6:.1f}M'
    elif num >= 1e3:
        return f'{num/1e3:.1f}K'
    else:
        return f'{num:.0f}'

def format_with_commas(num):
    return f"{num:,.2f}"

def get_currency_symbol(df):
    for col in df.columns:
        if 'MYR' in col.upper() or 'RM' in col:
            return 'MYR'
        elif 'USD' in col.upper() or '$' in col:
            return 'USD'
        elif 'EUR' in col.upper() or '€' in col:
            return 'EUR'
        elif 'GBP' in col.upper() or '£' in col:
            return 'GBP'
    return ''

def format_currency(amount, currency=''):
    return f"{currency} {amount:.2f}"

def download_all_predictions():
    # Safe check for predictions
    if 'predictions' not in st.session_state or not st.session_state['predictions']:
        st.sidebar.error("No predictions available to download")
        return
    
    # Check if any dataset actually has predictions
    has_predictions = False
    for predictions in st.session_state['predictions'].values():
        if predictions:  # Check if list is not empty
            has_predictions = True
            break
    
    if not has_predictions:
        st.sidebar.error("No predictions available to download")
        return
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        summary_data = []
        for dataset_name, predictions in st.session_state['predictions'].items():
            if predictions:
                for pred in predictions:
                    pred_copy = pred.copy()
                    pred_copy['Dataset'] = dataset_name.replace('.csv', '')
                    summary_data.append(pred_copy)
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='All Predictions', index=False)
        for dataset_name, predictions in st.session_state['predictions'].items():
            if predictions:
                sheet_name = dataset_name.replace('.csv', '')
                if len(sheet_name) > 31:
                    sheet_name = sheet_name[:31]
                predictions_df = pd.DataFrame(predictions)
                predictions_df.to_excel(writer, sheet_name=sheet_name, index=False)
    output.seek(0)
    st.sidebar.download_button(
        label="📥 Download All Predictions",
        data=output,
        file_name="All_Predictions.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def cost_breakdown(base_pred, epcic, predev_pct, owners_pct, cont_pct, esc_pct):
    base_pred = float(base_pred)
    
    owners_cost = round(base_pred * (owners_pct / 100.0), 2)
    predev_cost = round(base_pred * (predev_pct / 100.0), 2)
    
    contingency_cost = round((base_pred + owners_cost) * (cont_pct / 100.0), 2)
    escalation_cost = round((base_pred + owners_cost) * (esc_pct / 100.0), 2)
    
    epcic_costs = {k: round(base_pred * (float(v) / 100.0), 2) for k, v in (epcic or {}).items()}
    
    grand_total = round(base_pred + owners_cost + predev_cost + contingency_cost + escalation_cost, 2)
    return owners_cost, predev_cost, contingency_cost, escalation_cost, epcic_costs, grand_total

def project_components_df(proj):
    comps = proj.get("components", [])
    rows = []
    for c in comps:
        # Safely get the breakdown dictionary
        breakdown = c.get("breakdown", {})
        
        # For backward compatibility, check both old and new keys
        # Some older projects might have "sst_cost" instead of "predev_cost"
        predev_cost = breakdown.get("predev_cost")
        if predev_cost is None:
            predev_cost = breakdown.get("sst_cost", 0.0)  # Try old key
        
        rows.append(
            {
                "Component": c.get("component_type", "Unknown"),
                "Dataset": c.get("dataset", "Unknown"),
                "Base CAPEX": float(c.get("prediction", 0.0)),
                "Owner's Cost": float(breakdown.get("owners_cost", 0.0)),
                "Contingency": float(breakdown.get("contingency_cost", 0.0)),
                "Escalation": float(breakdown.get("escalation_cost", 0.0)),
                "Pre-Development": float(predev_cost),  # Fixed with fallback
                "Grand Total": float(breakdown.get("grand_total", 0.0)),
            }
        )
    return pd.DataFrame(rows)

def project_totals(proj):
    dfc = project_components_df(proj)
    if dfc.empty:
        return {"capex_sum": 0.0, "owners": 0.0, "cont": 0.0, "esc": 0.0, "predev": 0.0, "grand_total": 0.0}
    return {
        "capex_sum": float(dfc["Base CAPEX"].sum()),
        "owners": float(dfc["Owner's Cost"].sum()),
        "cont": float(dfc["Contingency"].sum()),
        "esc": float(dfc["Escalation"].sum()),
        "predev": float(dfc["Pre-Development"].sum()),
        "grand_total": float(dfc["Grand Total"].sum()),
    }

def single_prediction(rf_model, scaler, X_columns, payload):
    df_input = pd.DataFrame([payload])
    # Ensure all required columns are present
    for col in X_columns:
        if col not in df_input.columns:
            df_input[col] = np.nan
    input_scaled = scaler.transform(df_input[X_columns])
    return float(rf_model.predict(input_scaled)[0])

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
    
    totals = project_totals(proj)
    
    summary_df = comps_df.copy()
    summary_df.loc[len(summary_df)] = {
        "Component": "TOTAL",
        "Dataset": "",
        "Base CAPEX": totals["capex_sum"],
        "Owner's Cost": totals["owners"],
        "Contingency": totals["cont"],
        "Escalation": totals["esc"],
        "Pre-Development": totals["predev"],
        "Grand Total": totals["grand_total"],
    }
    
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        comps_df.to_excel(writer, sheet_name="Components Detail", index=False)
    
    output.seek(0)
    return output

# ---------------------------------------------------------------------------------------
# MAIN APP
# ---------------------------------------------------------------------------------------
def main():
    st.title('💲CAPEX AI RT2025💲')
    
    # Initialize session state
    if 'datasets' not in st.session_state:
        st.session_state['datasets'] = {}
    if 'predictions' not in st.session_state:
        st.session_state['predictions'] = {}
    if 'processed_excel_files' not in st.session_state:
        st.session_state['processed_excel_files'] = set()
    if 'projects' not in st.session_state:
        st.session_state.projects = {}
    if 'component_labels' not in st.session_state:
        st.session_state.component_labels = {}
    if 'widget_nonce' not in st.session_state:
        st.session_state.widget_nonce = 0
    
    # Create tabs
    tab_data, tab_pb = st.tabs(["📊 Data", "🏗️ Project Builder"])
    
    # =======================================================================================
    # DATA TAB
    # =======================================================================================
    with tab_data:
        st.sidebar.header('Data Controls')
        
        if st.sidebar.button("Clear all predictions"):
            # Clear predictions safely
            st.session_state['predictions'] = {}
            # Also initialize empty lists for each dataset
            for dataset_name in st.session_state.get('datasets', {}).keys():
                st.session_state['predictions'][dataset_name] = []
            st.sidebar.success("All predictions cleared!")
            st.rerun()
            
        if st.sidebar.button("Clear processed files history"):
            st.session_state['processed_excel_files'] = set()
            st.sidebar.success("Processed files history cleared!")
            st.rerun()
            
        if st.sidebar.button("📥 Download All Predictions"):
            download_all_predictions()
                
        # Add horizontal line in sidebar
        st.sidebar.markdown('---')
        
        st.sidebar.header('System Controls')
        if st.sidebar.button("🔄 Refresh System"):
            list_csvs_from_manifest.clear()
            st.sidebar.success("System refreshed!")
            st.rerun()

        # Add horizontal line in sidebar
        st.sidebar.markdown('---')
        
        st.sidebar.subheader("📁 Choose Data Source")
        data_source = st.sidebar.radio("Data Source", ["Upload CSV", "Load from Server"], index=0)
        uploaded_files = []
        if data_source == "Upload CSV":
            uploaded_files = st.sidebar.file_uploader(
                "Upload CSV files (max 200MB)", type="csv", accept_multiple_files=True
            )
            # Add this block below the file uploader
            st.sidebar.markdown("### 📁 Or access data from external link")
            data_link = "https://petronas.sharepoint.com/sites/ecm_ups_coe/confidential/DFE%20Cost%20Engineering/Forms/AllItems.aspx?id=%2Fsites%2Fecm%5Fups%5Fcoe%2Fconfidential%2FDFE%20Cost%20Engineering%2F2%2ETemplate%20Tools%2FCost%20Predictor%2FDatabase%2FCAPEX%20%2D%20RT%20Q1%202025&viewid=25092e6d%2D373d%2D41fe%2D8f6f%2D486cd8cdd5b8"
            st.sidebar.markdown(
                f'<a href="{data_link}" target="_blank"><button style="background-color:#0099ff;color:white;padding:8px 16px;border:none;border-radius:4px;">Open Data Storage</button></a>',
                unsafe_allow_html=True
            )
        
        elif data_source == "Load from Server":
            github_csvs = list_csvs_from_manifest(DATA_FOLDER)
            if github_csvs:
                selected_file = st.sidebar.selectbox("Choose CSV from GitHub", github_csvs)
                if selected_file:
                    raw_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{DATA_FOLDER}/{selected_file}"
                    try:
                        df = pd.read_csv(raw_url)
                        fake_file = type('FakeUpload', (), {'name': selected_file})
                        uploaded_files.append(fake_file)
                        st.session_state['datasets'][selected_file] = df
                        if selected_file not in st.session_state['predictions']:
                            st.session_state['predictions'][selected_file] = []
                        st.success(f"✅ Loaded from GitHub: {selected_file}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error loading CSV: {e}")
            else:
                st.warning("No CSV files found in GitHub folder.")
                
        for uploaded_file in uploaded_files:
            if uploaded_file.name not in st.session_state['datasets']:
                df = pd.read_csv(uploaded_file)
                st.session_state['datasets'][uploaded_file.name] = df
                if uploaded_file.name not in st.session_state['predictions']:
                    st.session_state['predictions'][uploaded_file.name] = []

        # Add horizontal line in sidebar
        st.sidebar.markdown('---')
        
        if st.sidebar.checkbox("🧹 Cleanup Current Session", value=False,
                               help="Enable this if you want to remove datasets not uploaded in this session."):
            uploaded_names = {f.name for f in uploaded_files}
            for name in list(st.session_state['datasets'].keys()):
                if name not in uploaded_names:
                    del st.session_state['datasets'][name]
                    st.session_state['predictions'].pop(name, None)
                    
        if not st.session_state['datasets']:
            st.write("Please upload one or more CSV files to begin.")
            return

        selected_dataset_name = st.sidebar.selectbox(
            "Select a dataset for prediction",
            list(st.session_state['datasets'].keys())
        )
        df = st.session_state['datasets'][selected_dataset_name]
        clean_name = selected_dataset_name.replace('.csv', '')
        st.subheader(f"📊 Metrics: {clean_name}")

        currency = get_currency_symbol(df)
        
        # Store the first column separately for project names
        project_names = df.iloc[:, 0] if len(df.columns) > 0 else pd.Series()
        
        # Use all columns except the first one for the model
        # The last column is still the target, but now we start from column 1
        df_model = df.iloc[:, 1:] if len(df.columns) > 1 else df
        
        imputer = KNNImputer(n_neighbors=5)
        df_imputed = pd.DataFrame(imputer.fit_transform(df_model), columns=df_model.columns)
        
        # Minimized collapse for Data Overview
        with st.expander('Data Overview', expanded=False):
            st.header('Data Overview')
            # Show only the modeling data (without project names)
            st.write('Dataset Shape:', df_imputed.shape)
            st.dataframe(df_imputed.head())

        # X includes all columns except the first (project name) and the last (target)
        # y is still the last column
        X = df_imputed.iloc[:, :-1]
        y = df_imputed.iloc[:, -1]
        target_column = y.name

        # Minimized collapse for Model Training and Performance
        with st.expander('Model Training and Performance', expanded=False):
            st.header('Model Training and Performance')
            test_size = st.slider('Select test size (0.0-1.0)', 0.1, 1.0, 0.2)
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
            scaler = MinMaxScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            rf_model = RandomForestRegressor(random_state=42)
            rf_model.fit(X_train_scaled, y_train)
            y_pred = rf_model.predict(X_test_scaled)

            # st.header('Model Performance')
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            r2 = r2_score(y_test, y_pred)
            col1, col2 = st.columns(2)
            col1.metric('RMSE', f'{rmse:,.2f}')
            col2.metric('R² Score', f'{r2:.2f}')

        # Minimized collapse for Data Visualization
        with st.expander('Data Visualization', expanded=False):
            st.subheader('Correlation Matrix')
            feature_count = len(X.columns)
            corr_height = min(9, max(7, feature_count * 0.5))
            
            # Create correlation matrix from the imputed data
            df_for_corr = pd.concat([X, y], axis=1)
            fig, ax = plt.subplots(figsize=(8, corr_height))
            sns.heatmap(df_for_corr.corr(), annot=True, cmap='coolwarm', fmt='.2f', annot_kws={"size": 10})
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

            st.subheader('Feature Importance')
            fi_height = min(8, max(4, feature_count * 0.3))
            fig, ax = plt.subplots(figsize=(8, fi_height))
            importance_df = pd.DataFrame({
                'feature': X.columns,
                'importance': rf_model.feature_importances_
            }).sort_values('importance', ascending=False)
            sns.barplot(data=importance_df, x='importance', y='feature')
            plt.title('Feature Importance')
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

            st.subheader('Cost Curve (Original Data Only)')
            feature = st.selectbox('Select feature for cost curve (Data Visualization)', X.columns, key='cost_curve_feature_viz')
            fig, ax = plt.subplots(figsize=(7, 6))
            x_vals = df_imputed[feature].values
            y_vals = y.values
            mask = (~np.isnan(x_vals)) & (~np.isnan(y_vals))
            if mask.sum() >= 2:
                slope, intercept, r_val, _, _ = linregress(x_vals[mask], y_vals[mask])
                sns.scatterplot(x=x_vals, y=y_vals, label='Original Data', ax=ax)
                x_line = np.linspace(min(x_vals[mask]), max(x_vals[mask]), 100)
                y_line = slope * x_line + intercept
                ax.plot(x_line, y_line, color='red', label=f'Fit: y = {slope:.2f} * x + {intercept:.2f}')
                ax.text(0.05, 0.95, f'$R^2$ = {r_val**2:.3f}', transform=ax.transAxes,
                        verticalalignment='top', bbox=dict(facecolor='white', alpha=0.5))
            else:
                sns.scatterplot(x=x_vals, y=y_vals, label='Original Data', ax=ax)
                st.warning("Not enough data for regression.")
            ax.set_xlabel(feature)
            ax.set_ylabel(target_column)
            ax.set_title(f'Cost Curve: {feature} vs {target_column}')
            ax.legend()
            ax.xaxis.set_major_formatter(FuncFormatter(human_format))
            ax.yaxis.set_major_formatter(FuncFormatter(human_format))
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        # Minimized/collapsible Cost Breakdown Configuration
        with st.expander('Cost Breakdown Configuration', expanded=False):
            st.header('Cost Breakdown Configuration')
            st.subheader("🔧 EPCIC Cost Breakdown Percentage Input")
            st.markdown("Enter the percentage breakdown for the following categories. You may leave the input to 0% if unapplicable.")
            epcic_percentages = {}
            col_ep1, col_ep2, col_ep3, col_ep4, col_ep5 = st.columns(5)
            epcic_percentages["Engineering"] = col_ep1.number_input("Engineering (%)", min_value=0.0, max_value=100.0, value=0.0, key="eng")
            epcic_percentages["Procurement"] = col_ep2.number_input("Procurement (%)", min_value=0.0, max_value=100.0, value=0.0, key="proc")
            epcic_percentages["Construction"] = col_ep3.number_input("Construction (%)", min_value=0.0, max_value=100.0, value=0.0, key="const")
            epcic_percentages["Installation"] = col_ep4.number_input("Installation (%)", min_value=0.0, max_value=100.0, value=0.0, key="inst")
            epcic_percentages["Commissioning"] = col_ep5.number_input("Commissioning (%)", min_value=0.0, max_value=100.0, value=0.0, key="comm")
            epcic_total = sum(epcic_percentages.values())
            if abs(epcic_total - 100.0) > 1e-3 and epcic_total > 0:
                st.warning(f"⚠️ EPCIC total is {epcic_total:.2f}%. Please ensure it sums to 100% if applicable.")
            st.markdown("**Refer to Escalation and Inflation FY2025-FY2029 document for percentage breakdown by facilities and project types.*")
            st.subheader("💼 Pre-Development and Owner's Cost Percentage Input")
            st.markdown("")
            col_pd1, col_pd2 = st.columns(2)
            predev_percentage = col_pd1.number_input("Enter Pre-Development (%)", min_value=0.0, max_value=100.0, value=0.0, key="predev")
            owners_percentage = col_pd2.number_input("Enter Owner's Cost (%)", min_value=0.0, max_value=100.0, value=0.0, key="owner")
            col_cont1, col_cont2 = st.columns(2)
            with col_cont1:
                st.subheader("⚠️ Cost Contingency Input")
                st.markdown("")
                contingency_percentage = st.number_input("Enter Cost Contingency (%)", min_value=0.0, max_value=100.0, value=0.0, key="cont")
            with col_cont2:
                st.subheader("📈 Escalation & Inflation Percentage Input")
                st.markdown("")
                escalation_percentage = st.number_input("Enter Escalation & Inflation (%)", min_value=0.0, max_value=100.0, value=0.0, key="esc")
            st.markdown("**High-Level Escalation and Inflation rate is based on compounded percentage for the entire project development.*")

        st.header('Make New Predictions')
        project_name = st.text_input('Enter Project Name')
        
        # NEW: Table form like Component Feature Inputs
        st.markdown("**Feature Inputs**")
        st.markdown("Provide feature values (1 row). Leave blank for NaN.")
        
        # Create a dataframe with one row for editing
        input_key = f"input_row__{selected_dataset_name}"
        if input_key not in st.session_state:
            st.session_state[input_key] = {col: np.nan for col in X.columns}
        
        input_row_df = pd.DataFrame([st.session_state[input_key]], columns=X.columns)
        edited_df = st.data_editor(input_row_df, num_rows="fixed", use_container_width=True, key=f"pred_editor_{selected_dataset_name}")
        new_data = edited_df.iloc[0].to_dict()

        if st.button('Predict'):
            df_input = pd.DataFrame([new_data])
            input_scaled = scaler.transform(df_input)
            pred = rf_model.predict(input_scaled)[0]
            
            input_scaled = scaler.transform(df_input)
            pred = rf_model.predict(input_scaled)[0]
            result = {'Project Name': project_name, **new_data, target_column: round(pred, 2)}
            epcic_breakdown = {}
            for phase, percent in epcic_percentages.items():
                cost = round(pred * (percent / 100), 2)
                result[f"{phase} Cost"] = cost
                epcic_breakdown[phase] = {'cost': cost, 'percentage': percent}
            predev_cost = round(pred * (predev_percentage / 100), 2)
            owners_cost = round(pred * (owners_percentage / 100), 2)
            result["Pre-Development Cost"] = predev_cost
            result["Owner's Cost"] = owners_cost
            contingency_base = pred + owners_cost
            contingency_cost = round(contingency_base * (contingency_percentage / 100), 2)
            result["Cost Contingency"] = contingency_cost
            escalation_base = pred + owners_cost
            escalation_cost = round(escalation_base * (escalation_percentage / 100), 2)
            result["Escalation & Inflation"] = escalation_cost
            grand_total = round(pred + owners_cost + contingency_cost + escalation_cost + predev_cost, 2)
            result["Grand Total"] = grand_total
            
            # Initialize predictions list if it doesn't exist
            if selected_dataset_name not in st.session_state['predictions']:
                st.session_state['predictions'][selected_dataset_name] = []
                
            st.session_state['predictions'][selected_dataset_name].append(result)
            display_text = f"### **✅Cost Summary of project {project_name}**\n\n**{target_column}:** {format_currency(pred, currency)}\n\n"
            has_breakdown = any(data['percentage'] > 0 for data in epcic_breakdown.values()) or \
                           predev_percentage > 0 or owners_percentage > 0 or \
                           contingency_percentage > 0 or escalation_percentage > 0
            if has_breakdown:
                for phase, data in epcic_breakdown.items():
                    if data['percentage'] > 0:
                        display_text += f"• {phase} ({data['percentage']:.1f}%): {format_currency(data['cost'], currency)}\n\n"
                if predev_percentage > 0:
                    display_text += f"**Pre-Development ({predev_percentage:.1f}%):** {format_currency(predev_cost, currency)}\n\n"
                if owners_percentage > 0:
                    display_text += f"**Owner's Cost ({owners_percentage:.1f}%):** {format_currency(owners_cost, currency)}\n\n"
                if contingency_percentage > 0:
                    display_text += f"**Contingency ({contingency_percentage:.1f}%):** {format_currency(contingency_cost, currency)}\n\n"
                if escalation_percentage > 0:
                    display_text += f"**Escalation & Inflation ({escalation_percentage:.3f}%):** {format_currency(escalation_cost, currency)}\n\n"
            display_text += f"**Grand Total:** {format_currency(grand_total, currency)}"
            st.success(display_text)
            st.rerun()

        st.write("Or upload an Excel file:")
        excel_file = st.file_uploader("Upload Excel file", type=["xlsx"])
        if excel_file:
            file_id = f"{excel_file.name}_{excel_file.size}_{selected_dataset_name}"
            if file_id not in st.session_state['processed_excel_files']:
                batch_df = pd.read_excel(excel_file)
                
                # Skip the first column (assuming it's project names/identifiers)
                if len(batch_df.columns) > 1:
                    batch_features = batch_df.iloc[:, 1:]  # Skip first column
                    # Ensure we have the right columns for prediction
                    if set(X.columns).issubset(batch_features.columns):
                        scaled = scaler.transform(batch_features[X.columns])
                        preds = rf_model.predict(scaled)
                        
                        for i, row in batch_df.iterrows():
                            # Use the first column as project name
                            name = row.iloc[0] if not pd.isna(row.iloc[0]) else f"Project {i+1}"
                            entry = {'Project Name': str(name)}
                            
                            # Add the feature values (skip the first column)
                            for feature in X.columns:
                                entry[feature] = row[feature] if feature in row else np.nan
                            
                            entry[target_column] = round(preds[i], 2)
                            
                            # Add cost breakdown
                            for phase, percent in epcic_percentages.items():
                                cost = round(preds[i] * (percent / 100), 2)
                                entry[f"{phase} Cost"] = cost
                            
                            predev_cost = round(preds[i] * (predev_percentage / 100), 2)
                            owners_cost = round(preds[i] * (owners_percentage / 100), 2)
                            entry["Pre-Development Cost"] = predev_cost
                            entry["Owner's Cost"] = owners_cost
                            
                            contingency_base = preds[i] + owners_cost
                            contingency_cost = round(contingency_base * (contingency_percentage / 100), 2)
                            entry["Cost Contingency"] = contingency_cost
                            
                            escalation_base = preds[i] + owners_cost
                            escalation_cost = round(escalation_base * (escalation_percentage / 100), 2)
                            entry["Escalation & Inflation"] = escalation_cost
                            
                            grand_total = round(preds[i] + owners_cost + contingency_cost + escalation_cost + predev_cost, 2)
                            entry["Grand Total"] = grand_total
                            
                            # Initialize predictions list if it doesn't exist
                            if selected_dataset_name not in st.session_state['predictions']:
                                st.session_state['predictions'][selected_dataset_name] = []
                                
                            st.session_state['predictions'][selected_dataset_name].append(entry)
                        
                        st.session_state['processed_excel_files'].add(file_id)
                        st.success("Batch prediction successful!")
                        st.rerun()
                    else:
                        st.error(f"Excel missing required columns. Needed: {list(X.columns)}")
                else:
                    st.error("Excel file must have at least 2 columns (project name + features)")

        with st.expander('Simplified Project List', expanded=True):
            # Get predictions safely using .get() with default empty list
            preds = st.session_state['predictions'].get(selected_dataset_name, [])
            if preds:
                if st.button('Delete All', key='delete_all'):
                    st.session_state['predictions'][selected_dataset_name] = []
                    to_remove = {fid for fid in st.session_state['processed_excel_files'] if fid.endswith(selected_dataset_name)}
                    for fid in to_remove:
                        st.session_state['processed_excel_files'].remove(fid)
                    st.rerun()
                for i, p in enumerate(preds):
                    c1, c2 = st.columns([3, 1])
                    c1.write(p['Project Name'])
                    if c2.button('Delete', key=f'del_{i}'):
                        preds.pop(i)
                        st.rerun()
            else:
                st.write("No predictions yet.")

        st.header(f"Prediction Summary based on {clean_name}")
        # Get predictions safely using .get() with default empty list
        preds = st.session_state['predictions'].get(selected_dataset_name, [])
        if preds:
            df_preds = pd.DataFrame(preds)
            num_cols = df_preds.select_dtypes(include=[np.number]).columns
            df_preds_display = df_preds.copy()
            for col in num_cols:
                df_preds_display[col] = df_preds_display[col].apply(lambda x: format_with_commas(x))
            st.dataframe(df_preds_display, use_container_width=True)
            towrite = io.BytesIO()
            df_preds.to_excel(towrite, index=False, engine='openpyxl')
            towrite.seek(0)
            st.download_button(
                "Download Predictions as Excel",
                data=towrite,
                file_name=f"{selected_dataset_name}_predictions.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.write("No predictions available.")

    # =======================================================================================
    # PROJECT BUILDER TAB
    # =======================================================================================
    with tab_pb:
        st.markdown('<h4 style="margin:0;color:#000;">Project Builder</h4><p>Assemble multi-component CAPEX projects</p>', unsafe_allow_html=True)

        if not st.session_state.datasets:
            st.info("No dataset. Go to **Data** tab to upload or load.")
            st.stop()

        colA, colB = st.columns([2, 1])
        with colA:
            new_project_name = st.text_input("New Project Name", placeholder="e.g., CAPEX 2025", key="pb_new_project_name")
        with colB:
            if new_project_name and new_project_name not in st.session_state.projects:
                if st.button("Create Project", key="pb_create_project_btn"):
                    st.session_state.projects[new_project_name] = {"components": [], "totals": {}, "currency": ""}
                    st.success(f"Project '{new_project_name}' created.")
                    st.rerun()

        # ============ ADD THIS CLEANUP SECTION HERE ============
        st.markdown("---")
        st.markdown("#### 🧹 Data Cleanup")
        if st.button("🔄 Clear Session & Fix Data Issues", key="pb_clear_session"):
            # Clear only problematic data
            st.session_state.projects = {}
            st.session_state.component_labels = {}
            st.session_state.widget_nonce += 1
            st.success("✅ Session cleared! Old project data removed. Please create new projects.")
            st.rerun()
        # ======================================================

        if not st.session_state.projects:
            st.info("Create a project above, then add components.")
            st.stop()

        existing_projects = list(st.session_state.projects.keys())
        proj_sel = st.selectbox("Select project to work on", existing_projects, key="pb_project_select")

        ds_names = sorted(st.session_state.datasets.keys())
        dataset_for_comp = st.selectbox("Dataset for this component", ds_names, key="pb_dataset_for_component")
        df_comp = st.session_state.datasets[dataset_for_comp]

        # Get target column (last column)
        df_model_comp = df_comp.iloc[:, 1:] if len(df_comp.columns) > 1 else df_comp
        imputer_comp = KNNImputer(n_neighbors=5)
        df_imputed_comp = pd.DataFrame(imputer_comp.fit_transform(df_model_comp), columns=df_model_comp.columns)
        X_comp = df_imputed_comp.iloc[:, :-1]
        y_comp = df_imputed_comp.iloc[:, -1]
        target_column_comp = y_comp.name
        
        curr_ds = get_currency_symbol(df_comp)
        
        # Train model for this dataset
        X_train_comp, X_test_comp, y_train_comp, y_test_comp = train_test_split(X_comp, y_comp, test_size=0.2, random_state=42)
        scaler_comp = MinMaxScaler()
        X_train_scaled_comp = scaler_comp.fit_transform(X_train_comp)
        X_test_scaled_comp = scaler_comp.transform(X_test_comp)
        rf_model_comp = RandomForestRegressor(random_state=42)
        rf_model_comp.fit(X_train_scaled_comp, y_train_comp)

        default_label = st.session_state.component_labels.get(dataset_for_comp, "")
        component_type = st.text_input(
            "Component type (Asset / Scope)",
            value=(default_label or "Platform / Pipeline / Subsea / Well"),
            key=f"pb_component_type_{proj_sel}",
        )

        st.markdown("**Component Feature Inputs (1 row)**")
        comp_input_key = f"pb_input_row__{proj_sel}__{dataset_for_comp}"
        if comp_input_key not in st.session_state:
            st.session_state[comp_input_key] = {c: np.nan for c in X_comp.columns}

        comp_row_df = pd.DataFrame([st.session_state[comp_input_key]], columns=X_comp.columns)
        comp_editor_key = f"pb_editor__{proj_sel}__{dataset_for_comp}__{st.session_state.widget_nonce}"
        comp_edited = st.data_editor(comp_row_df, num_rows="fixed", use_container_width=True, key=comp_editor_key)
        comp_payload = comp_edited.iloc[0].to_dict()

        st.markdown("---")
        
        # COST BREAKDOWN CONFIGURATION - Consistent with Data tab
        with st.expander('Cost Breakdown Configuration', expanded=False):
            st.header('Cost Breakdown Configuration')
            
            # EPCIC Section
            st.subheader("🔧 EPCIC Cost Breakdown Percentage Input")
            st.markdown("Enter the percentage breakdown for the following categories. You may leave the input to 0% if unapplicable.")
            
            # Use 5 columns layout
            wb1, wb2, wb3, wb4, wb5 = st.columns(5)
            
            epcic_percentages_pb = {}
            epcic_percentages_pb["Engineering"] = wb1.number_input("Engineering (%)", 
                                                                min_value=0.0, 
                                                                max_value=100.0, 
                                                                value=10.0, 
                                                                step=1.0, 
                                                                key=f"pb_eng_{proj_sel}")
            
            epcic_percentages_pb["Procurement"] = wb2.number_input("Procurement (%)", 
                                                                min_value=0.0, 
                                                                max_value=100.0, 
                                                                value=30.0, 
                                                                step=1.0, 
                                                                key=f"pb_proc_{proj_sel}")
            
            epcic_percentages_pb["Construction"] = wb3.number_input("Construction (%)", 
                                                                min_value=0.0, 
                                                                max_value=100.0, 
                                                                value=25.0, 
                                                                step=1.0, 
                                                                key=f"pb_const_{proj_sel}")
            
            epcic_percentages_pb["Installation"] = wb4.number_input("Installation (%)", 
                                                                min_value=0.0, 
                                                                max_value=100.0, 
                                                                value=20.0, 
                                                                step=1.0, 
                                                                key=f"pb_inst_{proj_sel}")
            
            epcic_percentages_pb["Commissioning"] = wb5.number_input("Commissioning (%)", 
                                                                 min_value=0.0, 
                                                                 max_value=100.0, 
                                                                 value=15.0, 
                                                                 step=1.0, 
                                                                 key=f"pb_comm_{proj_sel}")
            
            epcic_total_pb = sum(epcic_percentages_pb.values())
            if abs(epcic_total_pb - 100.0) > 1e-3 and epcic_total_pb > 0:
                st.warning(f"⚠️ EPCIC total is {epcic_total_pb:.2f}%. Please ensure it sums to 100% if applicable.")
            
            st.markdown("**Refer to Escalation and Inflation FY2025-FY2029 document for percentage breakdown by facilities and project types.*")
            
            # Pre-Development and Owner's Cost
            st.subheader("💼 Pre-Development and Owner's Cost Percentage Input")
            st.markdown("")
            col_pd1, col_pd2 = st.columns(2)
            
            predev_percentage_pb = col_pd1.number_input("Enter Pre-Development (%)", 
                                                     min_value=0.0, 
                                                     max_value=100.0, 
                                                     value=0.0, 
                                                     step=0.5, 
                                                     key=f"pb_predev_{proj_sel}")
            owners_pb = col_pd2.number_input("Enter Owner's Cost (%)", 
                                             min_value=0.0, 
                                             max_value=100.0, 
                                             value=0.0, 
                                             step=0.5, 
                                             key=f"pb_owners_{proj_sel}")
            
            # Contingency and Escalation
            col_cont1, col_cont2 = st.columns(2)
            with col_cont1:
                st.subheader("⚠️ Cost Contingency Input")
                st.markdown("")
                cont_pb = st.number_input("Enter Cost Contingency (%)", 
                                          min_value=0.0, 
                                          max_value=100.0, 
                                          value=0.0, 
                                          step=0.5, 
                                          key=f"pb_cont_{proj_sel}")
            with col_cont2:
                st.subheader("📈 Escalation & Inflation Percentage Input")
                st.markdown("")
                esc_pb = st.number_input("Enter Escalation & Inflation (%)", 
                                         min_value=0.0, 
                                         max_value=100.0, 
                                         value=0.0, 
                                         step=0.5, 
                                         key=f"pb_esc_{proj_sel}")
            
            st.markdown("**High-Level Escalation and Inflation rate is based on compounded percentage for the entire project development.*")
        
        # Create EPCIC dictionary for cost breakdown function
        epcic_pb = epcic_percentages_pb

        if st.button("➕ Predict & Add Component", key=f"pb_add_comp_{proj_sel}_{dataset_for_comp}"):
            try:
                base_pred = single_prediction(rf_model_comp, scaler_comp, list(X_comp.columns), comp_payload)
                owners_cost, predev_cost, contingency_cost, escalation_cost, epcic_costs, grand_total = cost_breakdown(
                    base_pred, epcic_pb, predev_percentage_pb, owners_pb, cont_pb, esc_pb
                )

                comp_entry = {
                    "component_type": component_type or default_label or "Component",
                    "dataset": dataset_for_comp,
                    "model_used": "RandomForest",
                    "inputs": {k: comp_payload.get(k, np.nan) for k in X_comp.columns},
                    "feature_cols": list(X_comp.columns),
                    "prediction": base_pred,
                    "breakdown": {
                        "epcic_costs": epcic_costs,
                        "epcic_pct": epcic_pb,
                        "predev_cost": predev_cost,
                        "owners_cost": owners_cost,
                        "contingency_cost": contingency_cost,
                        "escalation_cost": escalation_cost,
                        "grand_total": grand_total,
                        "target_col": target_column_comp,
                        "predev_pct": float(predev_percentage_pb),
                        "owners_pct": float(owners_pb),
                        "cont_pct": float(cont_pb),
                        "esc_pct": float(esc_pb),
                    },
                }

                st.session_state.projects[proj_sel]["components"].append(comp_entry)
                st.session_state.component_labels[dataset_for_comp] = component_type or default_label
                st.session_state.projects[proj_sel]["currency"] = curr_ds

                st.session_state.widget_nonce += 1
                st.success(f"Component added to project '{proj_sel}'.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to add component: {e}")

        st.markdown("---")
        st.markdown("### Current Project Overview")

        proj = st.session_state.projects[proj_sel]
        comps = proj.get("components", [])
        if not comps:
            st.info("No components yet. Add at least one above.")
            st.stop()

        # Create DataFrame EXACTLY like Prediction Summary in Data tab
        rows = []
        for idx, c in enumerate(comps):
            breakdown = c.get("breakdown", {})
            inputs = c.get("inputs", {})
            epcic_costs = breakdown.get("epcic_costs", {})
            
            # 1. Start with "Project Name" equivalent - use Component as identifier
            row = {
                "Component": c.get("component_type", f"Component {idx+1}"),
                "Dataset": c.get("dataset", "Unknown")
            }
            
            # 2. Add ALL input features EXACTLY like Prediction Summary
            # Prediction Summary shows ALL feature columns from the dataset
            for feature_name in c.get("feature_cols", []):
                feature_value = inputs.get(feature_name, np.nan)
                row[feature_name] = feature_value
            
            # 3. Add the target column (Base CAPEX) - this is like target_column in Data tab
            target_col = breakdown.get("target_col", "Base CAPEX")
            row[target_col] = float(c.get("prediction", 0.0))
            
            # 4. Add EPCIC costs EXACTLY like Prediction Summary
            # These appear as "Engineering Cost", "Procurement Cost", etc.
            epcic_phases = ["Engineering", "Procurement", "Construction", "Installation", "Commissioning"]
            for phase in epcic_phases:
                cost = epcic_costs.get(phase, 0.0)
                row[f"{phase} Cost"] = float(cost)
            
            # 5. Add other cost breakdowns EXACTLY like Prediction Summary
            row["Pre-Development Cost"] = float(breakdown.get("predev_cost", 0.0))
            row["Owner's Cost"] = float(breakdown.get("owners_cost", 0.0))
            row["Cost Contingency"] = float(breakdown.get("contingency_cost", 0.0))
            row["Escalation & Inflation"] = float(breakdown.get("escalation_cost", 0.0))
            
            # 6. Add Grand Total at the end EXACTLY like Prediction Summary
            row["Grand Total"] = float(breakdown.get("grand_total", 0.0))
            
            rows.append(row)
        
        dfc = pd.DataFrame(rows)
        curr = proj.get("currency", "") or curr_ds

        # Display the table - SIMPLIFIED VERSION (no complex reordering)
        if not dfc.empty:
            # Just show the dataframe as-is - it already has all the columns
            # Format numeric columns with commas
            num_cols = dfc.select_dtypes(include=[np.number]).columns
            dfc_display = dfc.copy()
            for col in num_cols:
                dfc_display[col] = dfc_display[col].apply(lambda x: format_with_commas(x))
            
            st.dataframe(dfc_display, use_container_width=True, height=420)
            
            # Download button
            towrite = io.BytesIO()
            dfc.to_excel(towrite, index=False, engine='openpyxl')
            towrite.seek(0)
            st.download_button(
                "Download Project Components as Excel",
                data=towrite,
                file_name=f"{proj_sel}_components.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"download_components_{proj_sel}"
            )
        else:
            st.write("No components available.")

        # Keep the metrics summary
        t = project_totals(proj)
        proj["totals"] = {"capex_sum": t["capex_sum"], "grand_total": t["grand_total"]}

        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            st.metric("Project CAPEX (Base)", f"{curr} {t['capex_sum']:,.2f}")
        with col_t2:
            st.metric("Project Pre-Development", f"{curr} {t['predev']:,.2f}")
        with col_t3:
            st.metric("Project Grand Total (incl. Pre-Dev)", f"{curr} {t['grand_total']:,.2f}")

        with st.expander("📊 Component Cost Composition", expanded=False):
            st.markdown("#### Component Cost Composition")
            df_cost = dfc[["Component", "Base CAPEX", "Owner's Cost", "Cost Contingency", "Escalation & Inflation", "Pre-Development Cost"]].copy()
            df_cost = df_cost.rename(columns={
                "Base CAPEX": "CAPEX", 
                "Owner's Cost": "Owner",
                "Cost Contingency": "Contingency",
                "Escalation & Inflation": "Escalation",
                "Pre-Development Cost": "Pre-Development"
            })
            df_melt = df_cost.melt(id_vars="Component", var_name="Cost Type", value_name="Value")
            fig_stack = plt.figure(figsize=(10, 6))
            ax = fig_stack.add_subplot(111)
            
            # Create stacked bar chart
            categories = df_cost["Component"].unique()
            bottom = np.zeros(len(categories))
            
            for cost_type in ["CAPEX", "Owner", "Contingency", "Escalation", "Pre-Development"]:
                values = [df_cost[df_cost["Component"] == cat][cost_type].values[0] for cat in categories]
                ax.bar(categories, values, bottom=bottom, label=cost_type)
                bottom += values
            
            ax.set_ylabel(f"Cost ({curr})")
            ax.set_xlabel("Component")
            ax.set_title("Cost Composition by Component")
            ax.legend()
            ax.tick_params(axis='x', rotation=45)
            
            # Format y-axis with human readable format
            ax.yaxis.set_major_formatter(FuncFormatter(human_format))
            
            plt.tight_layout()
            st.pyplot(fig_stack)

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
                    st.session_state.widget_nonce += 1
                    st.success("Component removed.")
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
                key=f"pb_dl_excel_{proj_sel}",
            )

        with col_dl2:
            st.download_button(
                "⬇️ Download Project (JSON)",
                data=json.dumps(proj, indent=2, default=float),
                file_name=f"{proj_sel}.json",
                mime="application/json",
                key=f"pb_dl_json_{proj_sel}",
            )

        with col_dl3:
            # For PowerPoint export, you can add it later if needed
            st.info("PowerPoint export available in full version")

        up_json = st.file_uploader("Import project JSON", type=["json"], key=f"pb_import_{proj_sel}__{st.session_state.widget_nonce}")
        if up_json is not None:
            try:
                data = json.load(up_json)
                st.session_state.projects[proj_sel] = data
                st.session_state.widget_nonce += 1
                st.success("Project imported successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to import project JSON: {e}")

if __name__ == '__main__':
    main()
