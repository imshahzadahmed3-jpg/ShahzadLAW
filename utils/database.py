import sqlite3
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_NAME = "transactions.db"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase if configured
supabase = None
if SUPABASE_URL and SUPABASE_KEY and "yahan_apni_key" not in SUPABASE_KEY:
    try:
        from supabase import create_client, Client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except ImportError:
        print("Supabase library not found. Run 'pip install supabase'")

def init_db():
    # Local fallback
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank TEXT,
            transaction_date TEXT,
            description TEXT,
            debit REAL,
            credit REAL,
            party_name TEXT,
            account_number TEXT,
            is_tax BOOLEAN,
            source_file TEXT,
            added_at TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            account_number TEXT PRIMARY KEY,
            name TEXT,
            category TEXT,
            last_seen TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_transaction(bank, date, desc, debit, credit, party_name="", account_number="", is_tax=False, source_file="Manual"):
    added_at = datetime.now().isoformat()
    
    # 1. Save to Supabase (Cloud)
    if supabase:
        try:
            # Check for duplicate
            check = supabase.table("transactions").select("id").match({
                "bank": bank, "transaction_date": date, "description": desc, "debit": debit, "credit": credit
            }).execute()
            
            if not check.data:
                supabase.table("transactions").insert({
                    "bank": bank, "transaction_date": date, "description": desc,
                    "debit": debit, "credit": credit, "party_name": party_name,
                    "account_number": account_number, "is_tax": is_tax, "source_file": source_file
                }).execute()
        except Exception as e:
            print(f"Supabase Error: {e}")

    # 2. Save to SQLite (Local Backup)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 1 FROM transactions 
        WHERE bank=? AND transaction_date=? AND description=? AND debit=? AND credit=? AND source_file=?
    """, (bank, date, desc, debit, credit, source_file))
    
    if cursor.fetchone() is None:
        cursor.execute("""
            INSERT INTO transactions (bank, transaction_date, description, debit, credit, party_name, account_number, is_tax, source_file, added_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (bank, date, desc, debit, credit, party_name, account_number, is_tax, source_file, added_at))
        conn.commit()
    conn.close()

def load_transactions():
    if supabase:
        try:
            res = supabase.table("transactions").select("*").order("added_at", desc=True).execute()
            if res.data:
                return pd.DataFrame(res.data)
        except Exception as e:
            print(f"Supabase Load Error: {e}")
            
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY added_at DESC", conn)
    conn.close()
    return df

def get_uploaded_files():
    if supabase:
        try:
            res = supabase.table("transactions").select("source_file").execute()
            if res.data:
                files = list(set([r['source_file'] for r in res.data if r['source_file'] != 'Manual']))
                return files
        except: pass

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT source_file FROM transactions WHERE source_file != 'Manual'")
    files = [row[0] for row in cursor.fetchall()]
    conn.close()
    return files

def delete_transactions_by_file(filename):
    if supabase:
        try:
            supabase.table("transactions").delete().match({"source_file": filename}).execute()
        except: pass

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE source_file=?", (filename,))
    conn.commit()
    conn.close()

def clear_db():
    if supabase:
        try:
            supabase.table("transactions").delete().neq("id", 0).execute()
        except: pass

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions")
    conn.commit()
    conn.close()

def get_profile(account_number):
    if not account_number: return None
    
    if supabase:
        try:
            res = supabase.table("profiles").select("*").eq("account_number", account_number).execute()
            if res.data:
                return {"name": res.data[0]['name'], "category": res.data[0]['category']}
        except: pass

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, category FROM profiles WHERE account_number=?", (account_number,))
    res = cursor.fetchone()
    conn.close()
    return {"name": res[0], "category": res[1]} if res else None

def upsert_profile(account_number, name, category="General"):
    if not account_number: return
    last_seen = datetime.now().isoformat()

    if supabase:
        try:
            supabase.table("profiles").upsert({
                "account_number": account_number, "name": name, 
                "category": category, "last_seen": last_seen
            }).execute()
        except Exception as e:
            print(f"Profile Sync Error: {e}")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO profiles (account_number, name, category, last_seen)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(account_number) DO UPDATE SET
        name=excluded.name, category=excluded.category, last_seen=excluded.last_seen
    """, (account_number, name, category, last_seen))
    conn.commit()
    conn.close()
