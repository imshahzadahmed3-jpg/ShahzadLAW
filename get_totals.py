import utils.pdf_parser as pp
ibans = ['PK37UNIL0109000322850752', 'PK37UNIL0109000291455635', 'PK33NAYA1234503106944124']
alfalah_tx = pp.parse_alfalah("bank alflah.pdf")
meezan_tx = pp.parse_meezan("meezan.pdf")
filtered_tx = []
for tx in alfalah_tx + meezan_tx:
    pname = tx.get('party_name', '').upper()
    if pname in ['OWAIS TRADERS', 'MUHAMMAD OWAIS QARNI']:
        filtered_tx.append(tx)
        
tin = sum(t['credit'] for t in filtered_tx)
tout = sum(t['debit'] for t in filtered_tx)
print(f"Total IN: {tin}")
print(f"Total OUT: {tout}")
