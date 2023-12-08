import pandas as pd
from utils.local.save_data import save_data
import os

def stack_files(filesPath, savePath, fileName, commonWord):
    files = os.listdir(path=filesPath)
    dfs = []
    for f in files:
        if commonWord in f:
            dfs.append(pd.read_csv(filesPath+f))
    if len(dfs)>0:
        merged = pd.concat(dfs, axis=0)
        save_data(merged, savePath, fileName)
        return True
    else:
        return False
