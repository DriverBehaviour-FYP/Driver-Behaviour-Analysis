from sklearn.base import BaseEstimator, TransformerMixin
from requests.exceptions import Timeout
from geopy.distance import geodesic
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


class TripFilter( BaseEstimator, TransformerMixin):
  
  def __init__(self, month_pointer, path_to_temp):
    self.month_pointer = month_pointer
    self.path_to_temp = path_to_temp

  def fit(self, X, y=None):
    return self

  def transform(self, X):
    print(f"****************************Trip Filtering {self.month_pointer}")
    gps_data,bus_trips,trip_ends = X

    split_points_path = "../../data/Raw-GPS-data-Kandy-Buses/MAIN/TEMP/SPLIT_POINTS/segment_split_points.csv"
    split_points_df = pd.read_csv(split_points_path)

    out = []

    for index, row in bus_trips.iterrows():
      # print("Procesing ",row['trip_id'] )
      if row['direction']==1:
        buff = split_points_df[::].copy()
      else:
        buff = split_points_df[::-1].reset_index(drop=True).copy()
      max_index = np.max(np.where(gps_data['trip_id'] == row['trip_id']))
      min_index = np.min(np.where(gps_data['trip_id'] == row['trip_id']))

      acc_dis, count = 0, 0
      per_count = (max_index-min_index+1) // len(buff)
  
      for ind, row_buff in buff.iterrows():
         buff_gps = (row_buff['latitude'], row_buff['longitude'])
        #  print(f"Processing buff ind: {ind} through range {ind*per_count + min_index}-{min_index+(ind+1)*per_count}")
         for i in range(min_index+ ind*per_count, min_index+ ind*per_count+ (5 if per_count>5 else per_count)):
            try:
              gps = (gps_data.loc[i]['latitude'], gps_data.loc[i]['longitude'])
              acc_dis += geodesic(buff_gps, gps).meters
              count += 1
            except KeyError:
               print(f"key error occured! trip ID: {row['trip_id']}")

      out.append({"no_of_points": max_index-min_index+1, 'trip_id': row['trip_id'], 'kernel_value': acc_dis/count if count>0 else np.nan})

    df = pd.DataFrame(out)
    trip_ids_below_threshold = set(df[df['no_of_points']<50]['trip_id'])
    trip_ids_not_in_route = set(df[(df['kernel_value']>2200)]['trip_id'])

    all = trip_ids_below_threshold.union(trip_ids_not_in_route)
    print(f"Dropping {len(all)} trips")

    # drop the trips which has low number of points than specified threshold
    gps_data = gps_data.drop(gps_data[gps_data.trip_id.isin(trip_ids_below_threshold)].index)
    bus_trips = bus_trips.drop(bus_trips[bus_trips.trip_id.isin(trip_ids_below_threshold)].index)
    trip_ends = trip_ends.drop(trip_ends[trip_ends.trip_id.isin(trip_ids_below_threshold)].index)


    # drops the trips that are not driven in the focussed route
    gps_data = gps_data.drop(gps_data[gps_data.trip_id.isin(trip_ids_not_in_route)].index)
    bus_trips = bus_trips.drop(bus_trips[bus_trips.trip_id.isin(trip_ids_not_in_route)].index)
    trip_ends = trip_ends.drop(trip_ends[trip_ends.trip_id.isin(trip_ids_not_in_route)].index)

    gps_data.reset_index(drop=True, inplace=True)
    bus_trips.reset_index(drop=True, inplace=True)
    trip_ends.reset_index(drop=True, inplace=True)

    return gps_data, bus_trips, trip_ends