import csv
from typing import List, Dict, Optional

class Airports:
    def __init__(self):
        self.airports = []
        self.city_to_iata = {}
        self.country_to_iata = {}

    #######################
    # Method to load airports from a CSV file
    #######################    
    def load_airports(self, csv_file: str):
        """Load airports name by IATAS"""
        try:
            with open(csv_file, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)

                for row in reader:
                    if len(row) >= 6:
                        airport_data = {
                            'id': row[0],
                            'name': row[1],
                            'city': row[2],
                            'country': row[3],
                            'iata': row[4] if row[4] != '\\N' else None,
                            'icao': row[5] if row[5] != '\\N' else None
                        }

                        if airport_data['iata']:
                            self.airports.append(airport_data)

                            city_key = airport_data['city'].lower()
                            if city_key not in self.city_to_iata:
                                self.city_to_iata[city_key] = []
                            self.city_to_iata[city_key].append(airport_data)
                            country_key = airport_data['country'].lower()
                            if country_key not in self.country_to_iata:
                                self.country_to_iata[country_key] = []
                            self.country_to_iata[country_key].append(airport_data)
                print(f"Loaded {len(self.airports)} airports from {csv_file}")
        except FileNotFoundError:
            print(f"Error: The file {csv_file} was not found.")
        except Exception as e:
            print(f"Error loading airports: {e}")
        
    #######################
    # Methods to find IATA codes by city name
    #######################
    def find_iata_by_city(self, destination: str) -> List[Dict]:
        """Find IATA codes by city name"""
        parts = [part.strip() for part in destination.split(',')]
        city_key = parts[0].lower()
        country_key = parts[1].lower()

        return self.city_to_iata.get(city_key, []), country_key
    
    #######################
    # Method to get primary IATA code for a city
    #######################
    def get_primary_iata(self, cityname: str) -> Optional[str]:
        """Get primary IATA code for a city"""
        airports = self.find_iata_by_city(cityname)
        return airports[0]['iata'] if airports else None

    #######################
    # Method to search for cities containing a query string
    #######################
    def search_cities(self, query: str) -> List[Dict]:
        """Search for cities containing the query string"""
        search_term = query.lower()   
        results = []

        parts = [part.strip() for part in search_term.split(',')]
        city_key = parts[0].lower()
        country_key = parts[1].lower() if len(parts) > 1 else None

        for city, airports in self.city_to_iata.items():
            if city_key in city:
                for airport in airports:
                        if not country_key or country_key in airport['country'].lower():
                            results.append(airport)

        return results
    

if __name__ == "__main__":
    # Initialize and load data from local file
    finder = Airports()
    finder.load_airports("../data/airports.dat")  # Specify your file path here

    # Test cities
    test_cities = ["Rome", "Berlin", "Stuttgart", "Tashkent", "New York", "London"]

    print("\n=== City to IATA Code Mapping ===")
    for city in test_cities:
        airports = finder.find_iata_by_city(city)

        if airports:
            print(f"\n{city}:")
            for airport in airports:
                print(f"  {airport['iata']} - {airport['name']} ({airport['country']})")
        else:
            print(f"\n{city}: No airports found")

    print("\n=== Primary IATA Codes ===")
    for city in test_cities:
        iata = finder.get_primary_iata(city)
        print(f"{city}: {iata if iata else 'Not found'}")

    print("\n=== Search Example ===")
    # Search for cities containing "york"
    results = finder.search_cities("york")
    for airport in results[:5]:  # Show first 5 results
        print(f"{airport['city']} ({airport['country']}) - {airport['iata']}")