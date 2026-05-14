import utils.pdf_parser as pp

ibans = [
    'PK37UNIL0109000322850752',
    'PK37UNIL0109000291455635',
    'PK33NAYA1234503106944124'
]

print("Parsing Alfalah...")
try:
    alfalah_tx = pp.parse_alfalah("bank alflah.pdf")
except Exception as e:
    alfalah_tx = []
    print("Alfalah parse error:", e)

print("Parsing Meezan...")
try:
    meezan_tx = pp.parse_meezan("meezan.pdf")
except Exception as e:
    meezan_tx = []
    print("Meezan parse error:", e)

all_tx = alfalah_tx + meezan_tx

filtered_tx = []
for tx in all_tx:
    # Check by exact name or IBAN match in description
    pname = tx.get('party_name', '').upper()
    acc = tx.get('account_number', '').replace(' ', '')
    desc = tx.get('description', '').upper()
    
    match = False
    if pname in ['OWAIS TRADERS', 'MUHAMMAD OWAIS QARNI']:
        match = True
    elif any(iban in desc.replace(' ', '') for iban in ibans):
        match = True
    elif any(iban in acc for iban in ibans):
        match = True
        
    if match:
        filtered_tx.append(tx)

total_sent = sum(tx['debit'] for tx in filtered_tx if not tx['is_tax'])
total_received = sum(tx['credit'] for tx in filtered_tx if not tx['is_tax'])

print(f"\n--- OWAIS TRANSACTIONS ---")
print(f"Total Transactions Found: {len(filtered_tx)}")
print(f"Total Money Sent to Owais (Debit): Rs. {total_sent:,.2f}")
print(f"Total Money Received from Owais (Credit): Rs. {total_received:,.2f}")
print("--------------------------\n")

# For debugging, print first few to confirm
for tx in filtered_tx[:5]:
    print(f"{tx['transaction_date']} | {tx['bank']} | {tx['party_name']} | {tx['debit']} | {tx['credit']}")
