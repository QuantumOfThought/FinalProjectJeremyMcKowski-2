import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class WeatherFetcher:
    """
    Fetches current weather data from AccuWeather API
    """

    def __init__(self):
        """Initialize with API key and location from environment variables"""
        self.api_key = os.getenv('ACCUWEATHER_API_KEY')
        self.city = os.getenv('WEATHER_CITY', 'Hays')
        self.state = os.getenv('WEATHER_STATE', 'KS')
        self.location_key = None

    def get_location_key(self):
        """
        Get the AccuWeather location key for the specified city
        Returns: location key string or None if error
        """
        if self.location_key:
            return self.location_key

        try:
            # AccuWeather Locations API endpoint
            url = "http://dataservice.accuweather.com/locations/v1/cities/US/search"
            params = {
                'apikey': self.api_key,
                'q': f"{self.city}, {self.state}"
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data and len(data) > 0:
                self.location_key = data[0]['Key']
                return self.location_key
            else:
                return None

        except Exception as e:
            print(f"Error fetching location key: {e}")
            return None

    def get_current_weather(self):
        """
        Fetch current weather conditions
        Returns: Dictionary with weather data or None if error
        """
        location_key = self.get_location_key()

        if not location_key:
            return None

        try:
            # AccuWeather Current Conditions API endpoint
            url = f"http://dataservice.accuweather.com/currentconditions/v1/{location_key}"
            params = {
                'apikey': self.api_key,
                'details': 'true'
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data and len(data) > 0:
                conditions = data[0]

                # Extract relevant weather information
                weather_data = {
                    'temperature': conditions['Temperature']['Imperial']['Value'],
                    'unit': conditions['Temperature']['Imperial']['Unit'],
                    'weather_text': conditions['WeatherText'],
                    'humidity': conditions.get('RelativeHumidity', 'N/A'),
                    'wind_speed': conditions['Wind']['Speed']['Imperial']['Value'],
                    'wind_unit': conditions['Wind']['Speed']['Imperial']['Unit'],
                    'wind_direction': conditions['Wind']['Direction']['English'],
                    'city': f"{self.city}, {self.state}",
                    'icon': conditions.get('WeatherIcon', 1)
                }

                return weather_data
            else:
                return None

        except Exception as e:
            print(f"Error fetching weather data: {e}")
            return None
