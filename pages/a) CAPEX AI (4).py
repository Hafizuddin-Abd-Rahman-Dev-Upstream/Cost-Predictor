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

# Page config
st.set_page_config(
    page_title="CAPEX AI RT2025",
    page_icon="💲",
    initial_sidebar_state="expanded"
)

# Simple auth placeholder (keeps existing behaviour)
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Load approved emails & password from secrets (if provided)
APPROVED_EMAILS = st.secrets.get("emails", [])
correct_password = st.secrets.get("password", None)

if not st.session_state.authenticated:
    with st.form("login_form"):
        st.markdown("#### 🔐 Access Required", unsafe_allow_html=True)
        email = st.text_input("Email Address")
        password = st.text_input("Enter Access Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if (not APPROVED_EMAILS or email in APPROVED_EMAILS) and (correct_password is None or password == correct_password):
                st.session_state.authenticated = True
                st.success("✅ Access granted.")
                st.experimental_rerun()
            else:
                st.error("❌ Invalid email or password. Please contact Cost Engineering Focal for access")
    st.stop()

# Repo config for server CSV listing
GITHUB_USER = "Hafizuddin-Abd-Rahman-Dev-Upstream"
REPO_NAME = "Cost-Predictor"
BRANCH = "main"
DATA_FOLDER = "pages/data_CAPEX"

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

# Helpers
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

def format_currency(amount, currency=''):
    try:
        return f"{currency} {float(amount):,.2f}" if currency else f"{float(amount):,.2f}"
    except Exception:
        return str(amount)

def download_all_predictions():
    preds_all = st.session_state.get("predictions", {})
    if not preds_all or all(len(v) == 0 for v in preds_all.values()):
        st.sidebar.error("No predictions available to download")
        return

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
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

# Training helper (Random Forest only)
def train_random_forest_on_df(df: pd.DataFrame, test_size=0.2, random_state=42):
    """
    Expects df with last column as target. Imputes with KNNImputer, scales with MinMaxScaler,
    trains RandomForest, returns dict with model, scaler, imputer, features, target_name and metrics.
    """
    if df.shape[1] < 2:
        raise ValueError("Dataset must have at least one feature and one target column (target must be last column).")

    # Target is last column
    target_col = df.columns[-1]
    X = df.iloc[:, :-1].copy()
    y = df[target_col].copy()

    # Impute numeric columns (KNNImputer)
    imputer = KNNImputer(n_neighbors=5)
    X_imputed = pd.DataFrame(imputer.fit_transform(X), columns=X.columns)

    # Scale
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X_imputed)

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=test_size, random_state=random_state)

    # Random Forest (single model option)
    rf_model = RandomForestRegressor(random_state=random_state, n_jobs=-1)
    rf_model.fit(X_train, y_train)

    # Metrics on holdout
    y_pred = rf_model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    return {
        "model": rf_model,
        "scaler": scaler,
        "imputer": imputer,
        "features": X.columns.tolist(),
        "target": target_col,
        "metrics": {"rmse": float(rmse), "r2": float(r2)},
        "X_train_shape": X_train.shape,
        "X_test_shape": X_test.shape
    }

# Initialize session state containers
def init_state():
    ss = st.session_state
    ss.setdefault("datasets", {})  # dataset_name -> DataFrame
    ss.setdefault("predictions", {})  # dataset_name -> list of dict
    ss.setdefault("processed_excel_files", set())
    ss.setdefault("models", {})  # dataset_name -> dict with model/scaler/imputer/features/target
    ss.setdefault("projects", {})  # project_name -> dict
    ss.setdefault("component_labels", {})  # dataset_name -> label
init_state()

# Sidebar controls
st.sidebar.header('Data Controls')
if st.sidebar.button("Clear all predictions"):
    st.session_state['predictions'] = {}
    st.sidebar.success("All predictions cleared!")
if st.sidebar.button("Clear processed files history"):
    st.session_state['processed_excel_files'] = set()
    st.sidebar.success("Processed files history cleared!")
if st.sidebar.button("📥 Download All Predictions"):
    if st.session_state['predictions']:
        download_all_predictions()
        st.sidebar.success("All predictions compiled successfully!")
    else:
        st.sidebar.warning("No predictions to download.")

st.sidebar.markdown('---')
st.sidebar.header('System Controls')
if st.sidebar.button("🔄 Refresh System"):
    list_csvs_from_manifest.clear()
st.sidebar.markdown('---')

st.sidebar.subheader("📁 Choose Data Source")
data_source = st.sidebar.radio("Data Source", ["Upload CSV", "Load from Server"], index=0)
uploaded_files = []
if data_source == "Upload CSV":
    uploaded_files = st.sidebar.file_uploader(
        "Upload CSV files (max 200MB)", type="csv", accept_multiple_files=True
    )
    st.sidebar.markdown("### 📁 Or access data from external link")
    data_link = "https://petronas.sharepoint.com/sites/ecm_ups_coe/confidential/DFE%20Cost%20Engineering/Forms/AllItems.aspx?id=%2Fsites%2Fecm%5Fups%5Fcoe%2Fconfidential%2FDFE%20Cost%20Engineering[...]"
    st.sidebar.markdown(
        f'<a href="{data_link}" target="_blank"><button style="background-color:#0099ff;color:white;padding:8px 16px;border:none;border-radius:4px;">Open Data Storage</button></a>',
        unsafe_allow_html=True
    )
else:
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
                st.session_state['predictions'].setdefault(selected_file, [])
                st.success(f"✅ Loaded from GitHub: {selected_file}")
            except Exception as e:
                st.error(f"Error loading CSV: {e}")
    else:
        st.warning("No CSV files found in GitHub folder.")

# Persist uploaded CSVs into session datasets
for uploaded_file in uploaded_files:
    if uploaded_file.name not in st.session_state['datasets']:
        try:
            df = pd.read_csv(uploaded_file)
            st.session_state['datasets'][uploaded_file.name] = df
            st.session_state['predictions'].setdefault(uploaded_file.name, [])
        except Exception as e:
            st.error(f"Failed to read uploaded file {uploaded_file.name}: {e}")

st.sidebar.markdown('---')
if st.sidebar.checkbox("🧹 Cleanup Current Session",
                       value=False,
                       help="Remove datasets not uploaded in this session."):
    uploaded_names = {f.name for f in uploaded_files}
    for name in list(st.session_state['datasets'].keys()):
        if name not in uploaded_names:
            del st.session_state['datasets'][name]
            st.session_state['predictions'].pop(name, None)

# Main layout
st.title('💲CAPEX AI RT2025💲')
if not st.session_state['datasets']:
    st.info("Please upload one or more CSV files to begin.")
else:
    # Dataset selection (for the rest of the app)
    selected_dataset_name = st.sidebar.selectbox(
        "Select a dataset for prediction",
        list(st.session_state['datasets'].keys())
    )
    df = st.session_state['datasets'][selected_dataset_name]
    clean_name = selected_dataset_name.replace('.csv', '')
    st.subheader(f"📊 Metrics: {clean_name}")

    # Determine currency and prepare imputer/scaler placeholders
    currency = get_currency_symbol(df)

    # We'll keep an imputed+display copy for visuals
    try:
        imputer_preview = KNNImputer(n_neighbors=5)
        df_imputed_preview = pd.DataFrame(imputer_preview.fit_transform(df.select_dtypes(include=[np.number])), 
                                          columns=df.select_dtypes(include=[np.number]).columns)
    except Exception:
        # fallback: use original df for preview if imputation fails
        df_imputed_preview = df.select_dtypes(include=[np.number]).copy()

    # Target is always the last column
    target_column = df.columns[-1]
    st.caption(f"Target column (label) is fixed to the last column in CSV: '{target_column}'")

    # Model Training and Performance (Random Forest only) - uses slider for test size
    with st.expander('Model Training and Performance', expanded=False):
        st.header('Model Training and Performance (Random Forest)')
        st.write("The app uses RandomForestRegressor only. Adjust test size and retrain.")
        test_size = st.slider('Select test size (fraction for holdout)', 0.05, 0.5, 0.2, step=0.01, key=f"ts_{selected_dataset_name}")
        # Train when user clicks train button
        if st.button("⚙️ Train Random Forest", key=f"train_btn_{selected_dataset_name}"):
            try:
                # Train and store model into session
                model_bundle = train_random_forest_on_df(df, test_size=float(test_size))
                st.session_state['models'][selected_dataset_name] = model_bundle
                metrics = model_bundle["metrics"]
                col1, col2, col3 = st.columns(3)
                col1.metric("Holdout RMSE", f"{metrics['rmse']:,.2f}")
                col2.metric("Holdout R²", f"{metrics['r2']:.3f}")
                col3.metric("Features", len(model_bundle["features"]))
                st.success(f"Model trained for '{selected_dataset_name}'.")
            except Exception as e:
                st.error(f"Training failed: {e}")
        else:
            # If previously trained, show metrics
            mb = st.session_state['models'].get(selected_dataset_name)
            if mb:
                m = mb['metrics']
                col1, col2, col3 = st.columns(3)
                col1.metric("Holdout RMSE", f"{m['rmse']:,.2f}")
                col2.metric("Holdout R²", f"{m['r2']:.3f}")
                col3.metric("Features", len(mb["features"]))
            else:
                st.info("No trained model found for this dataset. Click 'Train Random Forest' to train using current dataset and test size.")

    # Data Overview (collapsed)
    with st.expander('Data Overview', expanded=False):
        st.write('Dataset Shape:', df.shape)
        st.dataframe(df.head())

    # Data Visualization (collapsed)
    with st.expander('Data Visualization', expanded=False):
        st.subheader('Correlation Matrix')
        num_df = df.select_dtypes(include=[np.number]).copy()
        feature_count = len(num_df.columns)
        corr_height = min(9, max(6, feature_count * 0.5))
        fig, ax = plt.subplots(figsize=(8, corr_height))
        if feature_count >= 1:
            sns.heatmap(num_df.corr(), annot=True, cmap='coolwarm', fmt='.2f', annot_kws={"size": 10}, ax=ax)
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.write("No numeric features to display correlation.")
        plt.close()

        st.subheader('Feature Importance (from last trained model)')
        mb = st.session_state['models'].get(selected_dataset_name)
        if mb:
            feat_cols = mb['features']
            importances = mb['model'].feature_importances_
            fi_df = pd.DataFrame({"feature": feat_cols, "importance": importances}).sort_values("importance", ascending=False)
            fi_height = min(8, max(3, len(fi_df) * 0.3))
            fig, ax = plt.subplots(figsize=(8, fi_height))
            sns.barplot(data=fi_df, x="importance", y="feature", ax=ax)
            plt.title("Feature Importance")
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
        else:
            st.info("Train the model to view feature importances.")

        st.subheader('Cost Curve (Original Data Only)')
        other_cols = [c for c in df.columns if c != target_column]
        if other_cols:
            feature = st.selectbox('Select feature for cost curve (Data Visualization)', other_cols, key=f'cc_{selected_dataset_name}')
            fig, ax = plt.subplots(figsize=(7, 6))
            x_vals = df[feature].values
            y_vals = df[target_column].values
            mask = (~pd.isna(x_vals)) & (~pd.isna(y_vals))
            if mask.sum() >= 2:
                slope, intercept, r_val, _, _ = linregress(x_vals[mask], y_vals[mask])
                sns.scatterplot(x=x_vals, y=y_vals, label='Original Data', ax=ax)
                x_line = np.linspace(min(x_vals[mask]), max(x_vals[mask]), 100)
                y_line = slope * x_line + intercept
                ax.plot(x_line, y_line, color='red', label=f'Fit: y = {slope:.2f}x + {intercept:.2f}')
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
        else:
            st.write("No suitable feature for cost curve visualisation.")

    # Cost Breakdown Configuration (collapsed)
    with st.expander('Cost Breakdown Configuration', expanded=False):
        st.subheader("🔧 Cost Breakdown Percentage Input")
        st.markdown("Enter the percentage breakdown for EPCIC phases. Leave as 0 if not applicable.")
        epcic_percentages = {}
        col_ep1, col_ep2, col_ep3, col_ep4, col_ep5 = st.columns(5)
        epcic_percentages["Engineering"] = col_ep1.number_input("Engineering (%)", min_value=0.0, max_value=100.0, value=0.0, key=f"ep_eng_{selected_dataset_name}")
        epcic_percentages["Procurement"] = col_ep2.number_input("Procurement (%)", min_value=0.0, max_value=100.0, value=0.0, key=f"ep_proc_{selected_dataset_name}")
        epcic_percentages["Construction"] = col_ep3.number_input("Construction (%)", min_value=0.0, max_value=100.0, value=0.0, key=f"ep_const_{selected_dataset_name}")
        epcic_percentages["Installation"] = col_ep4.number_input("Installation (%)", min_value=0.0, max_value=100.0, value=0.0, key=f"ep_inst_{selected_dataset_name}")
        epcic_percentages["Commissioning"] = col_ep5.number_input("Commissioning (%)", min_value=0.0, max_value=100.0, value=0.0, key=f"ep_comm_{selected_dataset_name}")
        epcic_total = sum(epcic_percentages.values())
        if abs(epcic_total - 100.0) > 1e-3 and epcic_total > 0:
            st.warning(f"⚠️ EPCIC total is {epcic_total:.2f}%. Consider summing to 100% if applicable.")

        st.subheader("💼 Pre-Dev and Owner's Cost Percentage Input")
        col_pd1, col_pd2 = st.columns(2)
        predev_percentage = col_pd1.number_input("Pre-Development (%)", min_value=0.0, max_value=100.0, value=0.0, key=f"pd_{selected_dataset_name}")
        owners_percentage = col_pd2.number_input("Owner's Cost (%)", min_value=0.0, max_value=100.0, value=0.0, key=f"owners_{selected_dataset_name}")

        col_ct1, col_ct2 = st.columns(2)
        contingency_percentage = col_ct1.number_input("Contingency (%)", min_value=0.0, max_value=100.0, value=0.0, key=f"cont_{selected_dataset_name}")
        escalation_percentage = col_ct2.number_input("Escalation & Inflation (%)", min_value=0.0, max_value=100.0, value=0.0, key=f"escal_{selected_dataset_name}")

    # Make New Predictions (single-row and batch)
    st.header('Make New Predictions')
    project_name = st.text_input('Enter Project Name', key=f"pn_{selected_dataset_name}")

    # If model not trained yet, show info
    if selected_dataset_name not in st.session_state['models']:
        st.info("No trained Random Forest model for this dataset. Train it in 'Model Training and Performance' expander to enable predictions.")
    else:
        mb = st.session_state['models'][selected_dataset_name]
        feat_cols = mb["features"]

        # Single-row inputs
        num_features = len(feat_cols)
        if num_features == 0:
            st.error("No feature columns available to collect inputs.")
        else:
            # Create input grid (2 columns)
            if num_features <= 2:
                cols = st.columns(num_features)
            else:
                cols = []
                for i in range(0, num_features, 2):
                    row_cols = st.columns(min(2, num_features - i))
                    cols.extend(row_cols)

            new_data = {}
            for i, col in enumerate(feat_cols):
                col_idx = i % len(cols)
                user_val = cols[col_idx].text_input(f'{col}', key=f'input_{selected_dataset_name}_{col}')
                if str(user_val).strip().lower() in ("", "nan"):
                    new_data[col] = np.nan
                else:
                    try:
                        new_data[col] = float(user_val)
                    except Exception:
                        new_data[col] = np.nan

            if st.button('Predict', key=f'predict_btn_{selected_dataset_name}'):
                try:
                    # Build input DF and apply imputer/scaler then predict
                    df_input_raw = pd.DataFrame([new_data], columns=feat_cols)
                    X_imputed = pd.DataFrame(mb['imputer'].transform(df_input_raw), columns=feat_cols)
                    X_scaled = mb['scaler'].transform(X_imputed)
                    pred = float(mb['model'].predict(X_scaled)[0])

                    result = {'Project Name': project_name, **{k: (v if not pd.isna(v) else None) for k, v in new_data.items()}, mb['target']: round(pred, 2)}

                    # EPCIC breakdown
                    for phase, pct in epcic_percentages.items():
                        cost = round(pred * (pct / 100.0), 2)
                        result[f"{phase} Cost"] = cost

                    predev_cost = round(pred * (predev_percentage / 100.0), 2)
                    owners_cost = round(pred * (owners_percentage / 100.0), 2)
                    contingency_base = pred + owners_cost
                    contingency_cost = round(contingency_base * (contingency_percentage / 100.0), 2)
                    escalation_base = pred + owners_cost
                    escalation_cost = round(escalation_base * (escalation_percentage / 100.0), 2)
                    grand_total = round(pred + owners_cost + contingency_cost + escalation_cost, 2)

                    result.update({
                        "Pre-Development Cost": predev_cost,
                        "Owner's Cost": owners_cost,
                        "Cost Contingency": contingency_cost,
                        "Escalation & Inflation": escalation_cost,
                        "Grand Total": grand_total
                    })

                    st.session_state['predictions'].setdefault(selected_dataset_name, [])
                    st.session_state['predictions'][selected_dataset_name].append(result)

                    display_text = (
                        f"### ✅ Cost Summary of project {project_name}\n\n"
                        f"**{mb['target']}:** {format_currency(pred, currency)}\n\n"
                        + (f"**Pre-Development:** {format_currency(predev_cost, currency)}\n\n" if predev_percentage > 0 else "")
                        + (f"**Owner's Cost:** {format_currency(owners_cost, currency)}\n\n" if owners_percentage > 0 else "")
                        + (f"**Contingency:** {format_currency(contingency_cost, currency)}\n\n" if contingency_percentage > 0 else "")
                        + (f"**Escalation & Inflation:** {format_currency(escalation_cost, currency)}\n\n" if escalation_percentage > 0 else "")
                        + f"**Grand Total:** {format_currency(grand_total, currency)}"
                    )
                    st.success(display_text)
                except Exception as e:
                    st.error(f"Prediction failed: {e}")

        # Batch Excel upload predictions
        st.write("Or upload an Excel file:")
        excel_file = st.file_uploader("Upload Excel file (for batch prediction)", type=["xlsx"], key=f"excel_{selected_dataset_name}")
        if excel_file:
            file_id = f"{excel_file.name}_{excel_file.size}_{selected_dataset_name}"
            if file_id not in st.session_state['processed_excel_files']:
                try:
                    batch_df = pd.read_excel(excel_file)
                    mb = st.session_state['models'][selected_dataset_name]
                    if set(mb['features']).issubset(batch_df.columns):
                        # Impute & scale
                        X_batch = batch_df[mb['features']]
                        X_imputed = pd.DataFrame(mb['imputer'].transform(X_batch), columns=mb['features'])
                        X_scaled = mb['scaler'].transform(X_imputed)
                        preds = mb['model'].predict(X_scaled)
                        batch_df[mb['target']] = preds
                        st.session_state['predictions'].setdefault(selected_dataset_name, [])
                        for i, row in batch_df.iterrows():
                            name = row.get("Project Name", f"Project {i+1}")
                            entry = {"Project Name": name}
                            entry.update(row[mb['features']].to_dict())
                            p = float(preds[i])
                            entry[mb['target']] = round(p, 2)
                            for phase, percent in epcic_percentages.items():
                                entry[f"{phase} Cost"] = round(p * (percent / 100.0), 2)
                            predev_cost = round(p * (predev_percentage / 100.0), 2)
                            owners_cost = round(p * (owners_percentage / 100.0), 2)
                            contingency_base = p + owners_cost
                            contingency_cost = round(contingency_base * (contingency_percentage / 100.0), 2)
                            escalation_base = p + owners_cost
                            escalation_cost = round(escalation_base * (escalation_percentage / 100.0), 2)
                            grand_total = round(p + owners_cost + contingency_cost + escalation_cost, 2)
                            entry["Pre-Development Cost"] = predev_cost
                            entry["Owner's Cost"] = owners_cost
                            entry["Cost Contingency"] = contingency_cost
                            entry["Escalation & Inflation"] = escalation_cost
                            entry["Grand Total"] = grand_total
                            st.session_state['predictions'][selected_dataset_name].append(entry)
                        st.session_state['processed_excel_files'].add(file_id)
                        st.success("Batch prediction successful!")
                    else:
                        st.error("Excel missing required feature columns for this model.")
                except Exception as e:
                    st.error(f"Batch prediction failed: {e}")

    # Simplified Project List
    with st.expander('Simplified Project List', expanded=True):
        preds = st.session_state['predictions'].get(selected_dataset_name, [])
        if preds:
            if st.button('Delete All', key=f'delete_all_{selected_dataset_name}'):
                st.session_state['predictions'][selected_dataset_name] = []
                to_remove = {fid for fid in st.session_state['processed_excel_files'] if fid.endswith(selected_dataset_name)}
                for fid in to_remove:
                    st.session_state['processed_excel_files'].remove(fid)
                st.experimental_rerun()
            for i, p in enumerate(preds):
                c1, c2 = st.columns([3, 1])
                c1.write(p.get('Project Name', f"Project {i+1}"))
                if c2.button('Delete', key=f'del_{selected_dataset_name}_{i}'):
                    preds.pop(i)
                    st.experimental_rerun()
        else:
            st.write("No predictions yet.")

    # Prediction summary table and download
    st.header(f"Prediction Summary based on {clean_name}")
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

# Project Builder & Compare Projects remain largely unchanged but use the single-model storage structure
# Tabbed interface for Project Builder and Compare Projects
tab1, tab2, tab3 = st.tabs(["📁 Datasets & Models (Current)", "🏗️ Project Builder", "🅚 Compare Projects"])

with tab1:
    st.write("Use the sidebar to select/upload datasets and train the Random Forest model in the 'Model Training and Performance' expander.")
    st.write("Once trained you can make single or batch predictions and download results.")

with tab2:
    st.header("🏗️ Project Builder")
    colA, colB = st.columns([3, 2])
    with colA:
        new_project_name = st.text_input(
            "Project Name", placeholder="e.g., Project A",
            key="pb_project_name_input"
        )
    with colB:
        if new_project_name and new_project_name not in st.session_state["projects"]:
            if st.button("Create Project", key="pb_create_project_btn"):
                st.session_state["projects"][new_project_name] = {"components": [], "totals": {}, "currency": ""}
                st.success(f"Project '{new_project_name}' created.")

    if not st.session_state["datasets"]:
        st.info("Upload datasets in the sidebar first.")
    else:
        existing_projects = list(st.session_state["projects"].keys())
        proj_sel = st.selectbox(
            "Choose project",
            ([new_project_name] + existing_projects) if new_project_name else existing_projects,
            key="pb_project_select"
        )

        ds_names = sorted(st.session_state["datasets"].keys())
        dataset_for_comp = st.selectbox(
            "Dataset for this component", ds_names,
            key="pb_dataset_for_component"
        )

        default_label = st.session_state["component_labels"].get(dataset_for_comp, "")
        component_type = st.text_input(
            "Component type (Oil & Gas term)",
            value=(default_label or "FPSO / Pipeline / Wellhead / Subsea"),
            key=make_word := f"pb_component_type_{proj_sel or new_project_name or 'NoProject'}"
        )

        # If model is not trained for dataset, provide quick training option (RandomForest only)
        if dataset_for_comp and dataset_for_comp not in st.session_state["models"]:
            with st.expander("Train model for selected dataset (quick)", expanded=False):
                st.write("Quick train Random Forest (same algorithm as main training). Adjust test size then train.")
                quick_test_size = st.slider("Test size", 0.05, 0.5, 0.2, step=0.01, key=f"quick_ts_{dataset_for_comp}")
                if st.button("⚙️ Quick Train", key=f"quick_train_btn_{dataset_for_comp}"):
                    try:
                        bundle_q = train_random_forest_on_df(st.session_state["datasets"][dataset_for_comp], test_size=float(quick_test_size))
                        st.session_state["models"][dataset_for_comp] = bundle_q
                        st.success(f"Model trained for {dataset_for_comp} (RMSE: {bundle_q['metrics']['rmse']:,.2f}, R²: {bundle_q['metrics']['r2']:.3f})")
                    except Exception as e:
                        st.error(f"Quick training failed: {e}")

        if dataset_for_comp and dataset_for_comp in st.session_state["models"]:
            st.markdown("**Component feature inputs** *(leave blank to auto-fill with training medians where NaN handling is applied)*")
            feat_cols = st.session_state["models"][dataset_for_comp]["features"]
            cols = st.columns(2)
            comp_inputs = {}
            for i, c in enumerate(feat_cols):
                key = f"pb_{proj_sel}_{dataset_for_comp}_feature_{i}_{c}"
                comp_inputs[c] = cols[i % 2].text_input(c, key=key)

            st.markdown("---")
            st.markdown("**Cost Percentage Inputs (EPCIC / Pre-Dev / Owner / Contingency / Escalation)**")
            cp1, cp2, cp3, cp4, cp5 = st.columns(5)
            epcic_percentages_pb = {
                "Engineering": cp1.number_input("Engineering (%)", 0.0, 100.0, 0.0, key=f"pb_eng_{proj_sel}"),
                "Procurement": cp2.number_input("Procurement (%)", 0.0, 100.0, 0.0, key=f"pb_proc_{proj_sel}"),
                "Construction": cp3.number_input("Construction (%)", 0.0, 100.0, 0.0, key=f"pb_const_{proj_sel}"),
                "Installation": cp4.number_input("Installation (%)", 0.0, 100.0, 0.0, key=f"pb_inst_{proj_sel}"),
                "Commissioning": cp5.number_input("Commissioning (%)", 0.0, 100.0, 0.0, key=f"pb_comm_{proj_sel}"),
            }
            pd1, pd2 = st.columns(2)
            predev_pct = pd1.number_input("Pre-Development (%)", 0.0, 100.0, 0.0, key=f"pb_predev_{proj_sel}")
            owners_pct = pd2.number_input("Owner's Cost (%)", 0.0, 100.0, 0.0, key=f"pb_owners_{proj_sel}")
            ct1, ct2 = st.columns(2)
            contingency_pct = ct1.number_input("Contingency (%)", 0.0, 100.0, 0.0, key=f"pb_cont_{proj_sel}")
            escalation_pct = ct2.number_input("Escalation & Inflation (%)", 0.0, 100.0, 0.0, key=f"pb_escal_{proj_sel}")

            if proj_sel:
                if st.button("➕ Predict & Add Component", key=f"pb_add_comp_{proj_sel}_{dataset_for_comp}"):
                    if proj_sel not in st.session_state["projects"]:
                        st.error("Please create/select a project first.")
                    else:
                        # Prepare inputs and predict using stored model/scaler/imputer
                        mb = st.session_state["models"][dataset_for_comp]
                        row = {}
                        for f in mb["features"]:
                            v = comp_inputs.get(f, "")
                            if v is None or str(v).strip() == "":
                                row[f] = np.nan
                            else:
                                try:
                                    row[f] = float(v)
                                except Exception:
                                    row[f] = np.nan
                        try:
                            df_input_raw = pd.DataFrame([row], columns=mb["features"])
                            X_imputed = pd.DataFrame(mb['imputer'].transform(df_input_raw), columns=mb['features'])
                            X_scaled = mb['scaler'].transform(X_imputed)
                            p = float(mb['model'].predict(X_scaled)[0])
                            # breakdown
                            res = {"Project Name": proj_sel, **row, mb['target']: round(p, 2)}
                            epcic_breakdown = {}
                            for phase, pct in epcic_percentages_pb.items():
                                cost = round(p * (pct / 100.0), 2)
                                res[f"{phase} Cost"] = cost
                                epcic_breakdown[phase] = {"cost": cost, "percentage": pct}
                            predev_cost = round(p * (predev_pct / 100.0), 2)
                            owners_cost = round(p * (owners_pct / 100.0), 2)
                            contingency_base = p + owners_cost
                            contingency_cost = round(contingency_base * (contingency_pct / 100.0), 2)
                            escalation_base = p + owners_cost
                            escalation_cost = round(escalation_base * (escalation_pct / 100.0), 2)
                            grand_total = round(p + owners_cost + contingency_cost + escalation_cost, 2)

                            comp_entry = {
                                "component_type": component_type or default_label or "Component",
                                "dataset": dataset_for_comp,
                                "inputs": {k: v for k, v in row.items()},
                                "prediction": p,
                                "breakdown": {
                                    "epcic": epcic_breakdown,
                                    "predev_cost": predev_cost,
                                    "owners_cost": owners_cost,
                                    "contingency_cost": contingency_cost,
                                    "escalation_cost": escalation_cost,
                                    "grand_total": grand_total,
                                    "target_col": mb['target']
                                }
                            }
                            st.session_state["projects"][proj_sel]["components"].append(comp_entry)
                            st.session_state["component_labels"][dataset_for_comp] = component_type or default_label
                            if not st.session_state["projects"][proj_sel]["currency"]:
                                st.session_state["projects"][proj_sel]["currency"] = currency
                            st.success(f"Added {comp_entry['component_type']} ({dataset_for_comp}) to '{proj_sel}'.")
                        except Exception as e:
                            st.error(f"Failed to predict component: {e}")

        st.markdown("---")
        st.subheader("Current Project Overview")
        if st.session_state["projects"]:
            sel = st.selectbox("View/Edit project", list(st.session_state["projects"].keys()), key="pb_view_project_select")
            proj = st.session_state["projects"][sel]
            comps = proj.get("components", [])
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

                # Simple visuals
                st.subheader("📊 Component Composition (Grand Total)")
                stack_rows = []
                for c in comps:
                    capex = float(c["prediction"])
                    owners = float(c["breakdown"]["owners_cost"])
                    cont = float(c["breakdown"]["contingency_cost"])
                    escal = float(c["breakdown"]["escalation_cost"])
                    predev = float(c["breakdown"]["predev_cost"])
                    stack_rows.append({"Component": c["component_type"], "CAPEX": capex, "Owners": owners,
                                       "Contingency": cont, "Escalation": escal, "PreDev": predev})
                dfc_stack = pd.DataFrame(stack_rows).groupby("Component", as_index=False).sum()
                if not dfc_stack.empty:
                    cats = ["CAPEX", "Owners", "Contingency", "Escalation", "PreDev"]
                    colors = ["#2E86AB","#6C757D","#C0392B","#17A589","#9B59B6"]
                    x = np.arange(len(dfc_stack["Component"]))
                    fig, ax = plt.subplots(figsize=(min(12, 1.2*len(x)+6), 6))
                    bottom = np.zeros(len(x))
                    for ccol, colname in zip(colors, cats):
                        vals = dfc_stack[colname].values
                        ax.bar(x, vals, bottom=bottom, color=ccol, label=colname)
                        bottom += vals
                    ax.set_xticks(x); ax.set_xticklabels(dfc_stack["Component"], rotation=30, ha="right")
                    ax.set_ylabel(f"Cost {proj.get('currency','')}".strip())
                    ax.set_title("Component Composition (Grand Total)")
                    ax.legend(ncols=5, fontsize=9, loc="upper center", bbox_to_anchor=(0.5, 1.12))
                    ax.grid(axis="y", linestyle="--", alpha=0.4)
                    fig.tight_layout()
                    st.pyplot(fig, use_container_width=True)

                # Component remove controls
                for idx, c in enumerate(comps):
                    cc1, cc2, cc3 = st.columns([6, 3, 1])
                    cc1.write(f"**{c['component_type']}** — *{c['dataset']}*")
                    cc2.write(f"Grand Total: {c['breakdown']['grand_total']:,.2f}")
                    if cc3.button("🗑️", key=f"pb_del_comp_{sel}_{idx}"):
                        comps.pop(idx)
                        st.experimental_rerun()

                # Export project
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    dfc.to_excel(writer, sheet_name="Components", index=False)
                buffer.seek(0)
                st.download_button("⬇️ Download Project (Excel)", buffer,
                                   file_name=f"{sel}_project.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                st.download_button("⬇️ Download Project (JSON)",
                                   data=json.dumps(st.session_state["projects"][sel], indent=2),
                                   file_name=f"{sel}.json", mime="application/json")
                up = st.file_uploader("Import project JSON", type=["json"], key=f"pb_import_json_{sel}")
                if up is not None:
                    try:
                        data = json.load(up)
                        st.session_state["projects"][sel] = data
                        st.success("Project imported and replaced.")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Failed to import: {e}")

with tab3:
    st.header("🅚 Compare Projects")
    proj_names = list(st.session_state["projects"].keys())
    if len(proj_names) < 2:
        st.info("Create at least two projects to compare.")
    else:
        compare = st.multiselect("Pick projects to compare", proj_names, default=proj_names[:2], key="compare_select")
        if len(compare) >= 2:
            comp_rows = []
            for p in compare:
                proj = st.session_state["projects"][p]
                grand_total = proj.get("totals", {}).get("grand_total", 0.0)
                capex_sum = proj.get("totals", {}).get("capex_sum", 0.0)
                comp_rows.append({"Project": p, "CAPEX Sum": capex_sum, "Grand Total": grand_total})
            dft = pd.DataFrame(comp_rows).set_index("Project")
            st.dataframe(dft.style.format("{:,.2f}"), use_container_width=True)

            # Grand totals bar
            st.subheader("📊 Project Grand Totals")
            fig, ax = plt.subplots(figsize=(min(12, 1.2*len(dft)+6), 5))
            bars = ax.bar(dft.index, dft["Grand Total"], color="#2E86AB")
            ax.set_title("Project Grand Totals")
            ax.set_ylabel("Cost")
            ax.grid(axis="y", linestyle="--", alpha=0.4)
            ax.tick_params(axis='x', rotation=25)
            for b in bars:
                ax.annotate(f"{b.get_height():,.0f}", (b.get_x()+b.get_width()/2, b.get_height()),
                            ha='center', va='bottom', fontsize=9)
            fig.tight_layout()
            st.pyplot(fig, use_container_width=True)

            # Project composition stacked
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
            comp_df = pd.DataFrame(comp_rows).set_index("Project").reset_index()
            st.subheader("🏗️ Project Composition (Stacked)")
            cats = ["CAPEX","Owners","Contingency","Escalation","PreDev"]
            colors = ["#2E86AB","#6C757D","#C0392B","#17A589","#9B59B6"]
            x = np.arange(len(comp_df["Project"]))
            fig, ax = plt.subplots(figsize=(min(12, 1.2*len(x)+6), 6))
            bottom = np.zeros(len(x))
            for ccol, colname in zip(colors, cats):
                vals = comp_df[colname].values
                ax.bar(x, vals, bottom=bottom, color=ccol, label=colname)
                bottom += vals
            ax.set_xticks(x); ax.set_xticklabels(comp_df["Project"], rotation=25, ha="right")
            ax.set_ylabel("Cost")
            ax.set_title("Project Composition (Grand Total)")
            ax.legend(ncols=5, fontsize=9, loc="upper center", bbox_to_anchor=(0.5, 1.12))
            ax.grid(axis="y", linestyle="--", alpha=0.4)
            fig.tight_layout()
            st.pyplot(fig, use_container_width=True)

            # If exactly two projects selected, show simple waterfall-like differences
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
                cats = ["CAPEX","Owners","Contingency","Escalation","PreDev"]
                vals = [delta_dict.get(k,0.0) for k in cats]
                cum = np.cumsum([0]+vals[:-1])
                colors = ["#2E86AB" if v>=0 else "#C0392B" for v in vals]
                fig, ax = plt.subplots(figsize=(8, 5))
                for i,(v, base, ccol) in enumerate(zip(vals, cum, colors)):
                    ax.bar(i, v, bottom=base, color=ccol)
                    ax.annotate(f"{v:+,.0f}", (i, base + v/2), ha="center", va="center", color="white", fontsize=9)
                ax.set_xticks(range(len(cats))); ax.set_xticklabels(cats, rotation=0)
                total = sum(vals)
                ax.axhline(0, color="black", linewidth=0.8)
                ax.set_title(f"Δ Grand Total Waterfall (Total Δ = {total:+,.0f})")
                ax.set_ylabel("Δ Cost")
                ax.grid(axis="y", linestyle="--", alpha=0.4)
                fig.tight_layout()
                st.pyplot(fig, use_container_width=True)
