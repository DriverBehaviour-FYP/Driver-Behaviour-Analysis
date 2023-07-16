from sklearn.base import BaseEstimator, TransformerMixin
from datetime import datetime, date
import pandas as pd
import geopandas as gpd
import numpy as np


class TripExtractor(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        end_buffer = 100
        gps_data, bus_terminals = X
        trip_ends = self.trip_ends_extraction(gps_data, bus_terminals, end_buffer)
        bus_trips = self.trip_extraction(trip_ends)
        gps_data_2 = self.filter_all(gps_data, trip_ends)
        return gps_data_2, bus_trips  # returns gps_data dataframe with trip ids, and bus_trips dataframe

    def trip_ends_extraction(self, gps_data, bus_terminals, end_buffer):

        """
        To extract trip ends dataframe with given buffer range.
        Filter the records within terminals selected buffer range.
        Within the filtered records get entry & exit to terminals.


        Args:
            gps_data (pd.DataFrame): Cleaned gps data filtered out from the server for the required time window.
            bus_terminals (pd.DataFrame): End and start terminals for the trip.
            end_buffer (int):  Radius of the buffer area to represent terminals.

        Returns:
            trip_ends (pd.DataFrame): Trip data with extracted terminals.
      """

        # converting to GeoDataframe with Coordinate Reference system 4326
        gps_data = gpd.GeoDataFrame(gps_data, geometry=gpd.points_from_xy(gps_data.longitude, gps_data.latitude),
                                    crs='EPSG:4326')
        bus_terminals = gpd.GeoDataFrame(bus_terminals,
                                         geometry=gpd.points_from_xy(bus_terminals.longitude, bus_terminals.latitude),
                                         crs='EPSG:4326')

        # project them in local cordinate system
        gps_data = gps_data.to_crs('EPSG:5234')
        bus_terminals = bus_terminals.to_crs('EPSG:5234')

        # creating buffer area to extract records around bus terminals
        bus_terminals_buffer = gpd.GeoDataFrame(bus_terminals, geometry=bus_terminals.geometry.buffer(end_buffer))

        # filtering coordinates within bus terminals end buffer
        gps_data['bus_stop'] = pd.Series(dtype='object')  # create a new column in gps data set
        gps_data.reset_index(drop=True, inplace=True)  # reset indices to run a for loop

        for i in range(len(gps_data)):
            for stop in range(len(bus_terminals)):
                if bus_terminals_buffer.iloc[stop].geometry.contains(gps_data.iloc[i].geometry):
                    gps_data.at[i, 'bus_stop'] = bus_terminals.at[stop, 'terminal_id']

        trip_ends = gps_data.dropna()  # filter records within terminal buffer

        # EXTRACT TRIP ENDS

        # grouping the filtered records of one bus terminal and one date
        trip_ends['grouped_ends'] = ((trip_ends['bus_stop'].shift() != trip_ends['bus_stop']) | (
                trip_ends['date'].shift() != trip_ends['date'])).cumsum()

        # find the entry or exit record only of the terminals
        # Early records is the entry(1) to the terminal and last record as the exit(0) to the end terminal
        trip_ends['entry/exit'] = pd.Series(dtype='object')
        trip_ends = trip_ends.reset_index(drop=True)

        for name, group in trip_ends.groupby('grouped_ends'):
            # if 0 in group['speed'].values:
            for index, row in group.iterrows():
                if row['devicetime'] == group['devicetime'].max():
                    trip_ends.at[index, 'entry/exit'] = '0'
                elif row['devicetime'] == group['devicetime'].min():
                    trip_ends.at[index, 'entry/exit'] = '1'

        trip_ends = trip_ends.dropna()  # filter terminal entry/exit records only

        trip_ends = trip_ends.reset_index(drop=True)

        # Providing unique trip id for trips which have entry / exit values within the 2 bus end terminals
        trip = 0
        for i in range(len(trip_ends) - 1):
            if (trip_ends.at[i, 'bus_stop'] != trip_ends.at[i + 1, 'bus_stop']) & (
                    trip_ends.at[i, 'date'] == trip_ends.at[i + 1, 'date']):
                trip = trip + 1
                trip_ends.at[i, 'trip_id'] = trip
                trip_ends.at[i + 1, 'trip_id'] = trip

        trip_ends = trip_ends.dropna()

        trip_ends = trip_ends.groupby('trip_id').filter(
            lambda x: len(x) > 1)  # remove outliers where no defined 2 trip ends for a trip
        trip_ends = trip_ends.reset_index(drop=True)

        return trip_ends

    def trip_extraction(self, trip_ends):

        """
        To extract bus trips with derived columns.
        Create end_time, end_terminal for a bus trip.
        Create features of duration, duration_in_mins, day_of_the_week, hour_of_day

        Args:
            trip_ends (pd.DataFrame): Filtered bus trip data with terminals.

        Returns:
            bus_trips (pd.DataFrame): Bus trip terminals data with derived features.
      """

        bus_trips = trip_ends.copy()
        bus_trips[['end_time', 'end_terminal']] = bus_trips[['time', 'bus_stop']].shift(-1)
        bus_trips = bus_trips.iloc[::2]

        bus_trips = bus_trips.drop(
            ['id', 'devicetime', 'latitude', 'longitude', 'speed', 'geometry', 'grouped_ends', 'entry/exit'], axis=1)
        bus_trips.insert(0, 'trip_id', bus_trips.pop('trip_id'))
        bus_trips.rename(columns={'time': 'start_time', 'bus_stop': 'start_terminal'}, inplace=True)

        conditions = [(bus_trips['start_terminal'] == 'BT01'),
                      (bus_trips['start_terminal'] == 'BT02')]
        values = [1, 2]

        bus_trips['direction'] = np.select(conditions, values)

        bus_trips = bus_trips[
            ['trip_id', 'deviceid', 'date', 'start_terminal', 'end_terminal', 'direction', 'start_time', 'end_time']]
        bus_trips = bus_trips.reset_index(drop=True)

        # Calculate trip duration
        bus_trips['duration'] = pd.Series(dtype='object')
        for i in range(len(bus_trips)):
            bus_trips.at[i, 'duration'] = datetime.combine(date.min, bus_trips.at[i, 'end_time']) - datetime.combine(
                date.min, bus_trips.at[i, 'start_time'])

        bus_trips['duration_in_mins'] = bus_trips['duration'] / np.timedelta64(1, 'm')

        bus_trips['day_of_week'] = pd.to_datetime(bus_trips['date']).dt.weekday
        bus_trips['hour_of_day'] = list(map(lambda x: x.hour, (bus_trips['start_time'])))

        return bus_trips

    def filter_all(self, gps_data, trip_ends):
        """

        To extract all correct data raw point
        from start point to ent point.
        Args:
            gps_data (pd.DataFrame): Cleaned gps data filtered out from the server for the required time window.
            trip_ends (pd.DataFrame): Filtered bus trip data with terminals.

        Returns:
          row_bus_data (pd.DataFrame): all correct data raw point from start point to ent point..
      """
        pointer = 0
        new_gps_data = []
        new_columns = ['id', 'deviceid', 'devicetime', 'latitude', 'longitude', 'speed', 'date', 'time', 'trip_id']
        index_num = 0
        for index, row in gps_data.iterrows():
            # print(index_num,":",row['deviceid'],":",pointer)
            if datetime.strptime(trip_ends.loc[pointer, 'devicetime'], "%Y-%m-%d %H:%M:%S") <= datetime.strptime(
                    row['devicetime'], "%Y-%m-%d %H:%M:%S") <= datetime.strptime(
                trip_ends.loc[pointer + 1, 'devicetime'],
                "%Y-%m-%d %H:%M:%S"):
                new_row = [row['id'], row['deviceid'], row['devicetime'], row['latitude'], row['longitude'],
                           row['speed'],
                           row['date'], row['time'], trip_ends.loc[pointer, 'trip_id']]
                new_gps_data.append(new_row)
                # print(row['id'],":",row['id'] == trip_ends.loc[pointer+1,'id']," ",pointer+2)
                if row['id'] == trip_ends.loc[pointer + 1, 'id']:
                    pointer += 2
                    if (pointer == len(trip_ends)):
                        break
                    # print("pointer:",pointer+2)
                    # print(trip_ends.loc[pointer,'id'])
            index_num += 1
        new_gps_data = pd.DataFrame(new_gps_data, columns=new_columns)
        return new_gps_data
