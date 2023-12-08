from sklearn.base import BaseEstimator, TransformerMixin
from utils.local.save_data import save_data
from datetime import datetime, date
import pandas as pd
import numpy as np


# put your StoppingFrequencyForSegment here
class StoppingFrequencyForSegment( BaseEstimator, TransformerMixin):

  def __init__(self, month_pointer, path_to_temp, seg_pointer):
    self.month_pointer = month_pointer
    self.path_to_temp = path_to_temp
    self.seg_pointer = seg_pointer

  def fit(self, X, y=None):
    return self

  def transform(self, X):
    print(f"****************************Calculating Stopping Frequency {self.month_pointer}")
    gps_data_ts, segments_ts = X
    segment_id_list = segments_ts['segment_id'].unique()
    gps_data_ts['devicetime'] = pd.to_datetime(gps_data_ts['devicetime'])

    stoping_count_list = []
    
    for segment_id in segment_id_list:
        select_segment = gps_data_ts[gps_data_ts['segment_id'] == segment_id]
        velocities = select_segment['speed'].tolist()

        # Initialize variables
        stop_count = 0
        is_stopped = False

        # Iterate through velocity values
        for velocity in velocities:
            if velocity == 0 and not is_stopped:
                # Entered a stop, update stop count
                stop_count += 1
                is_stopped = True
            elif velocity != 0:
                # Left the stop, reset flag
                is_stopped = False

        stoping_count_list.append(stop_count)
        
    segments_df = segments_ts.copy()
    segments_df['stop_count'] = stoping_count_list

    save_data(gps_data_ts, self.path_to_temp + "AC_SF_CAL/" + self.seg_pointer +"/" , self.month_pointer + "_gps_data.csv" )
    save_data(segments_df, self.path_to_temp + "AC_SF_CAL/" + self.seg_pointer +"/" , self.month_pointer + "_segments.csv" )


    return gps_data_ts, segments_df

