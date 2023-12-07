from sklearn.base import BaseEstimator, TransformerMixin
from datetime import datetime, date
import pandas as pd
import numpy as np


# put your StoppingFrequencyForSegment here
class StoppingFrequencyForSegment( BaseEstimator, TransformerMixin):
  def fit(self, X, y=None):
    return self

  def transform(self, X):
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

    return gps_data_ts, segments_df

