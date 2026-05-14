import utils.database as db
import utils.pdf_parser as pp

# 1. Clear existing DB
db.clear_db()

# 2. Parse Meezan
print("Parsing Meezan...")
meezan_tx = pp.parse_meezan("meezan.pdf")
for t in meezan_tx:
    db.add_transaction(t['bank'], t['transaction_date'], t['description'], 
                       t['debit'], t['credit'], t['party_name'], t['account_number'], t['is_tax'])

# 3. Parse Alfalah
print("Parsing Alfalah...")
alfalah_tx = pp.parse_alfalah("bank alflah.pdf")
for t in alfalah_tx:
    db.add_transaction(t['bank'], t['transaction_date'], t['description'], 
                       t['debit'], t['credit'], t['party_name'], t['account_number'], t['is_tax'])

print("Successfully loaded both PDFs into the database!")
