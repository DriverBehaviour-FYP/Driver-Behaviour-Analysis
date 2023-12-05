from sklearn.base import BaseEstimator, TransformerMixin


class Dropper( BaseEstimator, TransformerMixin):
  
  def __init__(self, month_pointer, path_to_temp):
    self.month_pointer = month_pointer
    self.path_to_temp = path_to_temp

  def fit(self, X, y=None):
    return self

  def transform(self, X):
    print(f"****************************Dropping {self.month_pointer}")
    additional_columns = ['servertime','fixtime','address','routeid']
    dropped_df = X.drop(additional_columns, axis=1)
    dropped_df.to_csv( self.path_to_temp + "CL_DR/"+ self.month_pointer + "_C_D.csv", index = False)
    return dropped_df
