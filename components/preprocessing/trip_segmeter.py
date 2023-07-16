from sklearn.base import BaseEstimator, TransformerMixin
import pandas as pd
from datetime import datetime, timedelta


class TripSegmenter(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        gps_data_ts, bus_trips_ts = X
        new_records = []  # List to store the split records
        for index, row in bus_trips_ts.iterrows():
            duration = row['duration_in_mins']

            date_string = f"{row['date']} {row['start_time']}"
            format_string = "%Y-%m-%d %H:%M:%S"
            parsed_date = datetime.strptime(date_string, format_string)
            start_time = pd.Timestamp(parsed_date)

            # Generate a range of 3-minute intervals for the current record
            time_intervals = pd.date_range(start=start_time, periods=duration, freq='3T')

            # Iterate over the time intervals and create a new record for each interval
            for interval in time_intervals:
                end_time = interval + timedelta(minutes=3)
                new_record = {
                    'segment_starting_time': pd.to_datetime(interval),
                    'segment_ending_time': pd.to_datetime(end_time),
                    'trip_id': row['trip_id'],
                    'deviceid': row['deviceid'],
                    'date': row['date'],
                    'start_terminal': row['start_terminal'],
                    'end_terminal': row['end_terminal'],
                    'direction': row['direction'],
                    'day_of_week': row['day_of_week'],
                    'hour_of_day': row['hour_of_day']
                }
                new_records.append(new_record)

        # Create a new DataFrame from the split records
        segments_df = pd.DataFrame(new_records)
        segments_df['segment_id'] = [i for i in range(1, len(segments_df) + 1)]

        # add the segment id to the GPS data
        segment_ids = []
        for index, row in gps_data_ts.iterrows():
            device_time = pd.to_datetime(row['devicetime'])
            device_id = row['deviceid']
            temp_df1 = segments_df[(segments_df["segment_starting_time"] <= device_time) & (
                        segments_df["segment_ending_time"] > device_time)]
            temp_df2 = temp_df1[temp_df1["deviceid"] == device_id]
            if len(temp_df2) > 0:
                segment_ids_temp = temp_df2['segment_id'].values
                segment_id = segment_ids_temp[0]
            else:
                segment_id = None
            segment_ids.append(segment_id)

        gps_data_ts["segment_id"] = segment_ids
        return gps_data_ts, segments_df
