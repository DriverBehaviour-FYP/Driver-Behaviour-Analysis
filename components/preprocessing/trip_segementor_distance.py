from sklearn.base import BaseEstimator, TransformerMixin
from geopy.distance import geodesic
import pandas as pd
import numpy as np
import requests
from requests.exceptions import Timeout
from utils.local.save_data import save_data
import os

# this is the secondary segmentation component which creates the DataFrame of route points along the track
class TripSegmenterByDistance( BaseEstimator, TransformerMixin):

  def __init__(self, month_pointer, path_to_temp, previous_segment_max,path_to_terminals, precision=0.01, seg_pointer = '1000M', ):
    self.month_pointer = month_pointer
    self.path_to_temp = path_to_temp
    self.previous_segment_max = previous_segment_max
    self.seg_distance = int(seg_pointer[:-1])
    self.seg_pointer = seg_pointer
    self.path_to_terminals = path_to_terminals
    self.precision = precision

  def fit(self, X, y=None):
    return self
  
  def calculate_split_df(self, gps_data_ts, bus_trips_ts):
    # load terminals so that starting location and ending location is known
    terminals = pd.read_csv(self.path_to_terminals)

    # load starting point and ending points from the terminals df
    starting_point = (terminals.loc[0]['latitude'], terminals.iloc[0]['longitude'])
    ending_point  = (terminals.loc[1]['latitude'], terminals.iloc[1]['longitude'])

    processing_point = starting_point

    # select trips that are driven to the selected direction
    bus_trips_dir_1 = bus_trips_ts[(bus_trips_ts['start_terminal']==terminals.loc[0]['terminal_id']) & (bus_trips_ts['end_terminal']==terminals.loc[1]['terminal_id'])]

    # splitting points that would identify will store here
    split_points = []

    split_point_id = 1

    # run until complete route is segmented
    # get the distance from currently processing point to ending point and compare with segment length
    while(self.get_directions(processing_point, ending_point)['routes'][0]['legs'][0]['distance']['value']>self.seg_distance):
      print("Processing: ",split_point_id)
      # assign a ID to the split point
      split_point = {
        'split_point_id': split_point_id
      }
      # iterate through the bus trips df for the selected trips
      for index, row in bus_trips_dir_1.iterrows():
        max_index = np.max(np.where(gps_data_ts['trip_id'] == row['trip_id']))
        min_index = np.min(np.where(gps_data_ts['trip_id'] == row['trip_id']))

        margin, distance = self.binary_search(gps_data_ts,processing_point, min_index, max_index, ending_point)
        print(f"margin: {margin}, distance: {distance}")
        if abs(self.seg_distance - distance)/self.seg_distance <= self.precision:
          split_point['latitude'] = gps_data_ts.iloc[margin]['latitude']
          split_point['longitude'] = gps_data_ts.iloc[margin]['longitude']
          break

      # append the split points to the output list
      split_points.append(split_point)
      
      # increment the id
      split_point_id+=1

      processing_point = (split_point['latitude'], split_point['longitude'])
    
    # take splitting points into a dataframe
    split_points_df = pd.DataFrame(split_points)

    # save split points in temp dir
    save_path = self.path_to_temp + "SPLIT_POINTS/"
    save_data(split_points_df,save_path,f"{self.month_pointer}_split_points_{self.seg_pointer}.csv")

    return split_points_df

  def transform(self, X):
    print(f"****************************Trip Segmenting by Distance {self.month_pointer}")
    # splits data into gps data and the bus trips
    gps_data_ts, bus_trips_ts = X

    # path to split points in temp
    split_points_file_path = self.path_to_temp + "SPLIT_POINTS/" + f"{self.month_pointer}_split_points_{self.seg_pointer}.csv"

    if os.path.exists(split_points_file_path):
      split_points_df = pd.read_csv(split_points_file_path)
      print("Loaded splitting points from cache")
    else:
      print("Cache not found! calculating split points.")
      split_points_df = self.calculate_split_df(gps_data_ts, bus_trips_ts)
    
    # initialize segment ids of gps data to None
    gps_data_ts['segment_id'] = np.nan

    # segment_id for the gps_data ans segments df
    segment_id = self.previous_segment_max + 1

    # segments to keep details of segments
    segments = []

    split_points_arr = []

    for index, row in bus_trips_ts.iterrows():
    #   print(f"Processing trip-ID: {index+1} with dir: {row['direction']}")
      # get the maximum and minimum indexes of trip's gps points
      max_index = np.max(np.where(gps_data_ts['trip_id'] == row['trip_id']))
      min_index = np.min(np.where(gps_data_ts['trip_id'] == row['trip_id']))

      # take a copy from split points df to store buffer points
      if row['direction']==1:
        buff = split_points_df[::].copy()
      else:
        buff = split_points_df[::-1].reset_index(drop=True).copy()
    
      # initialize the gps_data_index to nan
      buff['gps_data_index'] = np.nan

      # filling out gps_data_ts's index to split points
      for ind, split_row in buff.iterrows():
        split_point = (split_row['latitude'], split_row['longitude'])
        for i in range(min_index, max_index+1):
          gps_point = (gps_data_ts.iloc[i]['latitude'], gps_data_ts.iloc[i]['longitude'])

          dist = geodesic(split_point, gps_point).meters
          if dist<=100:
            buff.loc[ind,'gps_data_index'] = i
            split_points_arr.append({"latitude": gps_point[0], "longitude":gps_point[1]})
            break
      
      # assign gps_data_ts the segment_ids
      for i in range(0, len(buff)):
        start = min_index if i==0 else buff.loc[i-1]['gps_data_index']
        end = buff.loc[i]['gps_data_index']

        gps_data_ts.loc[start:end,'segment_id'] = segment_id
        # print(f"{type(end)} value: {end}  {np.isnan(end)}")
        segments.append({
          'segment_starting_time': gps_data_ts.loc[start]['devicetime'] if not np.isnan(start) else np.nan,
          'segment_ending_time': gps_data_ts.loc[end]['devicetime'] if not np.isnan(end) else np.nan,
          'trip_id': row['trip_id'],
          'deviceid': row['deviceid'],
          'date': row['date'],
          'start_terminal':row['start_terminal'],
          'end_terminal': row['end_terminal'],
          'direction': row['direction'],
          'day_of_week': row['day_of_week'],
          'hour_of_day': row['hour_of_day']
        })
        segment_id+=1

        if i== len(buff)-1 :
          gps_data_ts.loc[end:max_index,'segment_id'] = segment_id
          segments.append({
            'segment_starting_time': gps_data_ts.loc[end]['devicetime'] if not np.isnan(end) else np.nan,
            'segment_ending_time': gps_data_ts.loc[max_index]['devicetime'] if not np.isnan(max_index) else np.nan,
            'trip_id': row['trip_id'],
            'deviceid': row['deviceid'],
            'date': row['date'],
            'start_terminal':row['start_terminal'],
            'end_terminal': row['end_terminal'],
            'direction': row['direction'],
            'day_of_week': row['day_of_week'],
            'hour_of_day': row['hour_of_day']
          })
          segment_id += 1
    
    segments_out = pd.DataFrame(segments)
    pd.DataFrame(split_points_arr).to_csv("./split_points_of_trips.csv", index=False)
    return gps_data_ts, segments_out

  def binary_search(self, gps_data, origin,starting_ind, max_ind, terminal_location):
    # low and high is for binary search since there are needed to calculate mid
    low, high = starting_ind, max_ind

    # early distance and mid is stored since it is useful when returning the optimal mid and distance
    early_mid, early_distance = None, None

    # tracking rounds since to store early mid and early distance, rounds > 0
    rounds = 0

    while low<=high:
      if rounds>0:
        early_mid, early_distance = mid, distance
      mid = (low + high)//2

      # assigning destination
      destination = (gps_data.iloc[mid]['latitude'], gps_data.iloc[mid]['longitude'])

      origin_to_terminal = self.get_directions(origin, terminal_location)['routes'][0]['legs'][0]['distance']['value']
      destination_to_teminal = self.get_directions(destination, terminal_location)['routes'][0]['legs'][0]['distance']['value']

      if origin_to_terminal<=destination_to_teminal:
        low = mid+1
        continue

      # calling the API
      res  = self.get_directions(origin, destination)

      # extract out distance
      distance = res['routes'][0]['legs'][0]['distance']['value']

      if distance>= self.seg_distance - 20 and distance <= self.seg_distance + 20:
        # print(res['routes'][0]['legs'][0])
        return mid, distance
      elif distance < self.seg_distance - 20:
        low = mid + 1
      elif distance > self.seg_distance + 20:
        high = mid - 1
      rounds+=1
    # print(f"Er dis: {early_distance}  er_mid: {early_mid}")
    if early_mid!=None and abs(self.seg_distance-early_distance) <= abs(self.seg_distance-distance):
      return early_mid, early_distance
    else:
      return mid, distance
    

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