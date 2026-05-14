import sqlite3
import pandas as pd

conn = sqlite3.connect('transactions.db')
query = """
SELECT * FROM transactions
WHERE party_name IN ('Owais Traders', 'Muhammad Owais Qarni')
   OR account_number IN ('PK37UNIL0109000322850752', 'PK37UNIL0109000291455635', 'PK33NAYA1234503106944124')
"""
df = pd.read_sql_query(query, conn)
print(df)
if not df.empty:
    print(f"Total Credit (IN): {df['credit'].sum()}")
    print(f"Total Debit (OUT): {df['debit'].sum()}")
else:
    print("No matching transactions found in DB.")
conn.close()
