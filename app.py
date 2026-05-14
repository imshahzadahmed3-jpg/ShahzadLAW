import streamlit as st
import pandas as pd
import os
from utils.database import (init_db, add_transaction, load_transactions, 
                            clear_db, get_profile, upsert_profile, 
                            get_uploaded_files, delete_transactions_by_file)
from utils.pdf_parser import process_pdf
from utils.word_export import export_to_word
from io import BytesIO

# Initialize Database
init_db()

# Premium UI Configuration
st.set_page_config(page_title="Global Intelligent Ledger", page_icon="🏦", layout="wide")

# High Contrast Bank Style CSS
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #fdfdfd;
    }
    
    /* Global Text Colors */
    h1, h2, h3, p, span, label {
        color: #1a202c !important;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #1a365d !important;
    }
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Metric Cards (Bank Style) */
    .metric-card {
        background-color: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        text-align: center;
        border-top: 5px solid #2b6cb0;
        margin-bottom: 15px;
    }
    .metric-card h4 {
        color: #4a5568 !important;
        font-size: 1rem;
        margin-bottom: 10px;
    }
    .metric-card h2 {
        font-size: 1.8rem;
        margin: 0;
    }
    
    /* Analysis Cards */
    .analysis-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #38a169;
        margin-bottom: 15px;
        color: #2d3748 !important;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #2b6cb0;
        color: white !important;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 700;
        width: 100%;
        border: none;
    }
    .stButton>button:hover {
        background-color: #2c5282;
    }
    
    /* Dataframe Visibility */
    [data-testid="stDataFrame"] {
        border: 1px solid #e2e8f0;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Session State
if 'pending_tx' not in st.session_state:
    st.session_state.pending_tx = None

# Sidebar Navigation
with st.sidebar:
    st.markdown("## 🏛️ Bank Navigation")
    view_mode = st.radio("Access Level", ["👤 Investor View", "🔑 Admin Panel"])
    
    admin_access = False
    if view_mode == "🔑 Admin Panel":
        st.markdown("---")
        password = st.text_input("Security Pin", type="password")
        if password == "admin123":
            admin_access = True
            st.success("Authorized")
        elif password:
            st.error("Access Denied")

# Header Section
st.title("🏦 Global Intelligent Ledger")
st.markdown("---")

if view_mode == "🔑 Admin Panel" and admin_access:
    # --- ADMIN PANEL ---
    st.header("🛠️ Central Management")
    
    col_a1, col_a2 = st.columns([1, 2])
    
    with col_a1:
        st.markdown("### 📄 Statement Upload")
        bank_choice = st.selectbox("Format", ["Meezan", "Alfalah", "Auto-Detect"])
        uploaded_files = st.file_uploader("Upload Bank PDF", type="pdf", accept_multiple_files=True)
        
        if st.button("🚀 Process & Sync"):
            if uploaded_files:
                all_tx = []
                for uploaded_file in uploaded_files:
                    temp_path = f"temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    txs = process_pdf(temp_path, bank_choice)
                    if txs:
                        for t in txs:
                            t['source_file'] = uploaded_file.name
                            all_tx.append(t)
                    os.remove(temp_path)
                if all_tx:
                    st.session_state.pending_tx = all_tx
                    st.rerun()

    with col_a2:
        st.markdown("### 📊 Active Ledgers")
        existing_files = get_uploaded_files()
        df_all = load_transactions()
        
        if existing_files and not df_all.empty:
            for f_name in existing_files:
                f_data = df_all[df_all['source_file'] == f_name]
                if not f_data.empty:
                    st.markdown(f"""
                    <div class="analysis-card">
                        <span style='font-size:1.1rem; font-weight:bold;'>{f_name}</span><br>
                        <b>Bank:</b> {f_data['bank'].iloc[0]} | <b>Records:</b> {len(f_data)}<br>
                        <b>Account:</b> {f_data['account_number'].iloc[0] or 'N/A'}<br>
                        <b>Statement Period:</b> {f_data['transaction_date'].min()} to {f_data['transaction_date'].max()}
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"🗑️ Remove Data: {f_name}", key=f"del_{f_name}"):
                        delete_transactions_by_file(f_name)
                        st.rerun()
        else:
            st.info("No bank data currently synchronized.")

    # Verification Step
    if st.session_state.pending_tx:
        st.markdown("---")
        st.header("🤖 Profile Validation")
        unique_ids = {t['account_number']: t['party_name'] for t in st.session_state.pending_tx if t['account_number']}
        new_profiles = []
        for acc_id, p_name in unique_ids.items():
            existing = get_profile(acc_id)
            if not existing: new_profiles.append({'id': acc_id, 'extracted': p_name, 'status': 'New'})
            elif existing['name'].upper() != p_name.upper(): new_profiles.append({'id': acc_id, 'extracted': p_name, 'status': 'Conflict', 'existing': existing['name']})

        if new_profiles:
            with st.form("verify_form"):
                updates = {}
                for p in new_profiles:
                    st.markdown(f"**Account ID:** `{p['id']}`")
                    if p['status'] == 'New':
                        updates[p['id']] = st.text_input(f"Verify Name for {p['id']}", value=p['extracted'])
                    else:
                        choice = st.radio(f"Conflict Detected for {p['id']}", [p['existing'], p['extracted']])
                        updates[p['id']] = choice
                if st.form_submit_button("✅ Authorize All Transactions"):
                    for acc_id, name in updates.items(): upsert_profile(acc_id, name)
                    for t in st.session_state.pending_tx:
                        n = updates.get(t['account_number'], t['party_name'])
                        add_transaction(t['bank'], t['transaction_date'], t['description'], t['debit'], t['credit'], n, t['account_number'], t['is_tax'], t['source_file'])
                    st.session_state.pending_tx = None
                    st.rerun()
        else:
            for t in st.session_state.pending_tx:
                prof = get_profile(t['account_number'])
                n = prof['name'] if prof else t['party_name']
                add_transaction(t['bank'], t['transaction_date'], t['description'], t['debit'], t['credit'], n, t['account_number'], t['is_tax'], t['source_file'])
            st.session_state.pending_tx = None
            st.success("Cloud Synchronization Complete!")
            st.rerun()

elif view_mode == "👤 Investor View":
    # --- INVESTOR VIEW ---
    st.header("🔍 My Private Ledger")
    search_query = st.text_input("Search by Account Number / IBAN or Name", placeholder="e.g. PK37... or Shahzad Ahmed")
    
    if search_query:
        df = load_transactions()
        if not df.empty:
            filtered_df = df[
                df['party_name'].str.contains(search_query, case=False, na=False) |
                df['account_number'].str.contains(search_query, case=False, na=False)
            ]
            
            if not filtered_df.empty:
                # Metrics
                calc_df = filtered_df[filtered_df['is_tax'] == False]
                tax_df = filtered_df[filtered_df['is_tax'] == True]
                in_amt = calc_df['credit'].sum()
                out_amt = calc_df['debit'].sum()
                tax_amt = tax_df['debit'].sum() + tax_df['credit'].sum()

                st.markdown("### 📈 Statement Summary")
                c1, c2, c3 = st.columns(3)
                c1.markdown(f"<div class='metric-card'><h4>Total Received (In)</h4><h2 style='color:#38a169;'>Rs. {in_amt:,.2f}</h2></div>", unsafe_allow_html=True)
                c2.markdown(f"<div class='metric-card'><h4>Total Sent (Out)</h4><h2 style='color:#e53e3e;'>Rs. {out_amt:,.2f}</h2></div>", unsafe_allow_html=True)
                c3.markdown(f"<div class='metric-card'><h4>Tax / Deductions</h4><h2 style='color:#d69e2e;'>Rs. {tax_amt:,.2f}</h2></div>", unsafe_allow_html=True)

                st.markdown("### 🧾 Transaction History")
                st.dataframe(filtered_df[['transaction_date', 'bank', 'description', 'debit', 'credit']], use_container_width=True)
                
                if st.button("📥 Download Detailed Report (.docx)"):
                    file_path = export_to_word(filtered_df, {'credit': in_amt, 'debit': out_amt, 'tax': tax_amt})
                    with open(file_path, "rb") as f:
                        st.download_button("Click to Download Report", f, file_name="Bank_Statement.docx")
            else:
                st.warning("⚠️ No records found for the provided details. Please contact the Admin.")
        else:
            st.info("🏦 The ledger database is currently empty. Please wait for the Admin to upload statements.")
    else:
        st.info("Sir, please enter your details to access your secure bank records.")
else:
    st.info("🔒 Secure System. Please enter the Admin pin in the sidebar.")
