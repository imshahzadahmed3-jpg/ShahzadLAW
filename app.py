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
/* ═══════════════════════════════════════════════════════
   ShahzadLAW — Holographic Glassmorphism Theme v2.0
   Pure White · Emerald Green · High Contrast · Accessible
═══════════════════════════════════════════════════════ */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── CSS VARIABLES ─────────────────────────────────── */
:root {
  --bg-main:       #ffffff;
  --bg-surface:    #f8fafb;
  --text-primary:  #1a1a1a;
  --text-secondary:#2d3748;
  --text-muted:    #4a5568;
  --emerald:       #00a86b;
  --emerald-dark:  #007a4d;
  --emerald-light: #00d68f;
  --navy:          #0a0f1e;
  --navy-mid:      #0d1b2a;
  --gold:          #d4a017;
  --red:           #dc2626;
  --blue-accent:   #3b82f6;

  --holo-gradient: linear-gradient(135deg, #0a0f1e 0%, #0d3b2a 40%, #001a0f 100%);
  --emerald-glow:  0 0 20px rgba(0,168,107,0.4), 0 0 40px rgba(0,168,107,0.15);
  --card-shadow:   0 4px 24px rgba(0,0,0,0.08), 0 1px 4px rgba(0,0,0,0.04);
  --glass-border:  linear-gradient(135deg, rgba(0,168,107,0.4), rgba(59,130,246,0.3), rgba(0,168,107,0.2));
}

/* ── GLOBAL BASE ────────────────────────────────────── */
* { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }

/* ── APP BACKGROUND ─────────────────────────────────── */
.stApp { background: #ffffff !important; }

.main .block-container {
    background: #ffffff !important;
    padding: 2rem 3rem !important;
    max-width: 1400px;
}

/* Force deep black on ALL main content text — no exceptions */
.main .block-container p,
.main .block-container span,
.main .block-container div,
.main .block-container label,
.main .block-container li,
.main .block-container td,
.main .block-container th {
    color: var(--text-primary) !important;
}

/* ── SIDEBAR ─────────────────────────────────────────── */
[data-testid="stSidebar"] > div:first-child {
    background: var(--holo-gradient) !important;
    padding: 2rem 1.5rem;
    border-right: 1px solid rgba(0,168,107,0.3);
}
[data-testid="stSidebar"] * { color: #ffffff !important; }
[data-testid="stSidebar"] .stRadio label {
    color: #a0aec0 !important;
    font-size: 0.9rem;
    font-weight: 500;
    transition: color 0.2s;
}
[data-testid="stSidebar"] .stRadio label:hover { color: #ffffff !important; }
[data-testid="stSidebar"] .stRadio [aria-checked="true"] + label,
[data-testid="stSidebar"] .stRadio [data-checked="true"] ~ div { color: #00d68f !important; }

/* Sidebar brand glow */
[data-testid="stSidebar"] h3 {
    background: linear-gradient(135deg, #00a86b, #3b82f6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 1.3rem !important;
    font-weight: 800 !important;
}

/* ── PAGE HEADER BANNER (Holographic) ───────────────── */
.page-header {
    background: var(--holo-gradient);
    padding: 32px 40px;
    border-radius: 16px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
    /* Holographic border via box-shadow */
    box-shadow:
        0 0 0 1px rgba(0,168,107,0.5),
        0 0 30px rgba(0,168,107,0.15),
        0 8px 32px rgba(0,0,0,0.2);
}
/* Holographic shimmer overlay */
.page-header::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(
        105deg,
        transparent 40%,
        rgba(0,168,107,0.08) 50%,
        rgba(59,130,246,0.06) 55%,
        transparent 65%
    );
    animation: shimmer 4s infinite;
}
@keyframes shimmer {
    0%   { transform: translateX(-100%); }
    100% { transform: translateX(200%); }
}
.page-header h1 {
    color: #ffffff !important;
    font-size: 2rem;
    font-weight: 900;
    margin: 0 0 6px 0;
    letter-spacing: -0.5px;
    text-shadow: 0 0 20px rgba(0,168,107,0.5);
    position: relative;
}
.page-header p {
    color: #00d68f !important;
    margin: 0;
    font-size: 0.95rem;
    font-weight: 500;
    position: relative;
}

/* ── GLASSMORPHISM KPI CARDS ─────────────────────────── */
.kpi-card {
    background: rgba(255,255,255,0.85);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 14px;
    padding: 24px 20px;
    margin-bottom: 16px;
    position: relative;
    /* Holographic gradient border using pseudo-element trick */
    border: 1px solid transparent;
    background-clip: padding-box;
    box-shadow: var(--card-shadow);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.kpi-card::before {
    content: '';
    position: absolute;
    inset: -1px;
    border-radius: 15px;
    background: linear-gradient(135deg, rgba(0,168,107,0.5), rgba(59,130,246,0.3), rgba(0,168,107,0.2));
    z-index: -1;
}
.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.12), 0 0 16px rgba(0,168,107,0.12);
}
.kpi-card .kpi-label {
    color: var(--text-muted) !important;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 10px;
}
.kpi-card .kpi-value {
    font-size: 1.85rem;
    font-weight: 900;
    margin: 0;
    line-height: 1;
}

/* ── GLASSMORPHISM FILE CARDS ────────────────────────── */
.file-card {
    background: rgba(255,255,255,0.9);
    backdrop-filter: blur(8px);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 14px;
    border: 1px solid transparent;
    background-clip: padding-box;
    box-shadow: var(--card-shadow);
    position: relative;
    transition: transform 0.2s;
}
.file-card::before {
    content: '';
    position: absolute;
    inset: -1px;
    border-radius: 13px;
    background: linear-gradient(135deg, rgba(0,168,107,0.6), rgba(59,130,246,0.25));
    z-index: -1;
}
.file-card:hover { transform: translateY(-1px); }
.file-card .file-name {
    color: var(--navy-mid) !important;
    font-weight: 800;
    font-size: 1rem;
}
.file-card .file-meta {
    color: var(--text-muted) !important;
    font-size: 0.85rem;
    margin-top: 4px;
}
.synced-badge {
    display: inline-block;
    background: linear-gradient(135deg, #00a86b, #007a4d);
    color: #ffffff !important;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    box-shadow: 0 2px 8px rgba(0,168,107,0.3);
}

/* ── SECTION TITLES ─────────────────────────────────── */
.section-title {
    color: var(--navy-mid) !important;
    font-size: 1.05rem;
    font-weight: 800;
    margin-bottom: 18px;
    padding-bottom: 10px;
    border-bottom: 2px solid transparent;
    background: linear-gradient(white, white) padding-box,
                linear-gradient(90deg, #00a86b, #3b82f6) border-box;
    border-image: linear-gradient(90deg, #00a86b, #3b82f6) 1;
    border-bottom-width: 2px;
    border-bottom-style: solid;
}

/* ── BUTTONS ─────────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #0a0f1e, #0d1b2a) !important;
    color: #ffffff !important;
    border: 1px solid rgba(0,168,107,0.4) !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    height: 46px !important;
    font-size: 0.9rem !important;
    width: 100%;
    transition: all 0.25s ease !important;
    box-shadow: 0 2px 10px rgba(0,0,0,0.25) !important;
    letter-spacing: 0.4px !important;
    position: relative !important;
    overflow: hidden !important;
}
.stButton > button::before {
    content: '' !important;
    position: absolute !important;
    inset: 0 !important;
    background: linear-gradient(135deg, transparent, rgba(0,168,107,0.1)) !important;
    opacity: 0 !important;
    transition: opacity 0.25s !important;
}
.stButton > button:hover {
    border-color: rgba(0,168,107,0.9) !important;
    box-shadow:
        0 0 0 1px rgba(0,168,107,0.6),
        0 0 20px rgba(0,168,107,0.35),
        0 6px 20px rgba(0,0,0,0.3) !important;
    transform: translateY(-2px) !important;
}

/* ── TABS ────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: #f0f4f8 !important;
    border-radius: 12px !important;
    padding: 5px !important;
    gap: 4px !important;
    border: 1px solid #d1d5db !important;
    box-shadow: inset 0 1px 4px rgba(0,0,0,0.06) !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #374151 !important;
    border-radius: 9px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 10px 22px !important;
    border: none !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.2px !important;
}
.stTabs [data-baseweb="tab"]:hover {
    background: #e5e7eb !important;
    color: #111827 !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #0a0f1e, #0d2a1a) !important;
    color: #00d68f !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.25), 0 0 8px rgba(0,168,107,0.2) !important;
    border-bottom: 2px solid #00a86b !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ── INPUT FIELDS ───────────────────────────────────── */
.stTextInput > div > div > input {
    background: #ffffff !important;
    color: #1a1a1a !important;
    border: 1.5px solid #d1d5db !important;
    border-radius: 10px !important;
    font-size: 0.95rem !important;
    padding: 10px 16px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
.stTextInput > div > div > input:focus {
    border-color: #00a86b !important;
    box-shadow: 0 0 0 3px rgba(0,168,107,0.15) !important;
}
.stTextInput > div > div > input::placeholder { color: #9ca3af !important; }
.stSelectbox > div > div > div {
    background: #ffffff !important;
    color: #1a1a1a !important;
    border: 1.5px solid #d1d5db !important;
    border-radius: 10px !important;
}

/* ── DATAFRAME ──────────────────────────────────────── */
.stDataFrame { border-radius: 12px; overflow: hidden; }
.stDataFrame thead th {
    background: linear-gradient(135deg, #0a0f1e, #0d2a1a) !important;
    color: #00d68f !important;
    font-weight: 700 !important;
    letter-spacing: 0.3px !important;
}
.stDataFrame tbody tr:nth-child(even) { background: #f8fafb !important; }
.stDataFrame tbody tr:hover { background: #f0fdf9 !important; }

/* ── ALERTS / INFO BOXES ────────────────────────────── */
.stAlert, [data-testid="stAlert"] {
    border-radius: 10px !important;
    border-left-width: 4px !important;
}
.stInfo, [data-testid="stAlert"][kind="info"] {
    background: #eff6ff !important;
    border-left-color: #3b82f6 !important;
}
.stInfo p, .stInfo span { color: #1e3a8a !important; }
.stWarning, [data-testid="stAlert"][kind="warning"] {
    background: #fffbeb !important;
    border-left-color: #d97706 !important;
}
.stWarning p, .stWarning span { color: #78350f !important; }
.stSuccess, [data-testid="stAlert"][kind="success"] {
    background: #f0fdf4 !important;
    border-left-color: #00a86b !important;
}
.stSuccess p, .stSuccess span { color: #065f46 !important; }
.stError, [data-testid="stAlert"][kind="error"] {
    background: #fef2f2 !important;
    border-left-color: #dc2626 !important;
}
.stError p, .stError span { color: #7f1d1d !important; }

/* ── PROGRESS BAR ───────────────────────────────────── */
[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, #00a86b, #3b82f6) !important;
    border-radius: 4px !important;
}

/* ── SCROLLBAR ──────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #f1f5f9; border-radius: 4px; }
::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #00a86b, #3b82f6);
    border-radius: 4px;
}

/* ── DIVIDERS ───────────────────────────────────────── */
hr, .section-divider {
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, #d1d5db, transparent) !important;
    margin: 24px 0 !important;
}

/* ── FORM ELEMENTS ──────────────────────────────────── */
.stForm { border: 1px solid #e5e7eb !important; border-radius: 12px !important; }

/* ── MOBILE RESPONSIVE ──────────────────────────────── */

/* Ledger Summary Grid — 2 cols on mobile, 4 on desktop */
.ledger-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr 1fr;
    gap: 20px;
}

@media (max-width: 768px) {
    /* Main container padding */
    .main .block-container {
        padding: 1rem 1rem !important;
    }

    /* Page header smaller on mobile */
    .page-header {
        padding: 20px 18px !important;
        border-radius: 12px !important;
        margin-bottom: 16px !important;
    }
    .page-header h1 {
        font-size: 1.3rem !important;
    }
    .page-header p {
        font-size: 0.82rem !important;
    }

    /* KPI Cards — tighter on mobile */
    .kpi-card {
        padding: 16px 14px !important;
    }
    .kpi-card .kpi-value {
        font-size: 1.35rem !important;
    }

    /* Ledger summary 2 cols on mobile */
    .ledger-grid {
        grid-template-columns: 1fr 1fr !important;
        gap: 12px !important;
    }

    /* Tabs — scrollable on mobile */
    .stTabs [data-baseweb="tab-list"] {
        overflow-x: auto !important;
        flex-wrap: nowrap !important;
        padding: 4px !important;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 0.78rem !important;
        padding: 8px 12px !important;
        white-space: nowrap !important;
    }

    /* File cards full width */
    .file-card {
        padding: 14px 14px !important;
    }
    .file-card .file-name {
        font-size: 0.88rem !important;
    }

    /* Buttons */
    .stButton > button {
        height: 42px !important;
        font-size: 0.85rem !important;
    }

    /* Section titles */
    .section-title {
        font-size: 0.95rem !important;
    }

    /* Hide shimmer animation on mobile for performance */
    .page-header::before {
        display: none !important;
    }
}

@media (max-width: 480px) {
    .page-header h1 { font-size: 1.1rem !important; }
    .kpi-card .kpi-value { font-size: 1.1rem !important; }
    .ledger-grid { grid-template-columns: 1fr 1fr !important; gap: 8px !important; }
}
</style>
""", unsafe_allow_html=True)


# Session State
if 'pending_tx' not in st.session_state:
    st.session_state.pending_tx = None
if 'last_imported' not in st.session_state:
    st.session_state.last_imported = None

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

    tab1, tab2, tab3 = st.tabs([
        "  📤  Import Statements  ",
        "  📁  File Archive & Delete  ",
        "  📊  Global Analysis  "
    ])

    with tab2:  # FILE ARCHIVE
        st.markdown("<div class='section-title'>📁 File Archive & Delete</div>", unsafe_allow_html=True)
        st.markdown("<p style='color:#64748b; font-size:0.9rem;'>Yahan saari upload ki gayi files hain. DELETE dabayen — data Supabase aur local dono jagah se khatam hoga.</p>", unsafe_allow_html=True)

        files = get_uploaded_files()
        df_all = load_transactions()

        if not files:
            st.info("📂 Koi file nahi mili. Import Statements tab se bank PDF upload karen.")
        else:
            for f in files:
                fd = df_all[df_all['source_file'] == f]
                if not fd.empty:
                    bank_name   = fd['bank'].iloc[0] or 'N/A'
                    date_from   = fd['transaction_date'].min()
                    date_to     = fd['transaction_date'].max()
                    acct_no     = fd['account_number'].iloc[0] or 'N/A'
                    acct_name   = fd['party_name'].iloc[0] or 'N/A'
                    total_count = len(fd)
                    total_in    = fd['credit'].sum()
                    total_out   = fd['debit'].sum()

                    col_card, col_btn = st.columns([6, 1])
                    with col_card:
                        st.markdown(f"""
                        <div class="file-card">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <div>
                                    <span class="file-name">📄 {f}</span>
                                    &nbsp;<span class="synced-badge">✓ SYNCED</span>
                                </div>
                                <span style="color:#64748b; font-size:0.8rem;">{total_count} records</span>
                            </div>
                            <hr style="border:none; border-top:1px solid #f1f5f9; margin:10px 0;">
                            <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; font-size:0.88rem;">
                                <div>
                                    <div style="color:#94a3b8; font-size:0.75rem; font-weight:600; text-transform:uppercase;">Account Holder</div>
                                    <div style="color:#0f172a; font-weight:700; margin-top:2px;">{acct_name}</div>
                                </div>
                                <div>
                                    <div style="color:#94a3b8; font-size:0.75rem; font-weight:600; text-transform:uppercase;">Account #</div>
                                    <div style="color:#0f172a; font-family:monospace; margin-top:2px;">{acct_no}</div>
                                </div>
                                <div>
                                    <div style="color:#94a3b8; font-size:0.75rem; font-weight:600; text-transform:uppercase;">Bank</div>
                                    <div style="color:#0f172a; font-weight:700; margin-top:2px;">🏦 {bank_name}</div>
                                </div>
                                <div>
                                    <div style="color:#94a3b8; font-size:0.75rem; font-weight:600; text-transform:uppercase;">Statement Period</div>
                                    <div style="color:#0f172a; margin-top:2px;">📅 {date_from} &nbsp;→&nbsp; {date_to}</div>
                                </div>
                                <div>
                                    <div style="color:#94a3b8; font-size:0.75rem; font-weight:600; text-transform:uppercase;">Total In</div>
                                    <div style="color:#059669; font-weight:700; margin-top:2px;">Rs. {total_in:,.0f}</div>
                                </div>
                                <div>
                                    <div style="color:#94a3b8; font-size:0.75rem; font-weight:600; text-transform:uppercase;">Total Out</div>
                                    <div style="color:#dc2626; font-weight:700; margin-top:2px;">Rs. {total_out:,.0f}</div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col_btn:
                        st.markdown("<br><br>", unsafe_allow_html=True)
                        if st.button("🗑️ DELETE", key=f"del2_{f}",
                                     help=f"'{f}' — Supabase + Local dono se delete hoga"):
                            delete_transactions_by_file(f)
                            st.success(f"✅ '{f}' ka data khatam — Supabase + Local!")
                            st.rerun()

        df_analysis = load_transactions()
        if df_analysis.empty:
            st.info("Koi data nahi mila. Pehle kuch bank statements import karen.")
        else:
            calc_all = df_analysis[df_analysis['is_tax'] == False]
            tax_all  = df_analysis[df_analysis['is_tax'] == True]

            grand_in  = calc_all['credit'].sum()
            grand_out = calc_all['debit'].sum()
            grand_tax = tax_all['debit'].sum() + tax_all['credit'].sum()
            grand_net = grand_in - grand_out - grand_tax

            # Grand Total Row
            st.markdown("### 🏦 Grand Total (All Files Combined)")
            g1, g2, g3, g4 = st.columns(4)
            g1.markdown(f"""<div class="kpi-card" style="border-top-color:#059669;">
                <div class="kpi-label">Total Received (In)</div>
                <div class="kpi-value" style="color:#059669;">Rs. {grand_in:,.0f}</div>
            </div>""", unsafe_allow_html=True)
            g2.markdown(f"""<div class="kpi-card" style="border-top-color:#dc2626;">
                <div class="kpi-label">Total Paid Out</div>
                <div class="kpi-value" style="color:#dc2626;">Rs. {grand_out:,.0f}</div>
            </div>""", unsafe_allow_html=True)
            g3.markdown(f"""<div class="kpi-card" style="border-top-color:#d97706;">
                <div class="kpi-label">Tax / Deductions</div>
                <div class="kpi-value" style="color:#d97706;">Rs. {grand_tax:,.0f}</div>
            </div>""", unsafe_allow_html=True)
            g4.markdown(f"""<div class="kpi-card" style="border-top-color:#1a3a5c;">
                <div class="kpi-label">Net Balance</div>
                <div class="kpi-value" style="color:{'#059669' if grand_net >= 0 else '#dc2626'};">
                    Rs. {grand_net:,.0f}
                </div>
            </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Bank-wise breakdown
            st.markdown("### 🏛️ Bank-wise Breakdown")
            banks = df_analysis['bank'].dropna().unique()
            for bank in banks:
                b_df = df_analysis[df_analysis['bank'] == bank]
                b_calc = b_df[b_df['is_tax'] == False]
                b_in  = b_calc['credit'].sum()
                b_out = b_calc['debit'].sum()
                b_net = b_in - b_out
                st.markdown(f"""
                <div style="background:white; border-radius:8px; padding:16px 20px;
                            border:1px solid #e2e8f0; border-left:5px solid #1a3a5c; margin-bottom:10px;">
                    <div style="font-weight:700; color:#0d1b2a; font-size:1rem;">🏦 {bank} Bank</div>
                    <div style="display:flex; gap:40px; margin-top:10px; font-size:0.9rem;">
                        <div><span style="color:#64748b;">Received (In):</span>
                             <b style="color:#059669;"> Rs. {b_in:,.0f}</b></div>
                        <div><span style="color:#64748b;">Paid Out:</span>
                             <b style="color:#dc2626;"> Rs. {b_out:,.0f}</b></div>
                        <div><span style="color:#64748b;">Net:</span>
                             <b style="color:{'#059669' if b_net >= 0 else '#dc2626'};"> Rs. {b_net:,.0f}</b></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Per-file breakdown
            st.markdown("### 📁 File-wise Breakdown")
            files_list = df_analysis['source_file'].dropna().unique()
            summary_rows = []
            for f in files_list:
                f_df = df_analysis[df_analysis['source_file'] == f]
                f_calc = f_df[f_df['is_tax'] == False]
                f_tax  = f_df[f_df['is_tax'] == True]
                summary_rows.append({
                    'File': f,
                    'Bank': f_df['bank'].iloc[0] if not f_df.empty else 'N/A',
                    'Rows': len(f_df),
                    'Period': f"{f_df['transaction_date'].min()} → {f_df['transaction_date'].max()}",
                    'Received (In)': f_calc['credit'].sum(),
                    'Paid Out': f_calc['debit'].sum(),
                    'Tax': f_tax['debit'].sum() + f_tax['credit'].sum(),
                })

            summary_df = pd.DataFrame(summary_rows)
            st.dataframe(
                summary_df.style.format({
                    'Received (In)': 'Rs. {:,.0f}',
                    'Paid Out': 'Rs. {:,.0f}',
                    'Tax': 'Rs. {:,.0f}',
                }),
                use_container_width=True,
                hide_index=True
            )

    with tab1:
        col1, col2 = st.columns([1, 2], gap="large")

        with col1:
            st.markdown("<div class='section-title'>Upload Bank PDF</div>", unsafe_allow_html=True)
            bank_choice = st.selectbox("Select Bank Format", ["Meezan", "Alfalah", "Auto-Detect"])
            uploaded_files = st.file_uploader("Choose PDF Files", type="pdf", accept_multiple_files=True, label_visibility="collapsed")

            # Password field for encrypted PDFs
            st.markdown("""
            <div style="background:#fffbeb; border:1px solid #fcd34d; border-radius:8px;
                        padding:10px 14px; margin:10px 0; font-size:0.85rem; color:#78350f;">
                🔐 <b>Alfalah PDFs are password protected.</b><br>
                Password usually = your <b>CNIC without dashes</b> (e.g. <code>3520112345671</code>)
                or <b>Date of Birth</b> (e.g. <code>15051990</code>)
            </div>
            """, unsafe_allow_html=True)
            pdf_password = st.text_input("🔑 PDF Password (if encrypted)",
                                         placeholder="Enter CNIC / DOB without dashes...",
                                         type="password")

            run_btn = st.button("🚀 Process & Sync to Cloud")

            if run_btn:
                if not uploaded_files:
                    st.warning("Please select at least one PDF file.")
                else:
                    all_tx = []
                    locked_files = []
                    progress_bar = st.progress(0, text="Processing...")
                    for i, uf in enumerate(uploaded_files):
                        try:
                            tmp = f"temp_{uf.name}"
                            with open(tmp, "wb") as f:
                                f.write(uf.getbuffer())
                            txs = process_pdf(tmp, bank_choice, password=pdf_password)
                            if txs:
                                for t in txs:
                                    t['source_file'] = uf.name
                                all_tx.extend(txs)
                                st.success(f"✓ {uf.name}: {len(txs)} transactions extracted")
                            else:
                                st.warning(f"⚠️ {uf.name}: 0 transactions found — check bank format or PDF content.")
                            os.remove(tmp)
                        except Exception as e:
                            err_str = str(e).lower()
                            if os.path.exists(tmp):
                                os.remove(tmp)
                            if 'password' in err_str or 'incorrect' in err_str or 'encrypted' in err_str or 'pdfminer' in err_str:
                                locked_files.append(uf.name)
                                st.error(f"🔒 **{uf.name}** — Password-protected PDF!  "
                                         f"Sahi password enter karein aur dobara try karen.")
                            else:
                                st.error(f"✗ Error in {uf.name}: {e}")
                        progress_bar.progress((i + 1) / len(uploaded_files))

                    if locked_files:
                        st.markdown(f"""
                        <div style="background:#fef2f2; border:1px solid #fca5a5; border-radius:10px;
                                    padding:16px 20px; margin-top:12px;">
                            <div style="font-weight:800; color:#7f1d1d; font-size:1rem;">🔐 {len(locked_files)} file(s) unlock nahi hui</div>
                            <div style="color:#991b1b; font-size:0.88rem; margin-top:6px;">
                                Neeche password enter karein (CNIC bina dashes ke) aur dobara
                                <b>Process & Sync to Cloud</b> dabayein.
                            </div>
                            <ul style="color:#7f1d1d; font-size:0.83rem; margin-top:8px;">
                                {''.join(f'<li>{fn}</li>' for fn in locked_files)}
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)

                    if all_tx:
                        st.session_state.pending_tx = all_tx
                        st.rerun()

        with col2:
            st.markdown("<div class='section-title'>Import Summary</div>", unsafe_allow_html=True)
            if uploaded_files:
                st.markdown(f"**{len(uploaded_files)} file(s) selected** for processing.")
                st.markdown("""
                <div style="background:#f0fdf4; border:1px solid #86efac; border-radius:8px;
                            padding:12px 16px; font-size:0.85rem; color:#166534; margin-top:8px;">
                    <b>💡 Tips:</b><br>
                    • Alfalah password = <b>CNIC without dashes</b><br>
                    • Ya Date of Birth: <b>DDMMYYYY</b> format<br>
                    • Multiple files ek saath upload ho sakti hain
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Upload PDFs on the left and click Process to begin.")

    with tab3:  # GLOBAL ANALYSIS
        st.markdown("<div class='section-title'>📊 Complete Ledger Analysis — Saari Sheets</div>", unsafe_allow_html=True)
    # === VERIFICATION ===
    if st.session_state.pending_tx:
        total_found = len(st.session_state.pending_tx)
        # Big clear banner
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #065f46, #059669); color:white;
                    padding: 24px 30px; border-radius: 12px; margin: 20px 0;">
            <div style="font-size:1.4rem; font-weight:800;">📋 STEP 2 OF 2 — Name Verification</div>
            <div style="margin-top:8px; font-size:1rem; opacity:0.9;">
                ✅ <b>{total_found} transactions</b> extracted from PDF successfully!
            </div>
            <div style="margin-top:6px; font-size:0.9rem; opacity:0.8;">
                Neeche diye gaye names check karen. Sahi hon toh seedha
                <b>"SAVE & ADD TO LEDGER"</b> dabayein.
            </div>
        </div>
        """, unsafe_allow_html=True)

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
            st.markdown(f"""
            <div style="background:#fffbeb; border:1px solid #fcd34d; border-radius:8px;
                        padding:14px 18px; margin-bottom:16px;">
                <b style="color:#92400e;">⚠️ {len(new_profiles)} naye account(s) mile hain.</b>
                <span style="color:#78350f; font-size:0.9rem;">
                 PDF se jo naam nikla woh neeche dikh raha hai. Agar naam galat ho toh edit karen,
                 warna seedha Save dabayein.
                </span>
            </div>
            """, unsafe_allow_html=True)

            with st.form("verify_form"):
                updates = {}
                for i, p in enumerate(new_profiles):
                    col_l, col_r = st.columns([1, 2])
                    with col_l:
                        st.markdown(f"""
                        <div style="background:#f8fafc; padding:12px; border-radius:6px;
                                    border:1px solid #e2e8f0; margin-bottom:8px;">
                            <div style="color:#64748b; font-size:0.75rem; font-weight:700;">ACCOUNT #{i+1}</div>
                            <div style="color:#0f172a; font-family:monospace; font-size:0.85rem;
                                        word-break:break-all; margin-top:4px;">{p['id']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_r:
                        if p['status'] == 'New':
                            updates[p['id']] = st.text_input(
                                f"✏️ Name for Account #{i+1} (edit agar galat ho)",
                                value=p['extracted'], key=f"name_{p['id']}"
                            )
                        else:
                            st.warning(f"Conflict: Database mein **{p['existing']}** hai, PDF mein **{p['extracted']}** mila")
                            updates[p['id']] = st.radio(
                                f"Account #{i+1} ke liye kaunsa naam use karen?",
                                [p['existing'], p['extracted']], key=f"radio_{p['id']}"
                            )
                    st.divider()

                col_save, col_cancel = st.columns([2, 1])
                with col_save:
                    save_clicked = st.form_submit_button(
                        "💾 SAVE & ADD TO LEDGER",
                        use_container_width=True
                    )
                with col_cancel:
                    cancel_clicked = st.form_submit_button(
                        "❌ Cancel Import",
                        use_container_width=True
                    )

                if save_clicked:
                    for acc_id, name in updates.items():
                        upsert_profile(acc_id, name)
                    for t in st.session_state.pending_tx:
                        n = updates.get(t['account_number'], t['party_name'])
                        add_transaction(t['bank'], t['transaction_date'], t['description'],
                                        t['debit'], t['credit'], n, t['account_number'],
                                        t['is_tax'], t['source_file'])
                    st.session_state.pending_tx = None
                    st.success(f"✅ {total_found} transactions successfully added to ledger!")
                    st.rerun()
                if cancel_clicked:
                    st.session_state.pending_tx = None
                    st.rerun()
        else:
            # No new profiles - auto save with a confirm button
            st.markdown("""
            <div style="background:#f0fdf4; border:1px solid #86efac; border-radius:8px;
                        padding:14px 18px; margin-bottom:16px;">
                <b style="color:#166534;">✅ Saare accounts already registered hain.</b>
                <span style="color:#15803d; font-size:0.9rem;">
                 Koi naya account nahi mila. Seedha save kar sakte hain.
                </span>
            </div>
            """, unsafe_allow_html=True)

            col_save, col_cancel = st.columns([2, 1])
            with col_save:
                if st.button("💾 SAVE & ADD TO LEDGER", use_container_width=True):
                    for t in st.session_state.pending_tx:
                        prof = get_profile(t['account_number'])
                        n = prof['name'] if prof else t['party_name']
                        add_transaction(t['bank'], t['transaction_date'], t['description'],
                                        t['debit'], t['credit'], n, t['account_number'],
                                        t['is_tax'], t['source_file'])
                    st.session_state.pending_tx = None
                    st.success(f"✅ {total_found} transactions added successfully!")
                    st.rerun()
            with col_cancel:
                if st.button("❌ Cancel Import", use_container_width=True):
                    st.session_state.pending_tx = None
                    st.rerun()

elif view_mode == "Investor Portal":

    # Header
    st.markdown("""
    <div class="page-header">
        <h1>🏛️ Investor Statement Portal</h1>
        <p>Search your account to view verified transaction history</p>
    </div>
    """, unsafe_allow_html=True)

    # Grand Total Banner (always visible on front page)
    df_all = load_transactions()
    if not df_all.empty:
        # Smart Date Parsing & Sorting
        def parse_smart_date(d):
            if pd.isna(d) or d == '': return pd.NaT
            try: return pd.to_datetime(d, dayfirst=True)
            except: 
                try: return pd.to_datetime(d)
                except: return pd.NaT
        df_all['date_obj'] = df_all['transaction_date'].apply(parse_smart_date)
        df_all = df_all.sort_values('date_obj', ascending=False)
        all_calc = df_all[df_all['is_tax'] == False]
        all_tax  = df_all[df_all['is_tax'] == True]
        g_in  = all_calc['credit'].sum()
        g_out = all_calc['debit'].sum()
        g_tax = all_tax['debit'].sum() + all_tax['credit'].sum()
        g_net = g_in - g_out - g_tax
        total_files = df_all['source_file'].nunique()
        total_rows  = len(df_all)

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0a0f1e, #0d2a1a);
                    border-radius: 14px; padding: 20px 22px; margin-bottom: 24px;
                    border: 1px solid rgba(0,168,107,0.3);
                    box-shadow: 0 4px 20px rgba(0,0,0,0.2);">
            <div style="color:#00d68f; font-size:0.75rem; font-weight:700;
                        text-transform:uppercase; letter-spacing:1px; margin-bottom:14px;">
                📊 Ledger Summary — {total_files} Files | {total_rows:,} Transactions
            </div>
            <div class="ledger-grid">
                <div style="border-right:1px solid rgba(255,255,255,0.08); padding-right:12px;">
                    <div style="color:#6ee7b7; font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.8px;">💚 Total Credit</div>
                    <div style="color:#6ee7b7; font-size:1.4rem; font-weight:900; margin-top:6px; line-height:1.1;">
                        Rs. {g_in:,.0f}
                    </div>
                </div>
                <div style="border-right:1px solid rgba(255,255,255,0.08); padding-right:12px;">
                    <div style="color:#fca5a5; font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.8px;">🔴 Total Debit</div>
                    <div style="color:#fca5a5; font-size:1.4rem; font-weight:900; margin-top:6px; line-height:1.1;">
                        Rs. {g_out:,.0f}
                    </div>
                </div>
                <div style="border-right:1px solid rgba(255,255,255,0.08); padding-right:12px;">
                    <div style="color:#fde68a; font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.8px;">🟡 Tax / Deductions</div>
                    <div style="color:#fde68a; font-size:1.4rem; font-weight:900; margin-top:6px; line-height:1.1;">
                        Rs. {g_tax:,.0f}
                    </div>
                </div>
                <div>
                    <div style="color:#a5b4fc; font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.8px;">⚡ Net Balance</div>
                    <div style="color:{'#6ee7b7' if g_net >= 0 else '#fca5a5'}; font-size:1.4rem; font-weight:900; margin-top:6px; line-height:1.1;">
                        Rs. {g_net:,.0f}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


    st.markdown("<div class='section-title'>🔍 Filter & Search</div>", unsafe_allow_html=True)
    f_col1, f_col2, f_col3 = st.columns([1.5, 1, 1])
    with f_col1:
        search = st.text_input("", placeholder="🔍 Name, Account #, or keyword...", label_visibility="collapsed")
    with f_col2:
        bank_list = ["All Banks"] + sorted(df_all['bank'].unique().tolist()) if not df_all.empty else ["All Banks"]
        bank_filter = st.selectbox("Bank", bank_list, label_visibility="collapsed")
    with f_col3:
        if not df_all.empty and not df_all['date_obj'].isna().all():
            # Default to the full range found in the database
            full_min = df_all['date_obj'].min().date()
            full_max = df_all['date_obj'].max().date()
            date_range = st.date_input("Date Audit Range", [full_min, full_max], label_visibility="collapsed")
        else:
            date_range = None

    if search:
        df = df_all.copy()
        if df.empty:
            st.info("The ledger is currently empty. Please contact the Administrator.")
        else:
            # Apply Search
            mask = (
                df['party_name'].str.contains(search, case=False, na=False) |
                df['account_number'].str.contains(search, case=False, na=False) |
                df['description'].str.contains(search, case=False, na=False)
            )
            df = df[mask]
            
            # Apply Bank Filter
            if bank_filter != "All Banks":
                df = df[df['bank'] == bank_filter]
                
            # Apply Date Filter
            if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
                s_dt = pd.to_datetime(date_range[0])
                e_dt = pd.to_datetime(date_range[1])
                df = df[(df['date_obj'] >= s_dt) & (df['date_obj'] <= e_dt)]

            filtered = df

            if filtered.empty:
                st.warning("No records found. Please check your name or account number and try again.")
            else:
                # Group selection if multiple accounts match
                acc_list = filtered['account_number'].unique()
                if len(acc_list) > 1:
                    st.warning(f"Found {len(acc_list)} accounts for '{search}'.")
                    selected_acc = st.radio("Choose Account to Audit", ["Combined View"] + list(acc_list), horizontal=True)
                    if selected_acc != "Combined View":
                        filtered = filtered[filtered['account_number'] == selected_acc]

                calc = filtered[filtered['is_tax'] == False]
                tax_rows = filtered[filtered['is_tax'] == True]
                in_v = calc['credit'].sum()
                out_v = calc['debit'].sum()
                tax_v = tax_rows['debit'].sum() + tax_rows['credit'].sum()
                net = in_v - out_v - tax_v

                st.markdown("<div class='section-title'>Account Summary</div>", unsafe_allow_html=True)
                c1, c2, c3, c4 = st.columns(4)
                c1.markdown(f"""<div class="kpi-card" style="border-top-color:#059669;">
                    <div class="kpi-label">💚 Total Credit (In)</div>
                    <div class="kpi-value" style="color:#059669;">Rs. {in_v:,.0f}</div>
                </div>""", unsafe_allow_html=True)
                c2.markdown(f"""<div class="kpi-card" style="border-top-color:#dc2626;">
                    <div class="kpi-label">🔴 Total Debit (Out)</div>
                    <div class="kpi-value" style="color:#dc2626;">Rs. {out_v:,.0f}</div>
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
