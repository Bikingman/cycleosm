import h3
import pandas as pd 
import geopandas as gpd
from utils import Utils
from shapely.geometry import Polygon

class HandleH3(Utils):
    def __init__(self):
        super(HandleH3, self).__init__()

    def _get_h3_list(self, feature, resolution):
        """
        Retreives h3 object that fills polygons 

        Parameters
        ----------
        feature : gpds
            geopandas feature

        resolution : int
            h3 index resolution 

        Returns
        -------
        list
            h3 object of h3 indexes for given polygon feature 

        """
        return([h3.polyfill(feature.geometry.__geo_interface__, resolution, geo_json_conformant = True)])

    def _polygon_row_get_inner_h3_id(self, feature, resolution):
        """
        Retreives list of h3 indexes that fills polygon 

        Parameters
        ----------
        feature : gpds
            geopandas feature

        resolution : int
            h3 index resolution 

        Returns
        -------
        list
            list of h3 indexes for given polygon feature 

        """
        roads_h3id = []
        for i in self._get_h3_list(feature, resolution):
            for j in i:
                roads_h3id.append(( feature.id, j))
        return roads_h3id

    def _ignore_road(self, func, gpd_df, resolution):
        """
        Sometimes no h3 index can be returned when fetching inner h3 id. This function handles that problem.

        Parameters
        ----------
        func : function
            a function 

        gpd_df : int
            geopandas dataframe

        resolution : int
            h3 index resolution 


        """
        try:
            return func(gpd_df, resolution)
        except:
            pass

    def _get_inner_h3(self, gpd_df, resolution):
        """
        Retreives list of h3 indexes that fill polygons

        Parameters
        ----------
        gpd_df : int
            geopandas dataframe

        resolution : int
            h3 index resolution   

        Returns
        -------
        geopandas df
            geopandas dataframe with h3 indexes for given resolution

        """
        return(gpd_df.apply(lambda row: (self._ignore_road(self._polygon_row_get_inner_h3_id, row, resolution)), axis=1))

    def _h3_to_parent(self, hex, resolution):
        """
        Returns the parent hex id of given child hex id

        Parameters
        ----------
        hex : int
            h3 hex id

        resolution : int
            parent resolution    

        Returns
        -------
        int
            parent h3 hex id for given resolution

        """
        return(h3.h3_to_parent(hex, resolution))

    def _return_clean_h3_index(self, gpd_df, resolution):
        """
        This function returns a pandas dataframe of osm feature ids and single h3 hex id .

        Parameters
        ----------
        gpd_df : int
            geopandas dataframe

        resolution : int
            h3 index resolution       

        Returns
        -------
        pandas df
            dataframe of osm feature ids with h3 index ids

        """
        df = []
        for i in self._get_inner_h3(gpd_df, resolution):
            if i is not None: # TODO look into why this is required 
                for j in i:
                    df.append({'feature_id': j[0], 'h3_index_lv'+str(resolution):h3.string_to_h3(j[1])})
        return(pd.DataFrame(df, columns=['feature_id', 'h3_index_lv'+str(resolution)]))

    def get_h3_index(self, gpd_df, h3_resolution):
        """
        This function returns a pandas dataframe of osm feature ids and h3 hex id in each resolution level.

        Parameters
        ----------
        gpd_df : int
            geopandas dataframe

        list_of_resolutions : list
            h3 index resolutions        

        Returns
        -------
        pandas df
            dataframe of osm feature ids and h3 index ids

        """

        assert len(h3_resolution) == 0, 'No h3 index supplied'
 
        table = pd.DataFrame()
        for v in h3_resolution:
            holding_table = self._return_clean_h3_index(gpd_df, v)
            if len(holding_table) == 0:
                print('No h3 indexes at level ' + str(v) +' were found for your geopandas dataframe.')
            else:
                table = pd.merge(table, holding_table, on='feature_id')
        
        return table

    def get_hex_geojson(self, hexes):
        """
        This function retreives an h3 boundary geojson.

        Parameters
        ----------
        hexes : list
            h3 IDs 

        Returns
        -------
        geojson object
            h3 hex polygons with feature id

        """

        layer = {'type':'FeatureCollection', 'features':[]}
        for hex_ in hexes:

            f = {"type":"Feature", "geometry":{"type":"Polygon", "coordinates":{}}}
            f["id"] = hex_ 
            f['properties'] = {}
            f['geometry']['coordinates'] = [h3.h3_to_geo_boundary(h3.h3_to_string(hex_), geo_json=True)]

            layer['features'].append(f)

        return layer

    def get_hex_gdf(self, hexes):
        """
        This function retreives an h3 object with spatial information and returns as a geopandas data frame.

        Parameters
        ----------
        hexes : list
            h3 IDs 

        Returns
        -------
        geopandas dataframe
            h3 hex polygons with IDs

        """
 
        hex_layer = self.get_hex_geojson(hexes)

        hex_df = gpd.GeoDataFrame(data=hexes, 
                geometry=[Polygon(p['geometry']['coordinates'][0]) for p in hex_layer['features']],
                            columns=['hex'])

        hex_df = hex_df.set_crs(epsg=4326) 

        return hex_df