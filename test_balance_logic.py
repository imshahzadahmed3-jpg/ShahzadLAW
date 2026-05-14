import pdfplumber
import re

def clean_amount(val):
    if not val:
        return 0.0
    val = str(val).replace(',', '').strip()
    try:
        return float(val)
    except:
        return 0.0

def test_balance(file_path):
    prev_balance = None
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue
            lines = text.split('\n')
            for line in lines:
                match = re.match(r'^(\d{2}-\d{2}-\d{4})\s+(.+?)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)$', line.strip())
                if match:
                    date = match.group(1)
                    desc = match.group(2)
                    amt = clean_amount(match.group(3))
                    bal = clean_amount(match.group(4))
                    
                    inferred_type = "UNKNOWN"
                    if prev_balance is not None:
                        diff = round(bal - prev_balance, 2)
                        if abs(diff - amt) < 0.1:
                            inferred_type = "CREDIT (Incoming)"
                        elif abs(diff + amt) < 0.1:
                            inferred_type = "DEBIT (Outgoing)"
                        else:
                            inferred_type = f"MISMATCH (diff: {diff}, amt: {amt})"
                    else:
                        inferred_type = "FIRST_TX (Need manual heuristic)"
                        
                    print(f"{date} | {amt} | Bal: {bal} | {inferred_type} | {desc[:30]}")
                    prev_balance = bal
            if i > 2:
                break

if __name__ == "__main__":
    test_balance("bank alflah.pdf")
