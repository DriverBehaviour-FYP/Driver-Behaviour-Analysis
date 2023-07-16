from sklearn.base import BaseEstimator, TransformerMixin
import pandas as pd


class Cleaner(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        gps_data_df, terminals_df = X
        gps_data = gps_data_df[gps_data_df.latitude != 0]
        gps_data = gps_data[gps_data.longitude != 0]  # cleaning zero values for latitude & longitude

        gps_data['date'] = pd.to_datetime(
            gps_data['devicetime']).dt.date  # split date and time separately into datetime variables
        gps_data['time'] = pd.to_datetime(gps_data['devicetime']).dt.time

        gps_data = gps_data.sort_values(['deviceid', 'date', 'time'])  # sorting dataset by time and device

        return gps_data, terminals_df
