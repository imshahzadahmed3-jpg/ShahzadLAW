import pdfplumber
import re
import pandas as pd

def clean_amount(val):
    if not val:
        return 0.0
    val = str(val).replace(',', '').strip()
    try:
        return float(val)
    except:
        return 0.0

def is_tax(desc):
    desc_lower = desc.lower()
    if 'tax' in desc_lower or 'fed' in desc_lower or 'charges' in desc_lower or 'fee' in desc_lower:
        return True
    return False

def parse_meezan(file_path, password=""):
    transactions = []
    open_kwargs = {"password": password} if password else {}
    with pdfplumber.open(file_path, **open_kwargs) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if len(row) >= 4:
                        date = str(row[0]).strip()
                        desc = str(row[1]).strip()
                        debit = clean_amount(row[2])
                        credit = clean_amount(row[3])
                        
                        # basic date validation dd/mm/yyyy
                        if re.match(r'\d{2}/\d{2}/\d{4}', date):
                            acc_num = extract_account_number(desc)
                            transactions.append({
                                'bank': 'Meezan',
                                'transaction_date': date,
                                'description': desc,
                                'debit': debit,
                                'credit': credit,
                                'party_name': extract_party_name(desc, acc_num),
                                'account_number': acc_num,
                                'is_tax': is_tax(desc)
                            })
    return transactions

MONTH_MAP = {
    'jan':'01','feb':'02','mar':'03','apr':'04','may':'05','jun':'06',
    'jul':'07','aug':'08','sep':'09','oct':'10','nov':'11','dec':'12'
}

def normalize_alfalah_date(raw_date):
    """Convert '01 Nov 2024' → '01-11-2024'"""
    parts = raw_date.strip().split()
    if len(parts) == 3:
        day, mon, yr = parts
        mon_num = MONTH_MAP.get(mon.lower()[:3], '01')
        return f"{day.zfill(2)}-{mon_num}-{yr}"
    return raw_date

def parse_alfalah(file_path, password=""):
    transactions = []
    prev_balance = None

    open_kwargs = {"password": password} if password else {}
    with pdfplumber.open(file_path, **open_kwargs) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.split('\n')
            for line in lines:
                line = line.strip()

                # Opening Balance line
                ob_match = re.search(r'Opening Balance\s+([\d,]+\.?\d*)', line, re.IGNORECASE)
                if ob_match:
                    prev_balance = clean_amount(ob_match.group(1))
                    continue

                # Transaction line: "DD Mon YYYY  Description [Cheq#]  Amount  Balance"
                # e.g. "01 Nov 2024 Funds Transfer RAAST 77,000.00 82,472.77"
                tx_match = re.match(
                    r'^(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})\s+(.+?)\s+([\d,]+\.\d{2})\s+([-\d,]+\.\d{2})\s*$',
                    line
                )
                if tx_match:
                    raw_date = tx_match.group(1)
                    desc     = tx_match.group(2).strip()
                    amount   = clean_amount(tx_match.group(3))
                    balance  = clean_amount(tx_match.group(4))
                    date_str = normalize_alfalah_date(raw_date)

                    debit = 0.0
                    credit = 0.0

                    if prev_balance is not None:
                        diff = round(balance - prev_balance, 2)
                        if abs(diff - amount) < 1.0:
                            credit = amount   # balance went UP → credit
                        elif abs(diff + amount) < 1.0:
                            debit = amount    # balance went DOWN → debit
                        else:
                            # fallback: use description keywords
                            desc_lower = desc.lower()
                            if any(k in desc_lower for k in ['charges','tax','fee','repayment','withdrawal','purchase','debit']):
                                debit = amount
                            else:
                                credit = amount
                    else:
                        desc_lower = desc.lower()
                        if any(k in desc_lower for k in ['charges','tax','fee','repayment','withdrawal','purchase','debit']):
                            debit = amount
                        else:
                            credit = amount

                    prev_balance = balance
                    acc_num = extract_account_number(desc)
                    transactions.append({
                        'bank': 'Alfalah',
                        'transaction_date': date_str,
                        'description': desc,
                        'debit': debit,
                        'credit': credit,
                        'party_name': extract_party_name(desc, acc_num),
                        'account_number': acc_num,
                        'is_tax': is_tax(desc)
                    })

    return transactions


def extract_account_number(desc):
    # Try to find IBAN
    match = re.search(r'PK\d{2}\s*[A-Z]{4}\s*[\d\s]+', desc, re.IGNORECASE)
    if match:
        return match.group(0).replace('\n', '').replace(' ', '')
    
    # Try to find a standard long account number (10+ digits)
    match = re.search(r'\b\d{10,20}\b', desc.replace(' ', ''))
    if match:
        return match.group(0)
    
    # Try finding XXXX1234 format
    match = re.search(r'[X\*]{4,}\d{4,}', desc, re.IGNORECASE)
    if match:
        return match.group(0)
        
    return ''

def finalize_alfalah_tx(tx, transactions_list, prev_balance):
    desc = tx['desc']
    amt1 = tx['amt1']
    bal = tx['amt2']
    
    debit = 0.0
    credit = 0.0
    
    if prev_balance is not None:
        diff = round(bal - prev_balance, 2)
        if abs(diff - amt1) < 1.0:
            credit = amt1
        elif abs(diff + amt1) < 1.0:
            debit = amt1
        else:
            # Fallback heuristic
            if 'from' in desc.lower():
                credit = amt1
            elif 'to' in desc.lower() or 'tax' in desc.lower() or 'charge' in desc.lower():
                debit = amt1
            else:
                debit = amt1
    else:
        # First transaction heuristic
        if 'from' in desc.lower():
            credit = amt1
        elif 'to' in desc.lower() or 'tax' in desc.lower() or 'charge' in desc.lower():
            debit = amt1
        else:
            debit = amt1
        
    acc_num = extract_account_number(desc)
    transactions_list.append({
        'bank': 'Alfalah',
        'transaction_date': tx['date'],
        'description': desc.replace('\n', ' '),
        'debit': debit,
        'credit': credit,
        'party_name': extract_party_name(desc, acc_num),
        'account_number': acc_num,
        'is_tax': is_tax(desc)
    })
    
    return bal

def extract_party_name(desc, acc_num=""):
    desc_upper = desc.upper().replace('\n', ' ')
    acc_num = acc_num.replace('X', '').replace('*', '').strip()
    
    # Check specific IBANs to force the exact name
    if 'PK37UNIL0109000322850752' in desc_upper or '0752' in acc_num:
        return 'Owais Traders'
    if 'PK37UNIL0109000291455635' in desc_upper or '5635' in acc_num:
        return 'Muhammad Owais Qarni'
    if 'PK33NAYA1234503106944124' in desc_upper or '4124' in acc_num:
        return 'Muhammad Owais Qarni'
        
    # Specific known cases
    if 'SHAHZAD' in desc_upper or 'SHA HZAD' in desc_upper:
        return 'Shahzad Ahmed'
    if 'OWAIS TRADERS' in desc_upper or 'OWA IS TRADERS' in desc_upper:
        return 'Owais Traders'
    if 'MUHAMMAD OWAIS QARNI' in desc_upper or 'MUH AMMAD OWAIS QARNI' in desc_upper:
        return 'Muhammad Owais Qarni'
    
    # Try to find words after "from" or "to"
    match = re.search(r'(from|to)\s+([A-Z\s\.\-]+)', desc, re.IGNORECASE)
    if match:
        name = match.group(2).strip()
        # Clean up any leftover numbers or reference tags
        name = re.sub(r'[0-9\[\]<>\n]', '', name).strip()
        if len(name) > 3 and not name.startswith('FT-RAAST') and not name.startswith('STAN') and not name.startswith('AC-'):
            return name.title()
            
    # Try looking at the second line of the description (often the party name in Alfalah)
    lines = desc.split('\n')
    if len(lines) > 1:
        potential_name = lines[1].strip()
        # If it's mostly letters and spaces, it's likely a name
        if re.match(r'^[A-Z\s\.\-]+$', potential_name) and len(potential_name) > 3:
            return potential_name.title()
            
    return ''

def process_pdf(file_path, bank_choice, password=""):
    pwd = password.strip() if password else ""
    if bank_choice.lower() == 'meezan':
        return parse_meezan(file_path, password=pwd)
    elif bank_choice.lower() == 'alfalah':
        return parse_alfalah(file_path, password=pwd)
    else:
        # try both
        res = parse_meezan(file_path, password=pwd)
        if not res:
            res = parse_alfalah(file_path, password=pwd)
        return res
