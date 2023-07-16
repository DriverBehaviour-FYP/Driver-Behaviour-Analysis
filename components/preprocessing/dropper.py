from sklearn.base import BaseEstimator, TransformerMixin


class Dropper(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        gps_data_df, terminals_df = X
        additional_columns = ['servertime', 'fixtime', 'address', 'routeid']
        return gps_data_df.drop(additional_columns, axis=1), terminals_df
