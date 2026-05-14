import os
import sqlite3
from utils.pdf_parser import parse_alfalah
from utils.database import add_transaction

def import_error_sheets():
    folder = 'sheet error'
    password = '715'
    
    if not os.path.exists(folder):
        print(f"Folder '{folder}' not found.")
        return

    files = [f for f in os.listdir(folder) if f.endswith('.pdf')]
    print(f"Found {len(files)} PDFs in '{folder}'")

    total_added = 0
    for filename in sorted(files):
        path = os.path.join(folder, filename)
        print(f"Processing {filename}...")
        try:
            txs = parse_alfalah(path, password=password)
            for t in txs:
                # add_transaction handles local and supabase sync
                add_transaction(
                    bank=t['bank'],
                    date=t['transaction_date'],
                    desc=t['description'],
                    debit=t['debit'],
                    credit=t['credit'],
                    party_name=t['party_name'],
                    account_number=t['account_number'],
                    is_tax=t['is_tax'],
                    source_file=filename
                )
            total_added += len(txs)
            print(f"  Successfully added {len(txs)} transactions.")
        except Exception as e:
            print(f"  Error processing {filename}: {e}")

    print(f"\nDone! Total transactions imported: {total_added}")

if __name__ == "__main__":
    import_error_sheets()
