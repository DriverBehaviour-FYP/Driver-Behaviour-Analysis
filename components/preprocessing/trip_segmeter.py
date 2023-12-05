from sklearn.base import BaseEstimator, TransformerMixin
import pandas as pd
from datetime import datetime, timedelta
import math


class TripSegmenterByTime( BaseEstimator, TransformerMixin):
  
  def __init__(self, month_pointer, path_to_temp, previous_segment_max):
    self.month_pointer = month_pointer
    self.path_to_temp = path_to_temp
    self.previous_segment_max = previous_segment_max

  def fit(self, X, y=None):
    return self

  def transform(self, X):
    # global month_pointer, previous_segment_max, path_to_temp
    print(f"****************************Trip segmenting {self.month_pointer}")
    gps_data_ts, bus_trips_ts, trip_ends = X
    new_records = []  # List to store the split records
    for index, row in bus_trips_ts.iterrows():
      duration = row['duration_in_mins']

      date_string = f"{row['date']} {row['start_time']}"
      format_string = "%Y-%m-%d %H:%M:%S"
      parsed_date = datetime.strptime(date_string, format_string)
      start_time = pd.Timestamp(parsed_date)

      # Generate a range of 3-minute intervals for the current record
      time_intervals = pd.date_range(start=start_time, periods=math.ceil(duration/3), freq='3T')

      # Iterate over the time intervals and create a new record for each interval
      for interval in time_intervals:
          end_time = interval + timedelta(minutes=3)

          segment_starting_time = pd.to_datetime(interval)
          segment_ending_time = pd.to_datetime(end_time)

          new_record = {
              'segment_starting_time': segment_starting_time,
              'segment_ending_time': segment_ending_time,
              'trip_id': row['trip_id'],
              'deviceid': row['deviceid'],
              'date': row['date'],
              'start_terminal':row['start_terminal'],
              'end_terminal': row['end_terminal'],
              'direction': row['direction'],
              'day_of_week': row['day_of_week'],
              'hour_of_day': row['hour_of_day']
          }
          new_records.append(new_record)

    # Create a new DataFrame from the split records
    segments_df = pd.DataFrame(new_records)
    segments_df['segment_id'] = [i for i in range(self.previous_segment_max + 1, self.previous_segment_max + len(segments_df)+1)]

    # add the segment id to the GPS data
    segment_ids = []
    for index, row in gps_data_ts.iterrows():
      device_time = pd.to_datetime(row['devicetime'])
      device_id = row['deviceid']
      temp_df1 = segments_df[(segments_df["segment_starting_time"]<=device_time) & (segments_df["segment_ending_time"]>device_time)]
      temp_df2 = temp_df1[temp_df1["deviceid"]==device_id]
      if len(temp_df2)>0:
        segment_ids_temp = temp_df2['segment_id'].values
        segment_id = segment_ids_temp[0]
      else:
        segment_id= None
      segment_ids.append(segment_id)

    gps_data_ts["segment_id"] = segment_ids

    # saving point
    gps_data_ts.to_csv( self.path_to_temp + "TR_SG_BT/" + self.month_pointer + "_gps_data.csv", index = False)
    segments_df.to_csv( self.path_to_temp + "TR_SG_BT/" + self.month_pointer + "_segments.csv", index = False)

    return gps_data_ts, segments_df, bus_trips_ts