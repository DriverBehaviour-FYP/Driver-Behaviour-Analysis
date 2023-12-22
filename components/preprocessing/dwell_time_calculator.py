from sklearn.base import BaseEstimator, TransformerMixin
import pandas as pd
import numpy as np

import geopandas as gpd

from utils.local.retrieve_data import get_data_from_path

class DwellTimeCalculator( BaseEstimator, TransformerMixin):

  def __init__(self, month_pointer,path_bus_stops , path_bus_trips):
    self.month_pointer = month_pointer
    self.path_bus_stops = path_bus_stops
    self.path_bus_trips = path_bus_trips

  def fit(self, X, y=None):
    return self

  def transform(self, X):
    gps_data,segment_data = X
    bus_stops = get_data_from_path(self.path_bus_stops)
    bus_trips = get_data_from_path(self.path_bus_trips)


    stop_buffer = 50
    extra_buffer = 100
    bus_stops_buffer1, bus_stops_buffer2,gps_data,bus_stops_buffer1_add,bus_stops_buffer2_add = self.bus_stop_buffer_create(gps_data,bus_stops,stop_buffer,extra_buffer)

    bus_trajectory = self.bus_trajectory(gps_data,bus_trips)

    bus_trip_all_points, bus_stop_all_points = self.stop_buffer_filter(bus_trajectory,bus_stops_buffer1,bus_stops_buffer2,bus_stops_buffer1_add,bus_stops_buffer2_add)
    
    segment_df = self.calculate_dewll_time(bus_trip_all_points, segment_data)

    return segment_df

  #developing geo-buffer rings around every bus stops
  def bus_stop_buffer_create(gps_data,bus_stops,stop_buffer,extra_buffer):

    #Create Geodataframe of GPS data and bus stops data
    gps_data = gpd.GeoDataFrame(gps_data, geometry=gpd.points_from_xy(gps_data.longitude,gps_data.latitude),crs='EPSG:4326')
    bus_stops = gpd.GeoDataFrame(bus_stops, geometry=gpd.points_from_xy(bus_stops.longitude,bus_stops.latitude),crs='EPSG:4326')

    #project the corrdinates in Local coordinate system
    bus_stops = bus_stops.to_crs('EPSG:5234')
    gps_data = gps_data.to_crs('EPSG:5234')

    #split bus stops dataframe into two based on route direction
    bus_stops_direction1 = bus_stops[bus_stops['direction']=='Kandy-Digana']
    bus_stops_direction2 = bus_stops[bus_stops['direction']=='Digana-Kandy']

    bus_stops_direction2.reset_index(drop = True, inplace = True)

    #proximity analysis
    #creating a buffer
    bus_stops_buffer1 = gpd.GeoDataFrame(bus_stops_direction1, geometry = bus_stops_direction1.geometry.buffer(stop_buffer))
    bus_stops_buffer2 = gpd.GeoDataFrame(bus_stops_direction2, geometry = bus_stops_direction2.geometry.buffer(stop_buffer))

    #creating additional extra buffer to accomodate points if they were missed in standard stop buffer
    bus_stops_buffer1_add = gpd.GeoDataFrame(bus_stops_direction1, geometry = bus_stops_direction1.geometry.buffer(extra_buffer))
    bus_stops_buffer2_add = gpd.GeoDataFrame(bus_stops_direction2, geometry = bus_stops_direction2.geometry.buffer(extra_buffer))

    return bus_stops_buffer1, bus_stops_buffer2,gps_data,bus_stops_buffer1_add,bus_stops_buffer2_add

  #splitting trajectories
  def bus_trajectory(bus_trajectory,bus_trips):

    trip =1
    for i in range(len(bus_trajectory)-1):
      if (bus_trajectory.at[i,'trip_id']==trip) & (bus_trajectory.at[i+1, 'trip_id'] == 0):
        bus_trajectory.at[i+1,'trip_id'] = trip
      elif (bus_trajectory.at[i,'trip_id']==trip) & (bus_trajectory.at[i+1, 'trip_id'] == trip):
        trip = trip + 1

    bus_trajectory.drop(bus_trajectory[bus_trajectory['trip_id']==0].index, inplace = True ) #drop records that are not identified as a bus trip

    #Identify the directions of each bus trajectories using bus trips extracted data
    directions= bus_trips.set_index('trip_id').to_dict()['direction']
    bus_trajectory['direction'] = list(map(lambda x: directions[x]   ,bus_trajectory['trip_id']))

    return bus_trajectory

  def stop_buffer_filter(bus_trajectory,bus_stops_buffer1,bus_stops_buffer2,bus_stops_buffer1_add,bus_stops_buffer2_add):

    #project to local coordinate system before buffer filtering
    bus_trajectory = bus_trajectory.to_crs('EPSG:5234')

    #split trajectories by direction
    trajectory_dir_1 = bus_trajectory[bus_trajectory['direction'] == 1]
    trajectory_dir_2 = bus_trajectory[bus_trajectory['direction'] == 2]

    #reset index before for loop
    trajectory_dir_1.reset_index(drop = True, inplace = True)
    trajectory_dir_2.reset_index(drop = True, inplace = True)

    #filter records within bus stops buffer of both directions
    for i in range(len(trajectory_dir_1)):
      for stop in range(len(bus_stops_buffer1)):
        if bus_stops_buffer1.iloc[stop].geometry.contains(trajectory_dir_1.iloc[i].geometry):
          trajectory_dir_1.at[i,'bus_stop_zone'] = bus_stops_buffer1.at[stop,'stop_id']
        else:
          if bus_stops_buffer1_add.iloc[stop].geometry.contains(trajectory_dir_1.iloc[i].geometry):
            trajectory_dir_1.at[i,'bus_stop_zone'] = bus_stops_buffer1_add.at[stop,'stop_id']

    for i in range(len(trajectory_dir_2)):
      for stop in range(len(bus_stops_buffer2)):
        if bus_stops_buffer2.iloc[stop].geometry.contains(trajectory_dir_2.iloc[i].geometry):
          trajectory_dir_2.at[i,'bus_stop_zone'] = bus_stops_buffer2.at[stop,'stop_id']
        else:
          if bus_stops_buffer2_add.iloc[stop].geometry.contains(trajectory_dir_2.iloc[i].geometry):
            trajectory_dir_2.at[i,'bus_stop_zone'] = bus_stops_buffer2_add.at[stop,'stop_id']
    #concatenate dataframes of both directions and keep only records filtered within bus stops
    bus_trip_all_points = pd.concat([trajectory_dir_1,trajectory_dir_2])
    bus_stop_all_points = bus_trip_all_points.dropna()

    return bus_trip_all_points , bus_stop_all_points

  def calculate_dewll_time(bus_trip_all_points, segment_df):
    segment_id_list = segment_df['segment_id'].unique()
    bus_trip_all_points['devicetime'] = pd.to_datetime(bus_trip_all_points['devicetime'])

    stop_time_out_zone_list = []
    stop_time_in_zone_list = []
    stop_count_out_zone_list = []
    stop_count_in_zone_list = []
    number_of_bus_stands_list = []
    x=0
    for segment_id in segment_id_list:
      select_segment = bus_trip_all_points[bus_trip_all_points['segment_id'] == segment_id]
      velocities = select_segment['speed'].tolist()
      timestamps = select_segment['devicetime'].tolist()
      in_zone_flags = select_segment['bus_stop_zone'].tolist()
      number_of_bus_stands = select_segment['bus_stop_zone'].nunique()
      # Initialize variables
      stop_count_in_zone = 0
      stop_count_out_zone = 0
      stop_time_in_zone = 0
      stop_time_out_zone = 0
      is_stopped = False
      stop_start_time = None
      stop_in_zone = False
      zone = None

      # Iterate through velocity values, timestamps, and in_zone flags
      for velocity, timestamp, in_zone_flag in zip(velocities, timestamps, in_zone_flags):
        if velocity == 0 and not is_stopped:
          # Entered a stop, update stop count and start time
          stop_in_zone = not np.isnan(in_zone_flag)
          stop_start_time = timestamp
          is_stopped = True
          zone = in_zone_flag
        elif velocity == 0 and zone != in_zone_flag and is_stopped:
          stop_time = (timestamp - stop_start_time).total_seconds()
          if stop_in_zone:
              stop_count_in_zone += 1
              stop_time_in_zone += stop_time
          else:
              stop_count_out_zone += 1
              stop_time_out_zone += stop_time
          stop_in_zone = not np.isnan(in_zone_flag)
          stop_start_time = timestamp
          is_stopped = True
          zone = in_zone_flag

        elif velocity != 0 and is_stopped:
          # Left the stop, update stop count and time, and reset flag
          stop_time = (timestamp - stop_start_time).total_seconds()
          if stop_in_zone:
              stop_count_in_zone += 1
              stop_time_in_zone += stop_time
          else:
              stop_count_out_zone += 1
              stop_time_out_zone += stop_time
          is_stopped = False
      x+=1
      stop_count_in_zone_list.append(stop_count_in_zone)
      stop_count_out_zone_list.append(stop_count_out_zone)
      stop_time_in_zone_list.append(stop_time_in_zone)
      stop_time_out_zone_list.append(stop_time_out_zone)
      number_of_bus_stands_list.append(number_of_bus_stands)
    segment_tf = segment_df.copy()
    segment_df['stop_count_in_bus_stop_zone'] = stop_count_in_zone_list
    segment_df['stop_count_in_between_bus_stop_zone'] = stop_count_out_zone_list
    segment_df['dwell_time_in_bus_stop_zone'] = stop_time_in_zone_list
    segment_df['dwell_time_in_between_bus_stop_zone'] = stop_time_out_zone_list
    segment_df['number_of_bus_stands'] = number_of_bus_stands_list
    return segment_df