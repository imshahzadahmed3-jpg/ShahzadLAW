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

# Professional Audit Theme Configuration
st.set_page_config(page_title="ShahzadLAW | Audit Intelligence", page_icon="⚖️", layout="wide")

# Sophisticated Audit UI CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background-color: #f1f5f9;
    }
    
    /* Sidebar Audit Style */
    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid #1e293b;
    }
    section[data-testid="stSidebar"] * {
        color: #f8fafc !important;
    }

    /* Main Header */
    .main-title {
        color: #0f172a;
        font-weight: 800;
        letter-spacing: -1px;
        border-bottom: 3px solid #eab308;
        padding-bottom: 10px;
        margin-bottom: 30px;
    }

    /* Audit Cards */
    .audit-card {
        background: white;
        padding: 24px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
        margin-bottom: 20px;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #0f172a;
    }

    .metric-label {
        color: #64748b;
        font-size: 0.875rem;
        text-transform: uppercase;
        font-weight: 600;
    }

    /* Professional Table */
    .stDataFrame {
        border: 1px solid #e2e8f0;
        border-radius: 4px;
    }

    /* Action Buttons */
    .stButton>button {
        background-color: #0f172a;
        color: white !important;
        border-radius: 4px;
        font-weight: 600;
        height: 45px;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        background-color: #334155;
        border-color: #eab308;
    }
    
    .status-badge {
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Session State Management
if 'pending_tx' not in st.session_state:
    st.session_state.pending_tx = None

# Sidebar Control
with st.sidebar:
    st.image("https://img.icons8.com/external-flat-icons-inorganic-blue/64/000000/external-audit-business-management-flat-icons-inorganic-blue.png", width=60)
    st.markdown("### AUDIT CONTROL")
    view_mode = st.radio("System Access", ["Investor Portal", "Audit Manager"])
    
    admin_access = False
    if view_mode == "Audit Manager":
        st.divider()
        pin = st.text_input("Security Pin", type="password")
        if pin == os.getenv("ADMIN_PASSWORD", "admin123"):
            admin_access = True
            st.success("Authorized")
        elif pin:
            st.error("Invalid Pin")

# Main Interface
st.markdown(f"<h1 class='main-title'>⚖️ SHAHZAD LAW | {view_mode.upper()}</h1>", unsafe_allow_html=True)

if view_mode == "Audit Manager" and admin_access:
    # --- ADMIN / AUDITOR VIEW ---
    t1, t2 = st.tabs(["📊 Data Import", "📁 File Archive"])
    
    with t1:
        st.subheader("Import Bank Statements")
        c1, c2 = st.columns([1, 2])
        
        with c1:
            bank_choice = st.selectbox("Format Selector", ["Meezan", "Alfalah", "Auto-Detect"])
            uploaded_files = st.file_uploader("Drop PDF Files Here", type="pdf", accept_multiple_files=True)
            
            if st.button("🚀 EXECUTE SYNC"):
                if not uploaded_files:
                    st.warning("Please select files first.")
                else:
                    all_tx = []
                    progress = st.progress(0)
                    for i, uploaded_file in enumerate(uploaded_files):
                        try:
                            temp_path = f"temp_{uploaded_file.name}"
                            with open(temp_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            txs = process_pdf(temp_path, bank_choice)
                            if txs:
                                for t in txs:
                                    t['source_file'] = uploaded_file.name
                                    all_tx.append(t)
                            else:
                                st.error(f"Failed to extract data from {uploaded_file.name}")
                            os.remove(temp_path)
                        except Exception as e:
                            st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                        progress.progress((i + 1) / len(uploaded_files))
                    
                    if all_tx:
                        st.session_state.pending_tx = all_tx
                        st.success(f"Extracted {len(all_tx)} transactions. Proceed to verification.")
                        st.rerun()
                    else:
                        st.error("Extraction failed or no data found in files.")

    with t2:
        st.subheader("Global File Archive")
        files = get_uploaded_files()
        df_all = load_transactions()
        
        if not files:
            st.info("Archive is empty. Sync data to begin.")
        else:
            for f in files:
                f_data = df_all[df_all['source_file'] == f]
                with st.container():
                    st.markdown(f"""
                    <div style="background:white; padding:15px; border-radius:5px; border-left:4px solid #eab308; margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between;">
                            <b>{f}</b>
                            <span class="status-badge" style="background:#dcfce7; color:#166534;">SYNCED</span>
                        </div>
                        <div style="font-size:0.9rem; color:#64748b;">
                            {f_data['bank'].iloc[0] if not f_data.empty else 'N/A'} | 
                            {len(f_data)} Rows | 
                            Period: {f_data['transaction_date'].min()} - {f_data['transaction_date'].max()}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Purge Records: {f}", key=f"purge_{f}"):
                        delete_transactions_by_file(f)
                        st.rerun()

    # Verification Flow
    if st.session_state.pending_tx:
        st.divider()
        st.subheader("🔍 Auditor Verification")
        unique_ids = {t['account_number']: t['party_name'] for t in st.session_state.pending_tx if t['account_number']}
        
        new_profiles = []
        for acc_id, p_name in unique_ids.items():
            existing = get_profile(acc_id)
            if not existing: 
                new_profiles.append({'id': acc_id, 'extracted': p_name, 'status': 'New'})
            elif existing['name'].upper() != p_name.upper(): 
                new_profiles.append({'id': acc_id, 'extracted': p_name, 'status': 'Conflict', 'existing': existing['name']})

        if new_profiles:
            with st.form("verify_audit"):
                updates = {}
                for p in new_profiles:
                    st.markdown(f"**Entity ID:** `{p['id']}`")
                    if p['status'] == 'New':
                        updates[p['id']] = st.text_input(f"Register Name for {p['id']}", value=p['extracted'])
                    else:
                        st.info(f"Existing: {p['existing']} | Found: {p['extracted']}")
                        updates[p['id']] = st.radio(f"Select Primary Name for {p['id']}", [p['existing'], p['extracted']])
                if st.form_submit_button("COMMIT TO CLOUD"):
                    for acc_id, name in updates.items(): upsert_profile(acc_id, name)
                    for t in st.session_state.pending_tx:
                        n = updates.get(t['account_number'], t['party_name'])
                        add_transaction(t['bank'], t['transaction_date'], t['description'], t['debit'], t['credit'], n, t['account_number'], t['is_tax'], t['source_file'])
                    st.session_state.pending_tx = None
                    st.success("Ledger Updated Successfully.")
                    st.rerun()
        else:
            # Auto-save
            for t in st.session_state.pending_tx:
                prof = get_profile(t['account_number'])
                n = prof['name'] if prof else t['party_name']
                add_transaction(t['bank'], t['transaction_date'], t['description'], t['debit'], t['credit'], n, t['account_number'], t['is_tax'], t['source_file'])
            st.session_state.pending_tx = None
            st.success("Automated Import Complete.")
            st.rerun()

elif view_mode == "Investor Portal":
    # --- INVESTOR VIEW ---
    st.subheader("Access Your Ledger")
    search = st.text_input("Enter Entity Name or IBAN Account Number", placeholder="Start typing to search...")
    
    if search:
        df = load_transactions()
        filtered = df[
            df['party_name'].str.contains(search, case=False, na=False) |
            df['account_number'].str.contains(search, case=False, na=False)
        ]
        
        if not filtered.empty:
            # Audit Summary
            calc = filtered[filtered['is_tax'] == False]
            tax = filtered[filtered['is_tax'] == True]
            in_v = calc['credit'].sum()
            out_v = calc['debit'].sum()
            tax_v = tax['debit'].sum() + tax['credit'].sum()

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"<div class='audit-card'><div class='metric-label'>Inbound Value</div><div class='metric-value' style='color:#059669;'>Rs. {in_v:,.2f}</div></div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div class='audit-card'><div class='metric-label'>Outbound Value</div><div class='metric-value' style='color:#dc2626;'>Rs. {out_v:,.2f}</div></div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div class='audit-card'><div class='metric-label'>Statutory Deductions</div><div class='metric-value' style='color:#d97706;'>Rs. {tax_v:,.2f}</div></div>", unsafe_allow_html=True)

            st.dataframe(filtered[['transaction_date', 'bank', 'description', 'debit', 'credit']], use_container_width=True)
            
            st.divider()
            if st.button("📑 GENERATE AUDIT REPORT (.DOCX)"):
                path = export_to_word(filtered, {'credit': in_v, 'debit': out_v, 'tax': tax_v})
                with open(path, "rb") as f:
                    st.download_button("Click to Download Verified Document", f, file_name=f"Audit_Report_{search}.docx")
        else:
            st.warning("No records found in the current audit cycle.")
    else:
        st.info("Welcome to the Shahzad Law Investor Portal. Please provide credentials to view transactions.")
else:
    st.info("Restricted Area. Please provide Audit Manager credentials.")
