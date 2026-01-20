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
    initial_sidebar_state="expanded"
)

# Password protection
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
        if '' in col.upper():
            return ''
        elif '' in col.upper() or '$' in col:
            return ''
        elif '' in col.upper() or '€' in col:
            return ''
        elif '' in col.upper() or '£' in col:
            return ''
    return ''

def format_currency(amount, currency=''):
    return f"{currency} {amount:.2f}"

def download_all_predictions():
    if not st.session_state['predictions'] or all(len(preds) == 0 for preds in st.session_state['predictions'].values()):
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

def main():
    st.title('💲CAPEX AI RT2025💲')
    if 'datasets' not in st.session_state:
        st.session_state['datasets'] = {}
    if 'predictions' not in st.session_state:
        st.session_state['predictions'] = {}
    if 'processed_excel_files' not in st.session_state:
        st.session_state['processed_excel_files'] = set()
        
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
            
    # Add horizontal line in sidebar
    st.sidebar.markdown('---')
    
    st.sidebar.header('System Controls')
    if st.sidebar.button("🔄 Refresh System"):
        list_csvs_from_manifest.clear()

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
        data_link = "https://petronas.sharepoint.com/sites/ecm_ups_coe/confidential/DFE%20Cost%20Engineering/Forms/AllItems.aspx?id=%2Fsites%2Fecm%5Fups%5Fcoe%2Fconfidential%2FDFE%20Cost%20Engineering%2F2%2ETemplate%20Tools%2FCost%20Predictor%2FDatabase%2FCAPEX%20%2D%20RT%20Q1%202025&viewid=25092e6d%2D373d%2D41fe%2D8f6f%2D486cd8cdd5b8"  # <-- CHANGE THIS TO YOUR ACTUAL LINK
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
        # Reconstruct full dataframe with project names for display
        df_display = pd.concat([project_names.reset_index(drop=True), df_imputed], axis=1)
        df_display.columns = [df.columns[0]] + list(df_imputed.columns)
        st.write('Dataset Shape:', df_display.shape)
        st.dataframe(df_display.head())

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
        st.subheader("🔧 Cost Breakdown Percentage Input")
        st.markdown("Enter the percentage breakdown for the following categories. You may leave the input to 0% if unapplicable.")
        epcic_percentages = {}
        col_ep1, col_ep2, col_ep3, col_ep4, col_ep5 = st.columns(5)
        epcic_percentages["Engineering"] = col_ep1.number_input("Engineering (%)", min_value=0.0, max_value=100.0, value=0.0)
        epcic_percentages["Procurement"] = col_ep2.number_input("Procurement (%)", min_value=0.0, max_value=100.0, value=0.0)
        epcic_percentages["Construction"] = col_ep3.number_input("Construction (%)", min_value=0.0, max_value=100.0, value=0.0)
        epcic_percentages["Installation"] = col_ep4.number_input("Installation (%)", min_value=0.0, max_value=100.0, value=0.0)
        epcic_percentages["Commissioning"] = col_ep5.number_input("Commissioning (%)", min_value=0.0, max_value=100.0, value=0.0)
        epcic_total = sum(epcic_percentages.values())
        if abs(epcic_total - 100.0) > 1e-3 and epcic_total > 0:
            st.warning(f"⚠️ EPCIC total is {epcic_total:.2f}%. Please ensure it sums to 100% if applicable.")
        st.markdown("**Refer to Escalation and Inflation FY2025-FY2029 document for percentage breakdown by facilities and project types.*")
        st.subheader("💼 Pre-Dev and Owner's Cost Percentage Input")
        st.markdown("")
        col_pd1, col_pd2 = st.columns(2)
        predev_percentage = col_pd1.number_input("Enter Pre-Development (%)", min_value=0.0, max_value=100.0, value=0.0)
        owners_percentage = col_pd2.number_input("Enter Owner's Cost (%)", min_value=0.0, max_value=100.0, value=0.0)
        col_cont1, col_cont2 = st.columns(2)
        with col_cont1:
            st.subheader("⚠️ Cost Contingency Input")
            st.markdown("")
            contingency_percentage = st.number_input("Enter Cost Contingency (%)", min_value=0.0, max_value=100.0, value=0.0)
        with col_cont2:
            st.subheader("📈 Escalation & Inflation Percentage Input")
            st.markdown("")
            escalation_percentage = st.number_input("Enter Escalation & Inflation (%)", min_value=0.0, max_value=100.0, value=0.0)
        st.markdown("**High-Level Escalation and Inflation rate is based on compounded percentage for the entire project development.*")

    st.header('Make New Predictions')
    project_name = st.text_input('Enter Project Name')
    num_features = len(X.columns)
    if num_features <= 2:
        cols = st.columns(num_features)
    else:
        cols = []
        for i in range(0, num_features, 2):
            row_cols = st.columns(min(2, num_features - i))
            cols.extend(row_cols)
    new_data = {}
    for i, col in enumerate(X.columns):
        col_idx = i % len(cols) if len(cols) > 0 else 0
        user_val = cols[col_idx].text_input(f'{col}', key=f'input_{col}')
        if user_val.strip().lower() == "nan" or user_val.strip() == "":
            new_data[col] = np.nan
        else:
            try:
                new_data[col] = float(user_val)
            except ValueError:
                new_data[col] = np.nan

    if st.button('Predict'):
        df_input = pd.DataFrame([new_data])
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
        grand_total = round(pred + owners_cost + contingency_cost + escalation_cost, 2)
        result["Grand Total"] = grand_total
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
                        
                        grand_total = round(preds[i] + owners_cost + contingency_cost + escalation_cost, 2)
                        entry["Grand Total"] = grand_total
                        
                        st.session_state['predictions'][selected_dataset_name].append(entry)
                    
                    st.session_state['processed_excel_files'].add(file_id)
                    st.success("Batch prediction successful!")
                else:
                    st.error(f"Excel missing required columns. Needed: {list(X.columns)}")
            else:
                st.error("Excel file must have at least 2 columns (project name + features)")

    with st.expander('Simplified Project List', expanded=True):
        preds = st.session_state['predictions'][selected_dataset_name]
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
    if preds := st.session_state['predictions'][selected_dataset_name]:
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

if __name__ == '__main__':
    main()
