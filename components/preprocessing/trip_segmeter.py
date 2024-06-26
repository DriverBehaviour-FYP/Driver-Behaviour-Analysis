from sklearn.base import BaseEstimator, TransformerMixin
from utils.local.save_data import save_data
import pandas as pd
from datetime import datetime, timedelta
import math


class TripSegmenterByTime( BaseEstimator, TransformerMixin):
  
  def __init__(self, month_pointer, path_to_temp, previous_segment_max, seg_pointer = '3T'):
    self.month_pointer = month_pointer
    self.path_to_temp = path_to_temp
    self.previous_segment_max = previous_segment_max
    self.seg_duration_in_mins = int(seg_pointer[:-1])
    self.seg_pointer = seg_pointer

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

      # Generate a range of segment_duration-minute intervals for the current record
      time_intervals = pd.date_range(start=start_time, periods=math.ceil(duration/self.seg_duration_in_mins), freq=f'{self.seg_duration_in_mins}T')

      # Iterate over the time intervals and create a new record for each interval
      for interval in time_intervals:
          end_time = interval + timedelta(minutes=self.seg_duration_in_mins)

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
    save_data(gps_data_ts, self.path_to_temp + "TR_SG_BT/"+ self.seg_pointer +"/" , self.month_pointer + "_gps_data.csv")
    save_data(segments_df, self.path_to_temp + "TR_SG_BT/" + self.seg_pointer + "/" , self.month_pointer + "_segments.csv")

    return gps_data_ts, segments_df