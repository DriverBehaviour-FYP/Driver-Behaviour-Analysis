from sklearn.base import BaseEstimator, TransformerMixin
import pandas as pd

class SegmentFilter(BaseEstimator, TransformerMixin):

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        gps_data_df, trips_df, segments_df = X

        gps_data_df['date'] = pd.to_datetime(gps_data_df['date'])
        trips_df['date'] = pd.to_datetime(trips_df['date'])
        segments_df['date'] = pd.to_datetime(segments_df['date'])

        starting_date = pd.to_datetime("2021-10-01")
        ending_date = pd.to_datetime("2022-10-31")

        # filter based on the dates
        gps_data_df = gps_data_df[(gps_data_df['date'] >= starting_date) & (gps_data_df['date'] <= ending_date)]
        segments_df = segments_df[(segments_df['date']>= starting_date) & (segments_df['date']<= ending_date)]
        trips_df = trips_df[(trips_df['date']>= starting_date) & (trips_df['date']<= ending_date)]

        return gps_data_df, trips_df, segments_df



        


