from sklearn.base import BaseEstimator, TransformerMixin
import pandas as pd



class Cleaner( BaseEstimator, TransformerMixin):
  
  def __init__(self, month_pointer):
    self.month_pointer = month_pointer

  def fit(self, X, y=None):
    return self

  def transform(self, X):
    print(f"****************************Cleaning {self.month_pointer}")
    gps_data = X[X.latitude != 0]
    gps_data = gps_data[gps_data.longitude != 0] #cleaning zero values for latitude & longitude

    gps_data['date'] = pd.to_datetime(gps_data['devicetime']).dt.date #split date and time separately into datetime variables
    gps_data['time'] = pd.to_datetime(gps_data['devicetime']).dt.time

    gps_data = gps_data.sort_values(['deviceid', 'date', 'time']) #sorting dataset by time and device

    return gps_data
