from sklearn.base import BaseEstimator, TransformerMixin
from datetime import datetime, date
import pandas as pd
import numpy as np
from pyproj import Proj, Transformer
from math import cos, radians, sqrt

def calculate_radius_of_curvature(x1, y1, x2, y2, x3,y3):
    x12 = x1 - x2;
    x13 = x1 - x3;

    y12 = y1 - y2;
    y13 = y1 - y3;

    y31 = y3 - y1;
    y21 = y2 - y1;

    x31 = x3 - x1;
    x21 = x2 - x1;

    # x1^2 - x3^2
    sx13 = pow(x1, 2) - pow(x3, 2);

    # y1^2 - y3^2
    sy13 = pow(y1, 2) - pow(y3, 2);

    sx21 = pow(x2, 2) - pow(x1, 2);
    sy21 = pow(y2, 2) - pow(y1, 2);

    denominator = 2 * ((y31) * (x12) - (y21) * (x13))

    # Avoid division by zero
    if denominator == 0:
        return 0  # Or some other value you want to use

    f = (((sx13) * (x12) + (sy13) *
          (x12) + (sx21) * (x13) +
          (sy21) * (x13)) // denominator)

    g = (((sx13) * (y12) + (sy13) * (y12) +
          (sx21) * (y13) + (sy21) * (y13)) //
          (2 * ((x31) * (y12) - (x21) * (y13))));

    c = (-pow(x1, 2) - pow(y1, 2) -
         2 * g * x1 - 2 * f * y1);

    # eqn of circle be x^2 + y^2 + 2*g*x + 2*f*y + c = 0
    # where centre is (h = -g, k = -f) and
    # radius r as r^2 = h^2 + k^2 - c
    h = -g;
    k = -f;
    sqr_of_r = h * h + k * k - c;

    # r is the radius
    r = round(sqrt(sqr_of_r), 5);
    return r

# Calculate radial acceleration based on speed and radius of curvature
def calculate_radial_acceleration(speed, radius_of_curvature):
    if radius_of_curvature != 0:
        radial_acceleration = speed**2 / radius_of_curvature
    else:
        radial_acceleration = 0
    return radial_acceleration

def lat_lon_to_utm(lat, lon):
    # Create a UTM projection for the appropriate UTM zone (Zone 44N for Sri Lanka)
    utm_zone = 44
    utm_proj = Proj(proj='utm', zone=utm_zone, ellps='WGS84')

    # Convert latitude and longitude to UTM coordinates
    utm_easting, utm_northing = utm_proj(lon, lat)
    return utm_easting, utm_northing

# put your calculate_radial_acceleration_for_trip here
class CalculateRadialAcceleration(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        gps_data_ts, segments_ts = X
        segment_id_list = segments_ts['segment_id'].unique()
        trip_id_list = gps_data_ts['trip_id'].unique()

        window_size = 1

        gps_data_df = gps_data_ts.copy()
        segments_df = segments_ts.copy()

        radial_acceleration_list_f = []

        for trip_id in trip_id_list:
            trip_df = gps_data_ts[gps_data_ts['trip_id'] == trip_id]

            radial_acceleration_list = []
            for i in range(window_size, len(trip_df) - window_size):
              lat1, lon1 = trip_df.iloc[i - window_size]["latitude"], trip_df.iloc[i - window_size]["longitude"]
              lat2, lon2 = trip_df.iloc[i]["latitude"], trip_df.iloc[i]["longitude"]
              lat3, lon3 = trip_df.iloc[i + window_size]["latitude"], trip_df.iloc[i + window_size]["longitude"]

              x1, y1 = lat_lon_to_utm(lat1, lon1)
              x2, y2 = lat_lon_to_utm(lat2, lon2)
              x3, y3 = lat_lon_to_utm(lat3, lon3)

              radius_of_curvature = calculate_radius_of_curvature(x1, y1, x2, y2, x3, y3)


              if i <= window_size:
                for j in range(0,window_size+1):
                  speed = trip_df.iloc[j]["speed"]
                  radial_acceleration = calculate_radial_acceleration(speed, radius_of_curvature)
                  radial_acceleration_list.append(radial_acceleration)

              elif i == len(trip_df) - window_size - 1:
                for j in range(0,window_size+1):
                  speed = trip_df.iloc[i+j]["speed"]
                  radial_acceleration = calculate_radial_acceleration(speed, radius_of_curvature)
                  radial_acceleration_list.append(radial_acceleration)

              else:
                speed = trip_df.iloc[i]["speed"]
                radial_acceleration = calculate_radial_acceleration(speed, radius_of_curvature)
                radial_acceleration_list.append(radial_acceleration)

            radial_acceleration_list_f.extend(radial_acceleration_list)
            # if(len(trip_df)!=len(radial_acceleration_list)):
            #   print(trip_id)
            #   break

        gps_data_df["radial_acceleration"] = radial_acceleration_list_f
        # print("pass")
        radial_acceleration_avg_list = []

        for segment_id in segment_id_list:
            select_segment = gps_data_df[gps_data_df['segment_id'] == segment_id]
            radial_acceleration_in_seg = select_segment['radial_acceleration'].tolist()
            average_radial_acceleration_in_seg = sum(radial_acceleration_in_seg) / len(radial_acceleration_in_seg)

            radial_acceleration_avg_list.append(average_radial_acceleration_in_seg)

        segments_df['avg_radial_acceleration'] = radial_acceleration_avg_list

        return gps_data_df, segments_df