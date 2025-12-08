# =============================================================================
# CVE FETCHER MODULE
# =============================================================================
# This file is where I fetch security vulnerability data from the internet
# CVE stands for Common Vulnerabilities and Exposures - it's how security
# researchers track bugs that hackers could exploit
# Example: CVE-2024-1234 might be a specific bug in Ubiquiti routers

# =============================================================================
# IMPORT REQUIRED LIBRARIES
# =============================================================================
import requests
# I'm using the requests library to make HTTP calls to the NVD API
# It's basically like a web browser but for Python code
# I installed it with: pip install requests

from datetime import datetime
# I need datetime for two things:
#   1. Converting the date strings I get from the API into readable dates
#   2. Tracking when I last fetched data (for caching)

import os
# I use os to read environment variables from my .env file
# This is where I store my API key so it's not visible in my code
# (My professor emphasized keeping API keys out of GitHub)

from dotenv import load_dotenv
# The dotenv library loads my API key from the .env file
# I installed it with: pip install python-dotenv

# I call this first to load the .env file before I try to use the API key
load_dotenv()
# This searches for a .env file and reads all the settings from it
# My .env file has one line: NVD_API_KEY=my-actual-key-here

# =============================================================================
# CVEFetcher CLASS DEFINITION
# =============================================================================
class CVEFetcher:
    """
    I made this class to handle all the CVE fetching logic

    What it does:
    - Connects to the National Vulnerability Database API
    - Searches for Ubiquiti vulnerabilities
    - Filters out router-specific ones
    - Returns the data in a format my dashboard can use

    I put this in a class because:
    - I can keep all the CVE-related code in one place
    - I can store the API key and cached data as properties
    - It's easier to reuse if I want to add more features later
    """

    # =========================================================================
    # CONSTRUCTOR METHOD
    # =========================================================================
    def __init__(self):
        """
        This __init__ method runs automatically when I create a CVEFetcher object
        It sets up everything I need: the API key, the URL, and cache storage
        """

        # =====================================================================
        # LOAD THE API KEY
        # =====================================================================
        # I try to load the API key from my .env file
        # If there's no key, the code still works (just with rate limits)
        self.api_key = os.getenv('NVD_API_KEY')

        # If the .env file has an empty value, I want to treat it as None
        # This makes my if-statements simpler later
        if self.api_key == "":
            self.api_key = None

        # =====================================================================
        # SET UP THE API URL
        # =====================================================================
        # This is the NVD API endpoint where I send my requests
        self.api_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"

        # Important note about rate limits:
        # Without an API key: only 5 requests per 30 seconds (really slow)
        # With an API key: 50 requests per 30 seconds (much better)
        # I got my free API key from: https://nvd.nist.gov/developers/request-an-api-key

        # =====================================================================
        # SET UP CACHE STORAGE
        # =====================================================================
        # I'm using cache to store the last successful API response
        # This way if the API is down, I can still show something
        self.cached_cves = None
        # Starts as None, becomes a list after the first successful fetch

        self.last_fetch_time = None
        # I track when I last fetched data in case I want to implement
        # rate limiting later (like only fetch once per minute)

    # =========================================================================
    # MAIN METHOD TO GET CVE DATA
    # =========================================================================
    def get_ubiquiti_cves(self, max_results=3):
        """
        This is the main method that fetches Ubiquiti CVEs from the NVD API

        I set max_results=3 because my dashboard only shows 3 CVEs

        Returns a list of dictionaries with CVE info, or None if something fails
        """

        # =====================================================================
        # WRAP EVERYTHING IN TRY-EXCEPT FOR ERROR HANDLING
        # =====================================================================
        # API calls can fail for lots of reasons (no internet, API down, etc)
        # I use try-except so my dashboard doesn't crash if something goes wrong
        try:
            # =================================================================
            # SET UP THE SEARCH PARAMETERS
            # =================================================================
            # I create a dictionary with my search criteria
            # NVD API v2.0 requires specific parameter format
            params = {
                'keywordSearch': 'Ubiquiti',
                'resultsPerPage': 5
            }
            # keywordSearch: I'm looking for anything mentioning "Ubiquiti"
            # resultsPerPage: Limit to 5 results to reduce data transfer

            # =================================================================
            # ADD MY API KEY TO THE HEADERS (IF I HAVE ONE)
            # =================================================================
            # I learned that NVD API v2.0 wants the API key in the headers
            # The correct header name is 'X-API-Key' (not 'apiKey')
            headers = {}

            # If I have an API key, I add it to the headers
            if self.api_key:
                headers['X-API-Key'] = self.api_key
                # This gives me 50 requests/30sec instead of just 5
            # If I don't have a key, I just leave headers empty and it still works

            # =================================================================
            # MAKE THE HTTP REQUEST TO THE API
            # =================================================================
            # I use requests.get() to fetch data from the NVD API
            response = requests.get(self.api_url, params=params, headers=headers, timeout=10)
            # self.api_url: The NVD endpoint I'm calling
            # params: My search criteria (keyword=Ubiquiti)
            # headers: My API key (if I have one)
            # timeout=10: Give up after 10 seconds if no response

            # Check if the request was successful (status code 200)
            # If not, this will raise an error and jump to my except block
            response.raise_for_status()

            # =================================================================
            # CONVERT THE RESPONSE FROM JSON TO PYTHON DICTIONARY
            # =================================================================
            # The API sends back JSON (text format)
            # I convert it to a Python dictionary so I can work with it
            data = response.json()

            # Make sure the response has what I expect
            # If there's no 'vulnerabilities' key, something's wrong
            if 'vulnerabilities' not in data:
                return None  # Return None so my dashboard knows there's no data

            # =================================================================
            # PROCESS THE CVE DATA
            # =================================================================
            # I create an empty list to store the cleaned-up CVE data
            cves = []

            # Pull out the vulnerabilities list from the response
            vulnerabilities = data['vulnerabilities']

            # =================================================================
            # LOOP THROUGH EACH CVE
            # =================================================================
            # I loop through up to 9 vulnerabilities (max_results * 3)
            # I do more than 3 because some might be missing data I need
            for vuln_item in vulnerabilities[:max_results * 3]:
                # Each vuln_item is one CVE record from the API

                # Pull out the CVE data
                cve = vuln_item.get('cve', {})
                cve_id = cve.get('id', 'N/A')

                # -------------------------------------------------------------
                # EXTRACT THE DESCRIPTION
                # -------------------------------------------------------------
                # CVEs can have descriptions in multiple languages
                # I need to find the English one
                descriptions = cve.get('descriptions', [])
                description = 'No description available'  # Default if I don't find English

                # Loop through until I find the English description
                for desc in descriptions:
                    if desc.get('lang') == 'en':
                        description = desc.get('value', 'No description available')
                        break  # Found it, stop looking

                # -------------------------------------------------------------
                # CHECK IF THIS CVE AFFECTS ROUTERS
                # -------------------------------------------------------------
                # I want to flag CVEs that specifically affect routers
                # I check if the description mentions router-related keywords
                description_lower = description.lower()
                router_keywords = ['router', 'unifi', 'usg', 'udm', 'network', 'gateway']

                # Loop through keywords and see if any are in the description
                is_router_related = False
                for keyword in router_keywords:
                    if keyword in description_lower:
                        is_router_related = True
                        break  # Found one, that's enough

                # -------------------------------------------------------------
                # EXTRACT CVSS SCORE AND SEVERITY
                # -------------------------------------------------------------
                # CVSS scores tell me how dangerous a vulnerability is (0-10 scale)
                # Higher = more dangerous. I use this for color-coding in my dashboard
                metrics = cve.get('metrics', {})

                # Set defaults in case there's no score
                cvss_score = 'N/A'
                severity = 'UNKNOWN'

                # Try different CVSS versions (some CVEs use v3.1, some v3.0, some v2.0)
                # I check in order from newest to oldest
                cvss_versions = ['cvssMetricV31', 'cvssMetricV30', 'cvssMetricV2']

                for cvss_version in cvss_versions:
                    if cvss_version in metrics and metrics[cvss_version]:
                        # Found a version that exists, grab the score from it
                        cvss_data = metrics[cvss_version][0]['cvssData']
                        cvss_score = cvss_data.get('baseScore', 'N/A')
                        severity = cvss_data.get('baseSeverity', 'UNKNOWN')
                        break  # Got what I need, stop checking other versions

                # -------------------------------------------------------------
                # CLEAN UP THE PUBLISHED DATE
                # -------------------------------------------------------------
                # The API gives me dates like "2024-11-30T15:30:00.000Z"
                # I want to simplify it to just "2024-11-30" for my dashboard
                published = cve.get('published', 'N/A')

                if published != 'N/A':
                    try:
                        # Parse the date string and reformat it
                        pub_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
                        published = pub_date.strftime('%Y-%m-%d')
                    except:
                        # If parsing fails, just keep the original string
                        pass

                # -------------------------------------------------------------
                # BUILD THE CVE DICTIONARY
                # -------------------------------------------------------------
                # I need to shorten the description if it's too long
                # (otherwise it breaks my dashboard layout)
                if len(description) > 200:
                    description = description[:200] + '...'

                # Put all the data into a dictionary
                cve_info = {
                    'id': cve_id,
                    'description': description,
                    'severity': severity,
                    'cvss_score': cvss_score,
                    'published': published,
                    'is_router_related': is_router_related
                }

                # Add this CVE to my list
                cves.append(cve_info)

                # If I have enough CVEs, stop processing more
                if len(cves) >= max_results:
                    break  # Exit the loop early

            # =================================================================
            # SAVE TO CACHE AND RETURN
            # =================================================================
            # I save the results to cache in case the API fails next time
            self.cached_cves = cves
            self.last_fetch_time = datetime.now()

            # Return the list of CVE dictionaries to my dashboard
            return cves

        # =====================================================================
        # ERROR HANDLING - NETWORK PROBLEMS
        # =====================================================================
        except requests.exceptions.RequestException as e:
            # This catches errors from the requests library
            # (no internet, timeout, bad status code, etc.)
            print(f"Error fetching CVE data: {e}")

            # If I have cached data, return that instead of crashing
            # Otherwise return None so my dashboard knows something failed
            if self.cached_cves:
                return self.cached_cves
            else:
                return None

        # =====================================================================
        # ERROR HANDLING - OTHER UNEXPECTED PROBLEMS
        # =====================================================================
        except Exception as e:
            # This catches any other errors I didn't anticipate
            # (bad data format, missing keys, etc.)
            print(f"Unexpected error fetching CVE data: {e}")

            # Same logic - try to return cached data, otherwise None
            if self.cached_cves:
                return self.cached_cves
            else:
                return None

# =============================================================================
# END OF FILE
# =============================================================================
# How I use this in app.py:
#   from cve_fetcher import CVEFetcher
#   fetcher = CVEFetcher()
#   cves = fetcher.get_ubiquiti_cves(3)
