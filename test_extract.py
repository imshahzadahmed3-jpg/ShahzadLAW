import re

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
    if 'OWAIS' in desc_upper or 'AWAIS' in desc_upper:
        if 'QARNI' in desc_upper:
            return 'Muhammad Owais Qarni'
        return 'Owais Traders'
    
    return ""

# Test
desc = "IBFT to XXXX0752"
acc = extract_account_number(desc)
name = extract_party_name(desc, acc)
print(f"Desc: {desc}")
print(f"Acc: {acc}")
print(f"Name: {name}")

desc = "Money Transferred to OWAIS TRADERS-XXXX0752"
acc = extract_account_number(desc)
name = extract_party_name(desc, acc)
print(f"Desc: {desc}")
print(f"Acc: {acc}")
print(f"Name: {name}")

