import csv
rows = list(csv.DictReader(open('ca_pricing_delivery.csv', encoding='utf-8')))
yes  = [r for r in rows if r['Pricing Found']=='Yes']
with open('thelma_ca_delivery.csv','w',newline='',encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(yes)
print(f'Saved {len(yes)} rows to thelma_ca_delivery.csv')
