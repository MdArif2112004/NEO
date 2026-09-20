import requests, os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('FOURSQUARE_API_KEY')
r = requests.get(
    'https://api.foursquare.com/v3/places/search',
    headers={'Authorization': key, 'Accept': 'application/json'},
    params={'query': 'wedding venue', 'near': 'Los Angeles CA', 'limit': 5}
)
print(r.status_code)
print(r.text[:300])