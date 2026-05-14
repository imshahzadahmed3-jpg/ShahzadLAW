import streamlit as st
import pandas as pd
import os
from utils.database import (init_db, add_transaction, load_transactions,
                            clear_db, get_profile, upsert_profile,
                            get_uploaded_files, delete_transactions_by_file)
from utils.pdf_parser import process_pdf
from utils.word_export import export_to_word

init_db()

st.set_page_config(page_title="ShahzadLAW Audit", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

* { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }

/* Remove all streamlit default overrides that break text */
.stApp { background: #f0f4f8 !important; }

/* Fix main area - force dark text everywhere */
.main .block-container { 
    background: #f0f4f8 !important; 
    padding: 2rem 3rem;
    color: #1a202c !important;
}
.main .block-container p,
.main .block-container span,
.main .block-container div,
.main .block-container label { 
    color: #1a202c !important; 
}

/* Sidebar */
[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(180deg, #0d1b2a 0%, #1a3a5c 100%) !important;
    padding: 2rem 1.5rem;
}
[data-testid="stSidebar"] * { color: #ffffff !important; }
[data-testid="stSidebar"] .stRadio label { 
    color: #cbd5e0 !important; 
    font-size: 0.9rem;
}
[data-testid="stSidebar"] .stRadio label:hover { color: #ffffff !important; }

/* Page Header Banner */
.page-header {
    background: linear-gradient(135deg, #0d1b2a 0%, #1a3a5c 100%);
    padding: 30px 40px;
    border-radius: 12px;
    margin-bottom: 30px;
    border-left: 6px solid #d4a017;
}
.page-header h1 {
    color: #ffffff !important;
    font-size: 2rem;
    font-weight: 800;
    margin: 0 0 5px 0;
    letter-spacing: -0.5px;
}
.page-header p {
    color: #93c5fd !important;
    margin: 0;
    font-size: 0.95rem;
}

/* Metric Cards */
.kpi-card {
    background: #ffffff;
    border-radius: 10px;
    padding: 24px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    margin-bottom: 16px;
    border-top: 4px solid #1a3a5c;
}
.kpi-card .kpi-label {
    color: #718096 !important;
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
}
.kpi-card .kpi-value {
    font-size: 1.9rem;
    font-weight: 800;
    margin: 0;
    line-height: 1;
}

/* File Archive Card */
.file-card {
    background: #ffffff;
    border-radius: 8px;
    padding: 18px 22px;
    margin-bottom: 12px;
    border: 1px solid #e2e8f0;
    border-left: 5px solid #d4a017;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.file-card .file-name { 
    color: #0d1b2a !important;
    font-weight: 700;
    font-size: 1rem;
}
.file-card .file-meta { 
    color: #718096 !important;
    font-size: 0.85rem;
    margin-top: 4px;
}
.synced-badge {
    display: inline-block;
    background: #d1fae5;
    color: #065f46 !important;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
}

/* Section headings */
.section-title {
    color: #0d1b2a !important;
    font-size: 1.1rem;
    font-weight: 700;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 2px solid #e2e8f0;
}

/* Buttons */
.stButton > button {
    background: #1a3a5c !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 700 !important;
    height: 44px !important;
    font-size: 0.9rem !important;
    width: 100%;
    transition: background 0.2s;
}
.stButton > button:hover {
    background: #0d1b2a !important;
}

/* Input fields */
.stTextInput > div > div > input,
.stSelectbox > div > div > div {
    background: #ffffff !important;
    color: #1a202c !important;
    border: 1px solid #cbd5e0 !important;
    border-radius: 6px !important;
}

/* Info/Warning boxes */
.stInfo { background: #dbeafe !important; border-radius: 6px !important; }
.stInfo p { color: #1e40af !important; }
.stWarning p { color: #92400e !important; }
.stSuccess p { color: #065f46 !important; }

/* Dividers */
.section-divider {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 24px 0;
}
</style>
""", unsafe_allow_html=True)

# Session State
if 'pending_tx' not in st.session_state:
    st.session_state.pending_tx = None

# === SIDEBAR ===
with st.sidebar:
    st.markdown("### ⚖️ ShahzadLAW")
    st.markdown("<div style='color:#93c5fd; font-size:0.8rem; margin-bottom:20px;'>Global Audit Intelligence</div>", unsafe_allow_html=True)
    st.divider()

    view_mode = st.radio("Access Level", ["Investor Portal", "Audit Manager"])

    admin_access = False
    if view_mode == "Audit Manager":
        st.markdown("---")
        pin = st.text_input("Admin PIN", type="password", placeholder="Enter PIN...")
        correct = os.getenv("ADMIN_PASSWORD", "admin123")
        if pin == correct:
            admin_access = True
            st.success("✓ Authorized")
        elif pin:
            st.error("✗ Invalid PIN")

# === MAIN CONTENT ===
if view_mode == "Audit Manager" and admin_access:

    # Header
    st.markdown("""
    <div class="page-header">
        <h1>🛡️ Audit Manager Dashboard</h1>
        <p>Secure data management & bank statement synchronization</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["  📤  Import Statements  ", "  📁  File Archive  "])

    with tab1:
        col1, col2 = st.columns([1, 2], gap="large")

        with col1:
            st.markdown("<div class='section-title'>Upload Bank PDF</div>", unsafe_allow_html=True)
            bank_choice = st.selectbox("Select Bank Format", ["Meezan", "Alfalah", "Auto-Detect"])
            uploaded_files = st.file_uploader("Choose PDF Files", type="pdf", accept_multiple_files=True, label_visibility="collapsed")
            run_btn = st.button("🚀 Process & Sync to Cloud")

            if run_btn:
                if not uploaded_files:
                    st.warning("Please select at least one PDF file.")
                else:
                    all_tx = []
                    progress_bar = st.progress(0, text="Processing...")
                    for i, uf in enumerate(uploaded_files):
                        try:
                            tmp = f"temp_{uf.name}"
                            with open(tmp, "wb") as f:
                                f.write(uf.getbuffer())
                            txs = process_pdf(tmp, bank_choice)
                            if txs:
                                for t in txs:
                                    t['source_file'] = uf.name
                                all_tx.extend(txs)
                                st.success(f"✓ {uf.name}: {len(txs)} rows found")
                            else:
                                st.error(f"✗ {uf.name}: No data extracted. Check format.")
                            os.remove(tmp)
                        except Exception as e:
                            st.error(f"✗ Error in {uf.name}: {e}")
                        progress_bar.progress((i + 1) / len(uploaded_files))

                    if all_tx:
                        st.session_state.pending_tx = all_tx
                        st.rerun()

        with col2:
            st.markdown("<div class='section-title'>Import Summary</div>", unsafe_allow_html=True)
            if uploaded_files:
                st.markdown(f"**{len(uploaded_files)} file(s) selected** for processing.")
            else:
                st.info("Upload PDFs on the left and click Process to begin.")

    with tab2:
        st.markdown("<div class='section-title'>Synchronized File Archive</div>", unsafe_allow_html=True)
        files = get_uploaded_files()
        df_all = load_transactions()

        if not files:
            st.info("No files in archive. Import bank statements to begin.")
        else:
            for f in files:
                fd = df_all[df_all['source_file'] == f]
                if not fd.empty:
                    bank = fd['bank'].iloc[0]
                    count = len(fd)
                    date_from = fd['transaction_date'].min()
                    date_to = fd['transaction_date'].max()
                    acct = fd['account_number'].iloc[0] or 'N/A'

                    col_info, col_del = st.columns([5, 1])
                    with col_info:
                        st.markdown(f"""
                        <div class="file-card">
                            <div class="file-name">{f} &nbsp; <span class="synced-badge">SYNCED</span></div>
                            <div class="file-meta">
                                🏦 {bank} &nbsp;|&nbsp; 📋 {count} transactions &nbsp;|&nbsp; 🗓 {date_from} → {date_to}
                                <br>Account: {acct}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_del:
                        if st.button("🗑 Remove", key=f"del_{f}"):
                            delete_transactions_by_file(f)
                            st.rerun()

    # === VERIFICATION ===
    if st.session_state.pending_tx:
        st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>🔍 Profile Verification</div>", unsafe_allow_html=True)

        unique_ids = {t['account_number']: t['party_name']
                      for t in st.session_state.pending_tx if t['account_number']}
        new_profiles = []
        for acc_id, p_name in unique_ids.items():
            existing = get_profile(acc_id)
            if not existing:
                new_profiles.append({'id': acc_id, 'extracted': p_name, 'status': 'New'})
            elif existing['name'].upper() != p_name.upper():
                new_profiles.append({'id': acc_id, 'extracted': p_name,
                                     'status': 'Conflict', 'existing': existing['name']})

        if new_profiles:
            with st.form("verify_form"):
                updates = {}
                for p in new_profiles:
                    st.markdown(f"**Account:** `{p['id']}`")
                    if p['status'] == 'New':
                        updates[p['id']] = st.text_input(f"Register name for {p['id']}", value=p['extracted'])
                    else:
                        st.info(f"Conflict: DB has **{p['existing']}**, extracted **{p['extracted']}**")
                        updates[p['id']] = st.radio(f"Use which name for {p['id']}?",
                                                     [p['existing'], p['extracted']])
                if st.form_submit_button("✅ Commit All to Cloud"):
                    for acc_id, name in updates.items():
                        upsert_profile(acc_id, name)
                    for t in st.session_state.pending_tx:
                        n = updates.get(t['account_number'], t['party_name'])
                        add_transaction(t['bank'], t['transaction_date'], t['description'],
                                        t['debit'], t['credit'], n, t['account_number'],
                                        t['is_tax'], t['source_file'])
                    st.session_state.pending_tx = None
                    st.success("Ledger updated successfully!")
                    st.rerun()
        else:
            for t in st.session_state.pending_tx:
                prof = get_profile(t['account_number'])
                n = prof['name'] if prof else t['party_name']
                add_transaction(t['bank'], t['transaction_date'], t['description'],
                                t['debit'], t['credit'], n, t['account_number'],
                                t['is_tax'], t['source_file'])
            st.session_state.pending_tx = None
            st.success("Import complete!")
            st.rerun()

elif view_mode == "Investor Portal":

    # Header
    st.markdown("""
    <div class="page-header">
        <h1>🏛️ Investor Statement Portal</h1>
        <p>Search your account to view verified transaction history</p>
    </div>
    """, unsafe_allow_html=True)

    search = st.text_input("", placeholder="🔍  Enter your Name or IBAN / Account Number...",
                           label_visibility="collapsed")

    if search:
        df = load_transactions()
        if df.empty:
            st.info("The ledger is currently empty. Please contact the Administrator.")
        else:
            mask = (
                df['party_name'].str.contains(search, case=False, na=False) |
                df['account_number'].str.contains(search, case=False, na=False)
            )
            filtered = df[mask]

            if filtered.empty:
                st.warning("No records found. Please check your name or account number and try again.")
            else:
                calc = filtered[filtered['is_tax'] == False]
                tax_rows = filtered[filtered['is_tax'] == True]
                in_v = calc['credit'].sum()
                out_v = calc['debit'].sum()
                tax_v = tax_rows['debit'].sum() + tax_rows['credit'].sum()
                net = in_v - out_v - tax_v

                st.markdown("<div class='section-title'>Account Summary</div>", unsafe_allow_html=True)
                c1, c2, c3, c4 = st.columns(4)
                c1.markdown(f"""<div class="kpi-card" style="border-top-color:#059669;">
                    <div class="kpi-label">Total Received</div>
                    <div class="kpi-value" style="color:#059669;">Rs.{in_v:,.0f}</div>
                </div>""", unsafe_allow_html=True)
                c2.markdown(f"""<div class="kpi-card" style="border-top-color:#dc2626;">
                    <div class="kpi-label">Total Paid Out</div>
                    <div class="kpi-value" style="color:#dc2626;">Rs.{out_v:,.0f}</div>
                </div>""", unsafe_allow_html=True)
                c3.markdown(f"""<div class="kpi-card" style="border-top-color:#d97706;">
                    <div class="kpi-label">Tax / Deductions</div>
                    <div class="kpi-value" style="color:#d97706;">Rs.{tax_v:,.0f}</div>
                </div>""", unsafe_allow_html=True)
                c4.markdown(f"""<div class="kpi-card" style="border-top-color:#1a3a5c;">
                    <div class="kpi-label">Net Balance</div>
                    <div class="kpi-value" style="color:#1a3a5c;">Rs.{net:,.0f}</div>
                </div>""", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("<div class='section-title'>Transaction History</div>", unsafe_allow_html=True)
                st.dataframe(
                    filtered[['transaction_date', 'bank', 'description', 'debit', 'credit']],
                    use_container_width=True, height=350
                )

                if st.button("📄 Download Statement (.docx)"):
                    path = export_to_word(filtered, {'credit': in_v, 'debit': out_v, 'tax': tax_v})
                    with open(path, "rb") as f:
                        st.download_button("⬇️ Download Now", f,
                                           file_name=f"Statement_{search}.docx")
    else:
        st.markdown("""
        <div style="background:white; border-radius:10px; padding:40px; text-align:center; 
                    border:1px solid #e2e8f0; margin-top:20px; box-shadow:0 2px 8px rgba(0,0,0,0.06);">
            <div style="font-size:3rem;">🏛️</div>
            <div style="color:#0d1b2a; font-size:1.2rem; font-weight:700; margin-top:10px;">
                Secure Investor Ledger
            </div>
            <div style="color:#718096; margin-top:8px; font-size:0.9rem;">
                Enter your name or account number above to view your verified transaction history.
            </div>
        </div>
        """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="background:#fff7ed; border:1px solid #fed7aa; border-radius:10px; 
                padding:30px; text-align:center; margin-top:20px;">
        <div style="font-size:2rem;">🔒</div>
        <div style="color:#92400e; font-weight:700; margin-top:8px;">Restricted Area</div>
        <div style="color:#78350f; font-size:0.9rem; margin-top:4px;">
            Please enter your Admin PIN in the sidebar to access management tools.
        </div>
    </div>
    """, unsafe_allow_html=True)
