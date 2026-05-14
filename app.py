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
    h1, h2, h3 { color: #0f172a; }
    .stButton>button {
        background-color: #2563eb; color: white; border-radius: 8px; font-weight: 600;
        transition: all 0.3s;
    }
    .stButton>button:hover { background-color: #1d4ed8; }
    .metric-card {
        background-color: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        text-align: center; border-left: 5px solid #2563eb;
    }
    .file-chip {
        background: #e2e8f0; padding: 5px 10px; border-radius: 15px; margin: 2px; display: inline-block; font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Session State for Verification
if 'pending_tx' not in st.session_state:
    st.session_state.pending_tx = None
if 'profile_map' not in st.session_state:
    st.session_state.profile_map = {}

st.title("🏦 Global Intelligent Ledger")
st.markdown("Automated banking reconciliation with intelligent profile matching.")

# Sidebar for Operations
with st.sidebar:
    st.header("📂 Data Management")
    
    # 1. Upload Section
    with st.expander("⬆️ Upload Statement", expanded=True):
        bank_choice = st.selectbox("Format", ["Meezan", "Alfalah", "Auto-Detect"])
        uploaded_files = st.file_uploader("Upload PDF(s)", type="pdf", accept_multiple_files=True)
        
        if st.button("Extract & Verify"):
            if uploaded_files:
                all_tx = []
                with st.spinner("Parsing files..."):
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
                else:
                    st.error("No data found.")

    st.divider()
    
    # 2. File Manager
    st.header("🗂️ Managed Files")
    existing_files = get_uploaded_files()
    if existing_files:
        for f_name in existing_files:
            col_f1, col_f2 = st.columns([3, 1])
            col_f1.markdown(f"<span class='file-chip'>{f_name}</span>", unsafe_allow_html=True)
            if col_f2.button("🗑️", key=f"del_{f_name}"):
                delete_transactions_by_file(f_name)
                st.success(f"Deleted {f_name}")
                st.rerun()
    else:
        st.info("No files uploaded yet.")

    st.divider()
    
    # 3. Manual Entry
    with st.expander("➕ Manual Entry"):
        with st.form("manual_entry"):
            m_bank = st.selectbox("Bank", ["Meezan", "Alfalah", "Cash"])
            m_date = st.date_input("Date")
            m_desc = st.text_input("Description")
            m_type = st.selectbox("Type", ["Sent (Debit)", "Received (Credit)", "Tax Deduction"])
            m_party = st.text_input("Party Name")
            m_amount = st.number_input("Amount", min_value=0.0)
            
            if st.form_submit_button("Add"):
                is_tax = (m_type == "Tax Deduction")
                debit = m_amount if m_type in ["Sent (Debit)", "Tax Deduction"] else 0.0
                credit = m_amount if m_type == "Received (Credit)" else 0.0
                add_transaction(m_bank, m_date.strftime("%d/%m/%Y"), m_desc, debit, credit, m_party, "", is_tax, "Manual")
                st.success("Added!")
                st.rerun()

    if st.button("🚨 Reset All Data", type="primary"):
        clear_db()
        st.rerun()

# --- INTELLIGENT VERIFICATION LOOP ---
if st.session_state.pending_tx:
    st.markdown("### 🤖 Intelligent Profile Verification")
    st.info("Sir, kuch naye records mile hain. Please verify karen ke names sahi hain ya naye profile banane hain.")
    
    unique_ids = {}
    for t in st.session_state.pending_tx:
        if t['account_number'] and t['account_number'] not in unique_ids:
            unique_ids[t['account_number']] = t['party_name']

    new_profiles = []
    for acc_id, p_name in unique_ids.items():
        existing = get_profile(acc_id)
        if not existing:
            new_profiles.append({'id': acc_id, 'extracted': p_name, 'status': 'New'})
        elif existing['name'].upper() != p_name.upper():
            new_profiles.append({'id': acc_id, 'extracted': p_name, 'status': 'Conflict', 'existing': existing['name']})

    if new_profiles:
        with st.form("verification_form"):
            updates = {}
            for p in new_profiles:
                st.markdown(f"**ID:** `{p['id']}`")
                if p['status'] == 'New':
                    updates[p['id']] = st.text_input(f"New Profile Name for {p['id']}", value=p['extracted'], key=f"input_{p['id']}")
                else:
                    st.warning(f"Conflict: Extracted '{p['extracted']}' but database says '{p['existing']}'.")
                    choice = st.radio(f"Which name to use for {p['id']}?", [p['existing'], p['extracted']], key=f"radio_{p['id']}")
                    updates[p['id']] = choice
                st.divider()
            
            if st.form_submit_button("✅ Confirm & Save All Transactions"):
                # Save Profiles
                for acc_id, final_name in updates.items():
                    upsert_profile(acc_id, final_name)
                
                # Save Transactions
                for t in st.session_state.pending_tx:
                    final_name = updates.get(t['account_number'], t['party_name'])
                    add_transaction(t['bank'], t['transaction_date'], t['description'], 
                                    t['debit'], t['credit'], final_name, t['account_number'], t['is_tax'], t['source_file'])
                
                st.session_state.pending_tx = None
                st.success("All records saved successfully!")
                st.rerun()
    else:
        # No new profiles to verify, just save
        for t in st.session_state.pending_tx:
            prof = get_profile(t['account_number'])
            name = prof['name'] if prof else t['party_name']
            add_transaction(t['bank'], t['transaction_date'], t['description'], 
                            t['debit'], t['credit'], name, t['account_number'], t['is_tax'], t['source_file'])
        st.session_state.pending_tx = None
        st.success("Transactions imported!")
        st.rerun()

    if st.button("Cancel Import"):
        st.session_state.pending_tx = None
        st.rerun()
    st.stop()

# --- MAIN DASHBOARD AREA ---
df = load_transactions()

if not df.empty:
    st.subheader("🔍 Search & Filter")
    col1, col2 = st.columns([2, 1])
    search_query = col1.text_input("Search Name, ID, or Description")
    bank_filter = col2.selectbox("Bank", ["All", "Meezan", "Alfalah"])

    filtered_df = df.copy()
    if bank_filter != "All":
        filtered_df = filtered_df[filtered_df['bank'] == bank_filter]
    if search_query:
        filtered_df = filtered_df[
            filtered_df['party_name'].str.contains(search_query, case=False, na=False) |
            filtered_df['description'].str.contains(search_query, case=False, na=False) |
            filtered_df['account_number'].str.contains(search_query, case=False, na=False)
        ]

    # Metrics
    tax_df = filtered_df[filtered_df['is_tax'] == True]
    calc_df = filtered_df[filtered_df['is_tax'] == False]
    
    total_received = calc_df['credit'].sum()
    total_sent = calc_df['debit'].sum()
    total_tax = tax_df['debit'].sum() + tax_df['credit'].sum()

    # Bank-wise for report
    meezan_df = calc_df[calc_df['bank'] == 'Meezan']
    alfalah_df = calc_df[calc_df['bank'] == 'Alfalah']

    report_totals = {
        'credit': total_received,
        'debit': total_sent,
        'tax': total_tax,
        'meezan_credit': meezan_df['credit'].sum(),
        'meezan_debit': meezan_df['debit'].sum(),
        'alfalah_credit': alfalah_df['credit'].sum(),
        'alfalah_debit': alfalah_df['debit'].sum()
    }

    st.markdown("### 📊 Totals")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'><h4>Received</h4><h2 style='color:#10b981;'>Rs. {total_received:,.2f}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card' style='border-left: 5px solid #ef4444;'><h4>Sent</h4><h2 style='color:#ef4444;'>Rs. {total_sent:,.2f}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card' style='border-left: 5px solid #f59e0b;'><h4>Tax</h4><h2 style='color:#f59e0b;'>Rs. {total_tax:,.2f}</h2></div>", unsafe_allow_html=True)

    # Transactions Table
    st.markdown("### 📜 Transactions")
    display_df = filtered_df[['transaction_date', 'bank', 'party_name', 'account_number', 'description', 'debit', 'credit', 'source_file']].copy()
    st.dataframe(display_df, use_container_width=True)

    if st.button("⬇️ Download Report"):
        file_path = export_to_word(filtered_df, report_totals)
        with open(file_path, "rb") as f:
            st.download_button("Download .docx", f, file_name="Report.docx")
else:
    st.info("Welcome! Start by uploading a bank statement in the sidebar.")
ally from the sidebar.")
