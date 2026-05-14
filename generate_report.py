import utils.pdf_parser as pp
import pandas as pd
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

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
        
    if match:
        filtered_tx.append(tx)

total_in = sum(t['credit'] for t in filtered_tx)
total_out = sum(t['debit'] for t in filtered_tx)

doc = SimpleDocTemplate("Owais_Final_Report.pdf", pagesize=landscape(letter),
                        rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
elements = []
styles = getSampleStyleSheet()

# Custom styles
title_style = ParagraphStyle(name='TitleStyle', parent=styles['Heading1'], alignment=1, spaceAfter=20, textColor=colors.HexColor('#1E3A8A'))
header_style = ParagraphStyle(name='HeaderStyle', parent=styles['Normal'], alignment=1, fontName='Helvetica-Bold', textColor=colors.whitesmoke)
cell_style = ParagraphStyle(name='CellStyle', parent=styles['Normal'], alignment=1, fontSize=9, leading=11)
desc_style = ParagraphStyle(name='DescStyle', parent=styles['Normal'], fontSize=8, leading=10)

elements.append(Paragraph("Final Bank Reconciliation Report: Owais", title_style))

summary_data = [
    [Paragraph("Grand Total Incoming (Credit)", header_style), Paragraph("Grand Total Outgoing (Debit)", header_style)],
    [f"Rs. {total_in:,.2f}", f"Rs. {total_out:,.2f}"]
]
t = Table(summary_data, colWidths=[200, 200])
t.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563EB')),
    ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
    ('FONTSIZE', (0,1), (-1,1), 14),
    ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ('TOPPADDING', (0,0), (-1,-1), 10),
    ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#93C5FD'))
]))
elements.append(t)
elements.append(Spacer(1, 30))

elements.append(Paragraph("Detailed Transactions", styles['Heading2']))

tx_data = [[
    Paragraph("Date", header_style), 
    Paragraph("Bank", header_style), 
    Paragraph("Incoming (Credit)", header_style), 
    Paragraph("Outgoing (Debit)", header_style), 
    Paragraph("Description", header_style)
]]

from datetime import datetime
def parse_date(d_str):
    d_str = d_str.replace('/', '-')
    try:
        return datetime.strptime(d_str, '%d-%m-%Y')
    except Exception:
        return datetime.min

for i, tx in enumerate(sorted(filtered_tx, key=lambda x: parse_date(x['transaction_date']))):
    in_val = f"{tx['credit']:,.2f}" if tx['credit'] > 0 else "-"
    out_val = f"{tx['debit']:,.2f}" if tx['debit'] > 0 else "-"
    
    tx_data.append([
        Paragraph(tx['transaction_date'], cell_style), 
        Paragraph(tx['bank'], cell_style), 
        Paragraph(in_val, cell_style),
        Paragraph(out_val, cell_style),
        Paragraph(tx['description'], desc_style)
    ])

# Adjust column widths to fit landscape nicely (Total ~730 pts)
t_tx = Table(tx_data, colWidths=[70, 60, 100, 100, 400])

# Alternating row colors
ts = [
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ('TOPPADDING', (0,0), (-1,-1), 8),
    ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey)
]

for i in range(1, len(tx_data)):
    if i % 2 == 0:
        ts.append(('BACKGROUND', (0,i), (-1,i), colors.HexColor('#F8FAFC')))
    else:
        ts.append(('BACKGROUND', (0,i), (-1,i), colors.white))

t_tx.setStyle(TableStyle(ts))

elements.append(t_tx)
doc.build(elements)
print("PDF Generated!")
