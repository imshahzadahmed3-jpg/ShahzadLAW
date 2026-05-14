import utils.pdf_parser as pp
import pandas as pd

ibans = [
    'PK37UNIL0109000322850752',
    'PK37UNIL0109000291455635',
    'PK33NAYA1234503106944124'
]

alfalah_tx = pp.parse_alfalah("bank alflah.pdf")
meezan_tx = pp.parse_meezan("meezan.pdf")

all_tx = alfalah_tx + meezan_tx

filtered_tx = []
for tx in all_tx:
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
        
    if match and tx['credit'] > 0:
        filtered_tx.append(tx)

df = pd.DataFrame(filtered_tx)
df = df.sort_values(by=['transaction_date'])

print(df[['transaction_date', 'bank', 'credit', 'description']].to_string())
print(f"\nTotal Incoming: {df['credit'].sum()}")
