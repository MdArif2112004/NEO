import requests
response = requests.get('https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD')
with open('experiments/btc_price.txt', 'w') as f:
    f.write(str(response.json()['USD']))