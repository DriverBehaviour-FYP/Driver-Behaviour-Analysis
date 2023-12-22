from sklearn.base import BaseEstimator, TransformerMixin
from requests.exceptions import Timeout
import requests
from datetime import datetime, date
import pandas as pd
import geopandas as gpd
import numpy as np


class TripExtractor( BaseEstimator, TransformerMixin):
  
  def __init__(self, month_pointer, path_to_temp):
    self.month_pointer = month_pointer
    self.path_to_temp = path_to_temp

  def fit(self, X, y=None):
    return self

  def transform(self, X):
    gps_data,bus_trips,trip_ends = X
    # global month_pointer, bus_terminals, path_to_temp, previous_trip_max
    print(f"****************************Trip Filtering {self.month_pointer}")

    # saving point
    gps_data_2.to_csv( self.path_to_temp + "TR_EX/" + self.month_pointer + "_gps_data.csv", index = False)
    bus_trips.to_csv( self.path_to_temp + "TR_EX/" + self.month_pointer + "_bus_trips.csv", index = False)
    trip_ends.to_csv( self.path_to_temp + "TR_EX/" + self.month_pointer + "_trip_ends.csv", index = False)

    return   # returns gps_data dataframe with trip ids, and bus_trips dataframe
  

  def get_directions(self, origin, destination, timeout=5, max_retries=3):
    base_url = "https://maps.googleapis.com/maps/api/directions/json"

    params = {
        'origin': f"{origin[0]},{origin[1]}",
        'destination': f"{destination[0]},{destination[1]}",
        'key': "AIzaSyCz5uw3SrNct_Dqw6S6_D6AokxUVp0_hAg",
    }

    for retry in range(max_retries):
        try:
            response = requests.get(base_url, params=params, timeout=timeout)
            response.raise_for_status()  # Raise an HTTPError for bad responses

            # Parse and return the JSON response
            return response.json()
        except Timeout:
            print(f"Timeout error. Retrying... ({retry + 1}/{max_retries})")
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")

    # If all retries fail, return None or handle as needed
    print(f"Failed after {max_retries} retries. Returning None.")
    return None
