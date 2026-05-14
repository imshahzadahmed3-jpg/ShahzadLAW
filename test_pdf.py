import utils.pdf_parser as pp

print("--- Testing Alfalah ---")
txs = pp.parse_alfalah("bank alflah.pdf")
print(f"Found {len(txs)} transactions.")
for i, tx in enumerate(txs[:10]):
    print(f"Tx {i+1}:")
    print(f"  Date: {tx['transaction_date']}")
    print(f"  Party: {tx['party_name']}")
    print(f"  Desc: {tx['description'][:100]}...")
    print(f"  Debit: {tx['debit']}")
    print(f"  Credit: {tx['credit']}")
    print(f"  Account: {tx['account_number']}")
    print("-" * 20)
