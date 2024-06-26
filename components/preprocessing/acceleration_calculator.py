from sklearn.base import BaseEstimator, TransformerMixin
from utils.local.save_data import save_data
from datetime import datetime, date
import pandas as pd
import geopandas as gpd
import numpy as np


# put your AccelerationCalculator here
class AccelerationCalculator( BaseEstimator, TransformerMixin):
  
  def __init__(self, month_pointer, path_to_temp, seg_pointer):
    self.month_pointer = month_pointer
    self.path_to_temp = path_to_temp
    self.seg_pointer = seg_pointer

  def fit(self, X, y=None):
    return self

  def transform(self, X):
    print(f"****************************Calculating Accelaration features {self.month_pointer}")
    gps_data_ts, segments_ts = X
    segment_id_list = segments_ts['segment_id'].unique()
    gps_data_ts['devicetime'] = pd.to_datetime(gps_data_ts['devicetime'])

    acceleration_list = []
    deacceleration_list = []
    acceleration_max_list = []
    deacceleration_max_list = []
    no_of_points_list = []
    no_of_acc_points_list = []
    no_of_deacc_points_list = []
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

        # calculate maximums
        acceleration_max_list.append(max(positive_accelerations) if len(positive_accelerations)>0 else 0)
        deacceleration_max_list.append(min(negative_accelerations) if len(negative_accelerations)>0 else 0)
        no_of_points_list.append(len(select_segment))
        no_of_acc_points_list.append(len(positive_accelerations))
        no_of_deacc_points_list.append(len(negative_accelerations))
        
    segments_df = segments_ts.copy()
    segments_df['average_acceleration'] = acceleration_list
    segments_df['average_deacceleration'] = deacceleration_list
    segments_df['std_acc_dacc'] = std_acc_dacc_list

    # add maximums to the dataframe
    segments_df['max_acceleration'] = acceleration_max_list
    segments_df['max_deacceleration'] = deacceleration_max_list
    segments_df['no_data_points'] = no_of_points_list
    segments_df['no_acc_points'] = no_of_deacc_points_list
    segments_df['no_deacc_points'] = no_of_deacc_points_list

    save_data(segments_df, self.path_to_temp + "AC_CAL/" + self.seg_pointer +"/" , self.month_pointer + "_segment_data.csv")

    return gps_data_ts, segments_df

