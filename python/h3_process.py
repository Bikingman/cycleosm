import h3
import pandas as pd 
import geopandas as gpd
from utils import Utils
from shapely.geometry import Polygon

class HandleH3(Utils):
    def __init__(self):
        super(HandleH3, self).__init__()

    def _get_h3_list(self, row, resolution):
        return([h3.polyfill(row.geometry.__geo_interface__, resolution, geo_json_conformant = True)])

    def _polygon_row_get_inner_h3_id(self, row, resolution):

        roads_h3id = []
        for i in self._get_h3_list(row, resolution):
            for j in i:
                roads_h3id.append(( row.id, j))
        return roads_h3id

    def ignore_exception(self, func, row, resolution):
        """Define a helper function.
        """
        try:
            return func(row, resolution)
        except:
            pass

    def _get_inner_h3(self, roads, resolution):
        return(roads.apply(lambda row: (self.ignore_exception(self._polygon_row_get_inner_h3_id, row, resolution)), axis=1))

    def h3_to_parent(self, hex, resolution):
        return(h3.h3_to_parent(hex, resolution))

    def _return_clean_h3_index(self, gpd_df, resolution):
        df = []
        for i in self._get_inner_h3(gpd_df, resolution):
            if i is not None: # TODO look into why this is required 
                for j in i:
                    df.append({'feature_id': j[0], 'h3_index_lv'+str(resolution):h3.string_to_h3(j[1])})
        return(pd.DataFrame(df, columns=['feature_id', 'h3_index_lv'+str(resolution)]))

    def get_h3_index(self, gpd_df, list_of_resolutions, list_of_summary_hex):
        table = pd.DataFrame()
        for i, v in enumerate(list_of_resolutions):
            if i == 0:
                table = self._return_clean_h3_index(gpd_df, v)
                if len(list_of_resolutions) == 0:
                    if len(list_of_summary_hex) != 0:
                        for k in list_of_summary_hex:
                            table['summary_hex_lv'+str(k)] = table.apply(lambda row: (h3.string_to_h3(h3.h3_to_parent(h3.h3_to_string(row['h3_index_lv'+str(v)]), k))), axis=1)
                    return(table)
            else:
                holding_table = self._return_clean_h3_index(gpd_df, v)
                if len(holding_table) == 0:
                    print('No h3 indexes at level ' + str(v) +' were found for your geopandas dataframe.')
                else:
                    table = pd.merge(table, holding_table, on='feature_id')
        if len(list_of_summary_hex) != 0:
                        for k in list_of_summary_hex:
                            table['summary_hex_lv'+str(k)] = table.apply(lambda row: (h3.string_to_h3(h3.h3_to_parent(h3.h3_to_string(row['h3_index_lv'+str(v)]), k))), axis=1)
        return table

    def get_hex_layer(self, hexes):

        layer = {'type':'FeatureCollection', 'features':[]}
        for hex_ in hexes:

            f = {"type":"Feature", "geometry":{"type":"Polygon", "coordinates":{}}}
            f["id"] = hex_ 
            f['properties'] = {}
            f['geometry']['coordinates'] = [h3.h3_to_geo_boundary(h3.h3_to_string(hex_), geo_json=True)]

            layer['features'].append(f)

        return layer

    def get_hex_df(self, hexes):

        hex_layer = self.get_hex_layer(hexes)

        hex_df = gpd.GeoDataFrame(data=hexes, 
                geometry=[Polygon(p['geometry']['coordinates'][0]) for p in hex_layer['features']],
                            columns=['hex'])

        hex_df = hex_df.set_crs(epsg=4326) 

        return hex_df