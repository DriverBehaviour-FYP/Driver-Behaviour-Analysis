import pandas as pd


def get_data_from_path(path):
    """
    Get csv file from given file path.

    Args:
        path (str): Location for the file.

    Returns:
        data (pd.DataFrame): A DataFrame Object of given file path.
    """

    data = pd.read_csv(path)
    return data
