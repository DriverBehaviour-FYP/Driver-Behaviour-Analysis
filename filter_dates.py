from utils.local.retrieve_data import get_data_from_path
from utils.local.save_data import save_data
from components.preprocessing.segment_filter import SegmentFilter

if __name__ == '__main__':
    version = '10T'
    gps_data = get_data_from_path(f"./data/Raw-GPS-data-Kandy-Buses/MAIN/OUTPUTS/merged_gps_data_{version}.csv")
    trips_data = get_data_from_path(f"./data/Raw-GPS-data-Kandy-Buses/MAIN/OUTPUTS/merged_trips_data.csv")
    segments_data = get_data_from_path(f"./data/Raw-GPS-data-Kandy-Buses/MAIN/OUTPUTS/merged_segments_{version}.csv")

    filter = SegmentFilter()

    gps_data, trips_data, segments_data = filter.fit_transform((gps_data, trips_data, segments_data))

    save_data(gps_data, f"./data/Raw-GPS-data-Kandy-Buses/MAIN/OUTPUTS/FINAL/", f"merged_gps_data_{version}.csv")
    save_data(trips_data, f"./data/Raw-GPS-data-Kandy-Buses/MAIN/OUTPUTS/FINAL/", "merged_trips_data.csv")
    save_data(segments_data, f"./data/Raw-GPS-data-Kandy-Buses/MAIN/OUTPUTS/FINAL/", f"merged_segments_data_{version}.csv")

    
