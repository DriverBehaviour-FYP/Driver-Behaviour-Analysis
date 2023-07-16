from utils.local.retrieve_data import get_data_from_path
from components.preprocessing.cleaner import Cleaner
from components.preprocessing.dropper import Dropper
from components.preprocessing.trip_extractor import TripExtractor
from components.preprocessing.trip_segmeter import TripSegmenter
from components.preprocessing.feature_calculator import FeatureCalculator
from components.preprocessing.standardizer import Standardizer
from sklearn.pipeline import Pipeline

if __name__ == '__main__':
    path_raw_data = './data/Raw-GPS-data-Kandy-Buses/digana_2021_10.csv'
    path_bus_terminals = './data/Raw-GPS-data-Kandy-Buses/more/bus_terminals_654.csv'

    # load the raw data and the bus terminals
    raw_data = get_data_from_path(path_raw_data)
    bus_terminals = get_data_from_path(path_bus_terminals)

    # configure the pipeline
    pipe = Pipeline([
        ("cleaner", Cleaner()),
        ("dropper", Dropper()),
        ("TripExtractor", TripExtractor()),
        ("TripSegmentor", TripSegmenter()),
        ("featureCalculator", FeatureCalculator()),
        ("Standardizer", Standardizer())
    ])
    gps_data, bus_segments = pipe.fit_transform((raw_data, bus_terminals))
    print(gps_data.head(10))
    print("------------------------")
    print(gps_data.head(10))
