import pandas as pd
import os

def save_data(df, path, filename):

    if not os.path.exists(path):
        os.makedirs(path)
    df.to_csv(os.path.join(path, filename), index=False)
