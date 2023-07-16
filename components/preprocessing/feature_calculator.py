from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np


class FeatureCalculator(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        gps_data_df, segments_df = X
        max_speeds = []
        speed_variences = []
        for index, row in segments_df.iterrows():
            segment_id = row["segment_id"]
            speeds = gps_data_df[gps_data_df["segment_id"] == segment_id]["speed"].values
            if len(speeds) > 0:
                max_speed = max(speeds)
                variation = np.var(speeds)
            else:
                max_speed = None
                variation = None
            max_speeds.append(max_speed)
            speed_variences.append(variation)
        segments_df["max_speed"] = max_speeds
        segments_df["variation"] = speed_variences

        return gps_data_df, segments_df
