"""
Created on 25.08.2024

@author: wf
"""

import logging

from geopy.exc import GeocoderTimedOut, GeocoderUnavailable, GeocoderQueryError
from geopy.geocoders import Nominatim


class NominatimWrapper:
    """
    Nominatim Wrapper to search for locations and retrieve Wikidata IDs
    """

    def __init__(self, user_agent: str = "AppUsingNominatim"):
        """
        Initialize the NominatimWrapper

        Args:
            user_agent (str): The user agent to use for the geolocator
        """
        self.geolocator = Nominatim(user_agent=user_agent)
        logging.getLogger("geopy").setLevel(logging.ERROR)

    def lookup_wikidata_id(self, location_text: str, max_retries: int = 3):
        """
        Lookup the Wikidata Identifier for the given location text

        Args:
            location_text (str): The location text to search for
            max_retries (int): Maximum number of retries in case of timeout or unavailability

        Returns:
            str: The Wikidata Q identifier most fitting the given location text, or None if not found
        """
        for attempt in range(max_retries):
            try:
                location = self.geolocator.geocode(
                    location_text, exactly_one=True, extratags=True
                )

                if location:
                    extratags = location.raw.get("extratags", {})
                    if extratags and "wikidata" in extratags:
                        return extratags["wikidata"]
                return None
            except (GeocoderTimedOut, GeocoderUnavailable):
                if attempt == max_retries - 1:
                    logging.error(f"Failed to geocode after {max_retries} attempts")
                else:
                    logging.warning(
                        f"Geocoding attempt {attempt + 1} failed, retrying..."
                    )
            except GeocoderQueryError:
                logging.warning("Geocoding failed")
        return None
