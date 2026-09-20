import csv
rows = list(csv.DictReader(open('ca_pricing_delivery.csv', encoding='utf-8')))
yes  = [r for r in rows if r['Pricing Found']=='Yes']
pdfs = [r for r in yes if r['PDF File']]
print(f'Total processed: {len(rows)}')
print(f'Pricing found:   {len(yes)}')
print(f'With PDF:        {len(pdfs)}')
