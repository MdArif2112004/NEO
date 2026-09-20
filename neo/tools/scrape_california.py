import csv
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY     = os.getenv("FOURSQUARE_API_KEY")
OUTPUT_FILE = "california_venues.csv"

HEADERS = {
    "Authorization": API_KEY,
    "Accept": "application/json"
}

CA_CITIES = [
    "Los Angeles CA", "San Francisco CA", "San Diego CA",
    "Sacramento CA", "San Jose CA", "Oakland CA",
    "Santa Barbara CA", "Napa CA", "Palm Springs CA",
    "Monterey CA", "Malibu CA", "Pasadena CA",
    "Temecula CA", "Carmel CA", "Santa Cruz CA"
]

def search_city(city):
    results = []
    for offset in range(0, 150, 50):
        params = {
            "query":      "wedding venue",
            "near":       city,
            "limit":      50,
            "offset":     offset,
            "categories": "13065"  # Event Space category
        }
        r = requests.get(
            "https://api.foursquare.com/v3/places/search",
            headers=HEADERS, params=params, timeout=10
        )
        if r.status_code != 200:
            print(f"  Error {r.status_code} for {city}")
            break
        data = r.json().get("results", [])
        if not data:
            break
        results.extend(data)
        time.sleep(1)
    return results

def main():
    seen = set()

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Venue Name", "Website URL", "City", "Address"])

        for city in CA_CITIES:
            print(f"\n--- {city} ---")
            businesses = search_city(city)

            for b in businesses:
                name    = b.get("name", "").strip()
                loc     = b.get("location", {})
                address = loc.get("address", "")
                city_r  = loc.get("locality", city.split()[0])
                website = b.get("website", "")

                # fallback: build Foursquare profile URL if no website
                if not website:
                    fsq_id  = b.get("fsq_id", "")
                    website = f"https://foursquare.com/v/{fsq_id}" if fsq_id else ""

                if name and name not in seen:
                    seen.add(name)
                    writer.writerow([name, website, city_r, address])
                    print(f"  ✓ {name} | {city_r}")

    print(f"\nDone. {len(seen)} venues saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()