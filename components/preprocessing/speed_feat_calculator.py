from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np
from utils.local.save_data import save_data


class SpeedFeatureCalculator(BaseEstimator, TransformerMixin):

    def __init__(self, month_pointer, path_to_temp, seg_pointer):
        self.month_pointer = month_pointer
        self.path_to_temp = path_to_temp
        self.seg_pointer = seg_pointer

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        print(f"****************************Calculating Speed Features {self.month_pointer}")
        gps_data_df, segments_df = X
        max_speeds = []
        speed_stds = []
        speed_means = []
        for index, row in segments_df.iterrows():
            segment_id = row["segment_id"]
            speeds = gps_data_df[gps_data_df["segment_id"] == segment_id]["speed"].values
            if len(speeds) > 0:
                max_speed = max(speeds)
                speed_std = np.std(speeds)
                speed_mean = np.mean(speeds, where=speeds>0)
            else:
                max_speed = None
                speed_std = None
                speed_mean = None
            max_speeds.append(max_speed)
            speed_stds.append(speed_std)
            speed_means.append(speed_mean)

        segments_df['speed_mean'] = speed_means
        segments_df["speed_max"] = max_speeds
        segments_df["speed_std"] = speed_stds

        save_data(gps_data_df, self.path_to_temp + "SP_FC/" + self.seg_pointer+ "/" , self.month_pointer + "_gps_data.csv")
        save_data(segments_df, self.path_to_temp + "SP_FC/" + self.seg_pointer+ "/", self.month_pointer + "_segments.csv")

        return gps_data_df, segments_df
