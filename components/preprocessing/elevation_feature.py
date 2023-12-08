from sklearn.base import BaseEstimator, TransformerMixin
from utils.local.save_data import save_data
from math import radians, cos, sin, asin, sqrt

class ElevationForSegment( BaseEstimator, TransformerMixin):

  def __init__(self, month_pointer, path_to_temp, seg_pointer):
    self.month_pointer = month_pointer
    self.path_to_temp = path_to_temp
    self.seg_pointer = seg_pointer

  def fit(self, X, y=None):
    return self


  def transform(self, X):
    print(f"**************************** Elevation For Segment {self.month_pointer}")
    gps_data,segments_ts = X

    segment_id_list = segments_ts['segment_id'].unique()

    elevation_p=[] #avg positive elevation for segments
    elevation_n=[] #avg negative elevation for segments
    ac_elevation_p=[] #accumilated positive sum of elevation angle X avg speed of adjest two points
    ac_elevation_n=[] #accumilated negative sum of elevation angle X avg speed of adjest two points

    for segment_id in segment_id_list:
      sum_elevation_p=0
      ac_sum_elevation_p=0
      sum_elevation_n=0
      ac_sum_elevation_n=0
      count_p=0
      count_n=0
      select_segment = gps_data[gps_data['segment_id'] == segment_id].reset_index()

      for i in range(len(select_segment)-1):
        elevation = select_segment['elevation'][i+1]-select_segment['elevation'][i]
        displacement = self.distance(select_segment['latitude'][i+1],select_segment['latitude'][i],select_segment['longitude'][i+1],select_segment['longitude'][i])
        if(elevation != 0 and displacement!=0):
        #   angle_sin = elevation/(math.sqrt(displacement**2+elevation**2))
          angle_tan = elevation/displacement
          if(angle_tan>0):
            sum_elevation_p+=angle_tan
            ac_sum_elevation_p+=angle_tan*(select_segment['speed'][i+1]+select_segment['speed'][i])/2
            count_p+=1
          elif(angle_tan<0):
            sum_elevation_n+=angle_tan
            ac_sum_elevation_n+=abs(angle_tan)*(select_segment['speed'][i+1]+select_segment['speed'][i])/2
            count_n+=1


      elevation_p.append(sum_elevation_p/count_p if count_p!=0 else 0)
      elevation_n.append(sum_elevation_n/count_n if count_n!=0 else 0)
      ac_elevation_p.append(ac_sum_elevation_p)
      ac_elevation_n.append(ac_sum_elevation_n)

    segments_ts["elevation_p"]=elevation_p
    segments_ts["elevation_n"]=elevation_n
    segments_ts["ele_X_speed_acc_p"]=ac_elevation_p
    segments_ts["ele_X_speed_acc_n"]=ac_elevation_n

    save_data(gps_data, self.path_to_temp + "EL_FC/" + self.seg_pointer +"/" , self.month_pointer + "_gps_data.csv")
    save_data(segments_ts, self.path_to_temp + "EL_FC/" + self.seg_pointer +"/" , self.month_pointer + "_segments.csv")
    
     
    return gps_data,segments_ts

  def distance(self, lat1, lat2, lon1, lon2):
     
    # The math module contains a function named
    # radians which converts from degrees to radians.
    lon1 = radians(lon1)
    lon2 = radians(lon2)
    lat1 = radians(lat1)
    lat2 = radians(lat2)
      
    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
 
    c = 2 * asin(sqrt(a)) 
    
    # Radius of earth in kilometers. Use 3956 for miles
    r = 6371
      
    # calculate the result
    return(c * r*1000)


  