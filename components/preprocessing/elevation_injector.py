from sklearn.base import BaseEstimator, TransformerMixin
import requests
from requests.exceptions import Timeout

class ElevationInjector( BaseEstimator, TransformerMixin):

  def __init__(self, month_pointer, path_to_temp):
    self.month_pointer = month_pointer
    self.path_to_temp = path_to_temp

  def fit(self, X, y=None):
    return self

  def transform(self, X):
    print(f"****************************Elevation Injecting {self.month_pointer}")
    gps_data, bus_trips_df, trip_ends_df = X

    # print(type(gps_data))

    # create new column called location with combining latitude and the longitude with a comma.
    gps_data['location'] = gps_data.apply(lambda row: f"{row['latitude']},{row['longitude']}", axis=1)

    # extract out locations
    locations = gps_data['location'].tolist()

    # Get elevations for all locations
    elevations = self.get_elevations(locations)

    # Add a new column 'elevation' to the DataFrame
    gps_data['elevation'] = elevations

    gps_data.drop(columns=['location'], axis = 1, inplace = True)

    # saving point
    gps_data.to_csv( self.path_to_temp + "EL_IJ/" + self.month_pointer + "_gps_data.csv", index = False)

    return gps_data, bus_trips_df, trip_ends_df

  def send_request(self, base_url, params, timeout=5, max_retries=3):

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

  def get_elevations(self, locations):
    base_url = "https://maps.googleapis.com/maps/api/elevation/json"
    elevations = []

    # Process locations in batches to stay within API limits
    batch_size = 500
    for i in range(0, len(locations), batch_size):
      # print(i)
      batch_locations = locations[i:i+batch_size]
      locations_str = '|'.join(batch_locations)

      params = {
          'locations': locations_str,
          'key': "AIzaSyC60V5MztXckUnRcp_jMUCegqJmX_pd5KI",
      }

      data = self.send_request(base_url, params)

      if 'results' in data:
          for result in data['results']:
              elevation = result.get('elevation')
              elevations.append(elevation)

    return elevations