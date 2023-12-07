from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np


class FeatureCalculator(BaseEstimator, TransformerMixin):

    def __init__(self, month_pointer, path_to_temp):
        self.month_pointer = month_pointer
        self.path_to_temp = path_to_temp

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        print(f"****************************Calculating Speed Features {self.month_pointer}")
        gps_data_df, segments_df = X
        max_speeds = []
        speed_variences = []
        speed_averages = []
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

            # calculating non-zero speed sum
            non_zero_speed_sum = 0
            count = 0
            for spd in speeds:
                if spd>0:
                    non_zero_speed_sum+= spd
                    count+=1
            speed_averages.append(non_zero_speed_sum/count if count!=0 else 0)
        segments_df['average_speed'] = speed_averages
        segments_df["max_speed"] = max_speeds
        segments_df["speed_variation"] = speed_variences

        gps_data_df.to_csv( self.path_to_temp + "SP_FC/" + self.month_pointer + "_gps_data.csv", index = False)
        segments_df.to_csv( self.path_to_temp + "SP_FC/" + self.month_pointer + "_segments.csv", index = False)

        return gps_data_df, segments_df
