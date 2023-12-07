from sklearn.base import BaseEstimator, TransformerMixin
from datetime import datetime, date
import pandas as pd
import geopandas as gpd
import numpy as np


# put your AccelerationCalculator here
class AccelerationCalculator( BaseEstimator, TransformerMixin):
  
  def __init__(self, month_pointer, path_to_temp):
    self.month_pointer = month_pointer
    self.path_to_temp = path_to_temp

  def fit(self, X, y=None):
    return self

  def transform(self, X):
    print(f"****************************Calculating Accelaration features {self.month_pointer}")
    gps_data_ts, segments_ts = X
    segment_id_list = segments_ts['segment_id'].unique()
    gps_data_ts['devicetime'] = pd.to_datetime(gps_data_ts['devicetime'])

    acceleration_list = []
    deacceleration_list = []
    # acceleration_sd_list = []
    # deacceleration_sd_list = []
    std_acc_dacc_list =[]

    for segment_id in segment_id_list:
        select_segment = gps_data_ts[gps_data_ts['segment_id'] == segment_id]
        velocities = select_segment['speed'].tolist()
        times = select_segment['devicetime'].tolist()

        accelerations =[]
        # Calculate accelerations
        for i in range(len(velocities) - 1): 
          time_difference = (times[i + 1] - times[i]).total_seconds()

            # Check if the time difference is zero before division
          if time_difference != 0:
            acceleration = (velocities[i + 1] - velocities[i]) / time_difference
            accelerations.append(acceleration)
        
        # Filter positive accelerations
        positive_accelerations = [acc for acc in accelerations if acc > 0]
        # Filter negative accelerations
        negative_accelerations = [acc for acc in accelerations if acc < 0]

        deacceleration = sum(negative_accelerations) / len(negative_accelerations) if len(negative_accelerations) > 0 else np.nan
        acceleration = sum(positive_accelerations) / len(positive_accelerations) if len(positive_accelerations) > 0 else np.nan
        std_acc_dacc = np.std(accelerations) if len(accelerations) > 0 else np.nan

        deacceleration_list.append(deacceleration)
        acceleration_list.append(acceleration)
        std_acc_dacc_list.append(std_acc_dacc)
        
    segments_df = segments_ts.copy()
    segments_df['average_acceleration'] = acceleration_list
    segments_df['average_deacceleration'] = deacceleration_list
    segments_df['std_acc_dacc'] = std_acc_dacc_list

    segments_df.to_csv( self.path_to_temp + "AC_CAL/" + self.month_pointer + "_segment_data.csv", index = False)

    return gps_data_ts, segments_df

