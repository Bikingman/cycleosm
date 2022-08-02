
import math
import geopandas as gpd
# from sqlalchemy import create_engine

class Utils():
    def __init__(self):
        super(Utils, self).__init__()

    def feet_to_meters(self, feet):
        return(round(feet/3.28084, 2))

    def get_utm_epsg(self, lat, lng):
        utm_band = str( (math.floor((lng + 180 ) / 6 ) % 60) + 1)
        if len(utm_band) == 1:
            utm_band = '0' + utm_band
        if lat >= 0:
            epsg = '326' + utm_band
        else:
            epsg = '327' + utm_band
        return(epsg)

    def convert_to_utm(self, object):
        # confirm dataframe is a gpds 
        if not isinstance(object, gpd.GeoDataFrame):
            raise ValueError('Your roads object is not a GeoPandas Dataframe.')
        cent_lat = sum(object.centroid.y)/len(object.centroid.y)
        cent_lng = sum(object.centroid.x)/len(object.centroid.x)
        utm = self.get_utm_epsg(cent_lat, cent_lng)
        return(object.to_crs(int(utm)))

    def _check_gpds(self, object):
        if isinstance(object, gpd.GeoDataFrame):
            return(True)
        else:
            return(False)

    def _check_is_dict(self, dict):
        if isinstance(object, dict):
            return(True)
        else:
            return(False)

    def _check_col_exists(self, columns, col):
        if col in columns:
            return(True)
        else:
            return(False)    

    def _check_col_dont_exists(self, columns, col):
        if col not in columns:
            return(True)
        else:
            return(False)    

    def _confirm_dict_not_empty(self, _dict):
        if len(_dict) > 0:
            return True
        else:
            return False

    def _get_existing_cols_to_check(self, known_cols=[], unknown_cols=[]):
        cols_exists = known_cols
        for i in unknown_cols:
            if i is not None:
                cols_exists.append(i)
        return cols_exists


    # TODO write utilities to connect to postgresql 
    # def make_connection(user, password, host, db):
    #     # connect to db
    #     return(create_engine('postgresql://{0}:{1}@{2}:5432/{db}'.format(user, password, host, db)))



