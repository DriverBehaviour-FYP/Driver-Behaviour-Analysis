from utils.local.retrieve_data import get_data_from_path
from components.preprocessing.cleaner import Cleaner
from components.preprocessing.dropper import Dropper
from components.preprocessing.trip_extractor import TripExtractor
from components.preprocessing.trip_segmeter import TripSegmenterByTime
from components.preprocessing.elevation_injector import ElevationInjector
from components.preprocessing.feature_calculator import FeatureCalculator
from components.preprocessing.standardizer import Standardizer
from components.preprocessing.acceleration_calculator import AccelerationCalculator
from sklearn.pipeline import Pipeline

global previous_trip_max, previous_segment_max, month_pointer, bus_terminals, path_to_temp

if __name__ == '__main__':
    DEVICE = 'LOCAL'    # both 'LOCAL' and 'COLAB' available
    dataset_names = ["digana_2021_10.csv","digana_2021_11.csv","digana_2021_12.csv","digana_2022_01.csv","digana_2022_02.csv","digana_2022_07.csv","digana_2022_08.csv","digana_2022_09.csv","digana_2022_10.csv"]

    rootPath = None
    if DEVICE=='COLAB':
        rootPath = '/content/drive/MyDrive/Data_sets/'
    else:
        rootPath = './data/'

    path_bus_terminals = rootPath + 'Raw-GPS-data-Kandy-Buses/more/bus_terminals_654.csv'
    path_to_temp = rootPath + 'Raw-GPS-data-Kandy-Buses/MAIN/TEMP/'


    # load the raw data and the bus terminals
    # raw_data = get_data_from_drive(path_raw_data)
    bus_terminals = get_data_from_path(path_bus_terminals)
    
    previous_trip_max = 0
    previous_segment_max = 0
    for ds in range(len(dataset_names)):
        path_raw_data = rootPath + 'Raw-GPS-data-Kandy-Buses/' + dataset_names[ds]
        month_pointer = dataset_names[ds].split(".")[0]
        print("---------------------------------------------------", month_pointer, "------------------------------------------------")
        raw_data = get_data_from_path(path_raw_data)
        
        # config pipeline
        pipe = Pipeline([
            ("cleaner", Cleaner(month_pointer)),
            ("dropper", Dropper(month_pointer, path_to_temp)),   # need a saving point here
            ("TripExtractor", TripExtractor(month_pointer, path_to_temp, previous_trip_max, bus_terminals )),   # need a saving point
            ("InjectElevations",ElevationInjector(month_pointer, path_to_temp)),  # save point there
            ("TripSegmentor", TripSegmenterByTime(month_pointer, path_to_temp, previous_segment_max )),   # need a saving point
            # ("CalculateFeatures", CalculateFeatures()),
            ("AccelerationCalculator", AccelerationCalculator(month_pointer,path_to_temp)),
        ])

        gps_data, segments, bus_trips = pipe.fit_transform(raw_data)
        previous_trip_max += len(bus_trips)
        previous_segment_max += len(segments)