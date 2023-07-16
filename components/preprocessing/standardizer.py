from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import StandardScaler


class Standardizer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        scaler = StandardScaler()
        gps_data_df, segments_df = X

        segments_df = segments_df.dropna()
        segments_df["max_speed"] = scaler.fit_transform(segments_df[["max_speed"]])
        segments_df["variation"] = scaler.fit_transform(segments_df[["variation"]])
        segments_df["day_of_week"] = scaler.fit_transform(segments_df[["day_of_week"]])
        segments_df["hour_of_day"] = scaler.fit_transform(segments_df[["hour_of_day"]])
        return gps_data_df, segments_df
