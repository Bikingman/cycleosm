import csv
import geopandas as gpd
from process_national_osm.python.utils import Utils
import os 
from numpy import where

# general TODO - write data type validations 
class Roads(Utils):
    def __init__(self):
        super(Roads, self).__init__()
 
        with open(os.path.join( os.path.dirname(__file__), 'static', 'error_message.txt')) as f:
            self.validatition_error_string = f.readlines()

        with open(os.path.join( os.path.dirname(__file__), 'static', 'fclass_to_lanes.csv')) as f:
            self.lanes_count_dict = {rows[0].replace("\xa0", ""):int(rows[1]) for rows in csv.reader(f)} 

        with open(os.path.join( os.path.dirname(__file__), 'static', 'lanes_to_width.csv')) as f:
            self.width_dict = {rows[0].replace("\xa0", ""):int(rows[1]) for rows in csv.reader(f)} 

    def _checks(self, object, check_gpds=True, check_dict=None, _dict=None, cols_exists=[], cols_d_exist = []):
        checks = []
        if check_gpds:
            if (self._check_gpds(object)):
                checks.append(True)
                if len(cols_exists) > 0:
                    for i in cols_exists:
                        checks.append(self._check_col_exists(object.columns, i)) 

                if len(cols_d_exist) > 0:
                    for i in cols_d_exist:
                        checks.append(self._check_col_dont_exists(object.columns, i)) 
            else:
                print('The object you identified is not a geopandas dataframe')
                checks.append(False)
        if check_dict:
            checks.append(self._check_is_dict(_dict))
        return(checks)


    def infer_lanes_from_fclass(self, roads, new_lns_col, cur_lns_col, one_way_col, fclass_col, lanes_count_dict={}):
        """
        Purpose: generic function for inferring number of lanes by functional classification 
        """

        if not any(self._checks(roads, 
                                cols_exists=self._get_existing_cols_to_check([fclass_col, one_way_col], [cur_lns_col]), 
                                cols_d_exist=[new_lns_col], 
                                _dict=lanes_count_dict,
                                check_dict=self._confirm_dict_not_empty(lanes_count_dict)
                                )):
            raise ValueError(self.validatition_error_string)

        if self._confirm_dict_not_empty(lanes_count_dict):
            self.lanes_count_dict = lanes_count_dict

        # define lanes 
        if cur_lns_col is not None: 
            roads[new_lns_col] = where(~roads[cur_lns_col].isnull(), roads[cur_lns_col], where(roads[one_way_col]=='yes',  roads[fclass_col].map(self.lanes_count_dict)*1, roads[fclass_col].map(self.lanes_count_dict)*2))
            try:
                roads[new_lns_col] = roads[new_lns_col].astype(int)
            except:
                roads[new_lns_col] = roads[fclass_col].map(self.lanes_count_dict) # some are characters strings
        else:
            roads[new_lns_col] = roads[fclass_col].map(self.lanes_count_dict)

        return (roads)

    def infer_width_from_lanes(self, roads, lanes_col,  new_width_col, fclass_col, cur_width_col=None, width_dict={}):


        if not any(self._checks(roads, 
                                cols_exists=self._get_existing_cols_to_check([lanes_col, fclass_col], [cur_width_col]), 
                                cols_d_exist=[new_width_col], 
                                _dict=width_dict,
                                check_dict=self._confirm_dict_not_empty(width_dict))):
            raise ValueError(self.validatition_error_string)

        # define lanes 
        if cur_width_col is not None: 
            roads[new_width_col] = roads[cur_width_col].apply(lambda x: cur_width_col if x is not None else roads[lanes_col].map(self.width_dict))
            roads[new_width_col] = self.feet_to_meters(roads[new_width_col])

        else:
            roads[new_width_col] = roads[fclass_col].map(self.width_dict)*roads[lanes_col]
            roads[new_width_col] = self.feet_to_meters(roads[new_width_col])

        return (roads)

    def buffer_roads(self, roads, width_col, convert_to_utm=False, capped_lines=True):
        if not any(self._checks(roads, cols_exists=[width_col, 'geometry'])):
            raise ValueError(self.validatition_error_string)

        if convert_to_utm:
            roads = self.convert_to_utm(roads)

        if capped_lines:
            roads['geometry'] = roads.apply(lambda row: (row['geometry'].buffer(row[width_col]/2, cap_style=2)), axis=1)
        else:
            roads['geometry'] = roads.apply(lambda row: (row['geometry'].buffer(row[width_col]/2)), axis=1)

        return(roads)

