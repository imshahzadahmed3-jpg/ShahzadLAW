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

st.markdown("""
<style>
    .main { background-color: #f8fafc; font-family: 'Inter', sans-serif; }
    .stApp { background-color: #f8fafc; }
    h1, h2, h3 { color: #0f172a; }
    .stButton>button {
        background-color: #2563eb; color: white; border-radius: 8px; font-weight: 600;
        transition: all 0.3s;
    }
    .metric-card {
        background-color: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        text-align: center; border-left: 5px solid #2563eb; margin-bottom: 10px;
    }
    .analysis-card {
        background-color: #f1f5f9; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Session State
if 'pending_tx' not in st.session_state:
    st.session_state.pending_tx = None

# Sidebar Navigation
with st.sidebar:
    st.header("🏦 Ledger System")
    view_mode = st.radio("Select View", ["👤 Investor View", "🔑 Admin Panel"])
    
    admin_access = False
    if view_mode == "🔑 Admin Panel":
        password = st.text_input("Enter Admin Password", type="password")
        if password == "admin123": # Default password
            admin_access = True
            st.success("Access Granted")
        elif password:
            st.error("Incorrect Password")

st.title("🏦 Global Intelligent Ledger")

if view_mode == "🔑 Admin Panel" and admin_access:
    # --- ADMIN PANEL ---
    st.markdown("### 🛠️ Admin Management")
    
    col_a1, col_a2 = st.columns([1, 2])
    
    with col_a1:
        st.subheader("⬆️ Upload Statement")
        bank_choice = st.selectbox("Bank Format", ["Meezan", "Alfalah", "Auto-Detect"])
        uploaded_files = st.file_uploader("Upload PDF(s)", type="pdf", accept_multiple_files=True)
        
        if st.button("Process & Analyze"):
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
        st.subheader("📂 File Analysis & History")
        existing_files = get_uploaded_files()
        df_all = load_transactions()
        
        if existing_files and not df_all.empty:
            for f_name in existing_files:
                f_data = df_all[df_all['source_file'] == f_name]
                if not f_data.empty:
                    with st.container():
                        st.markdown(f"""
                        <div class="analysis-card">
                            <b>File:</b> {f_name}<br>
                            <b>Bank:</b> {f_data['bank'].iloc[0]}<br>
                            <b>ID/Account:</b> {f_data['account_number'].iloc[0] or 'Multiple'}<br>
                            <b>Period:</b> {f_data['transaction_date'].min()} to {f_data['transaction_date'].max()}<br>
                            <b>Records:</b> {len(f_data)}
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button(f"🗑️ Delete {f_name}", key=f"del_{f_name}"):
                            delete_transactions_by_file(f_name)
                            st.rerun()
        else:
            st.info("No files processed yet.")

    # Verification Step (if pending)
    if st.session_state.pending_tx:
        st.divider()
        st.subheader("🤖 Intelligent Verification")
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
                    if p['status'] == 'New':
                        updates[p['id']] = st.text_input(f"New Profile Name for {p['id']}", value=p['extracted'])
                    else:
                        choice = st.radio(f"Conflict for {p['id']}", [p['existing'], p['extracted']])
                        updates[p['id']] = choice
                if st.form_submit_button("Confirm All"):
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
            st.success("Transactions Saved!")
            st.rerun()

elif view_mode == "👤 Investor View":
    # --- INVESTOR VIEW ---
    st.markdown("### 🔍 Search My Ledger")
    search_query = st.text_input("Enter your Name or Account Number / IBAN", placeholder="e.g. Shahzad Ahmed or PK37...")
    
    if search_query:
        df = load_transactions()
        if not df.empty:
            filtered_df = df[
                df['party_name'].str.contains(search_query, case=False, na=False) |
                df['account_number'].str.contains(search_query, case=False, na=False)
            ]
            
            if not filtered_df.empty:
                # Metrics for this specific investor
                calc_df = filtered_df[filtered_df['is_tax'] == False]
                tax_df = filtered_df[filtered_df['is_tax'] == True]
                
                in_amt = calc_df['credit'].sum()
                out_amt = calc_df['debit'].sum()
                tax_amt = tax_df['debit'].sum() + tax_df['credit'].sum()

                c1, c2, c3 = st.columns(3)
                c1.markdown(f"<div class='metric-card'><h4>Total Received</h4><h2 style='color:#10b981;'>Rs. {in_amt:,.2f}</h2></div>", unsafe_allow_html=True)
                c2.markdown(f"<div class='metric-card' style='border-left: 5px solid #ef4444;'><h4>Total Sent</h4><h2 style='color:#ef4444;'>Rs. {out_amt:,.2f}</h2></div>", unsafe_allow_html=True)
                c3.markdown(f"<div class='metric-card' style='border-left: 5px solid #f59e0b;'><h4>Tax/Charges</h4><h2 style='color:#f59e0b;'>Rs. {tax_amt:,.2f}</h2></div>", unsafe_allow_html=True)

                st.dataframe(filtered_df[['transaction_date', 'bank', 'description', 'debit', 'credit']], use_container_width=True)
                
                if st.button("⬇️ Download My Report (.docx)"):
                    file_path = export_to_word(filtered_df, {'credit': in_amt, 'debit': out_amt, 'tax': tax_amt})
                    with open(file_path, "rb") as f:
                        st.download_button("Click to Download", f, file_name="My_Ledger.docx")
            else:
                st.warning("No records found for this name or ID.")
        else:
            st.info("The database is currently empty. Please wait for the Admin to upload records.")
    else:
        st.info("Sir, please enter your details to see your transactions.")
else:
    st.info("Please enter the Admin password in the sidebar to access management tools.")
