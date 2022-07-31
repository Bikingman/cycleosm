import h3

class HandleH3():
    def __init__(self):
        super(HandleH3, self).__init__()

    def _get_h3_list(self, row, resolution):
        return([h3.polyfill(row.geometry.__geo_interface__, resolution, geo_json_conformant = True)])

    def _polygon_row_get_inner_h3_id(self, row, resolution):
        roads_h3id = []
        for i in self._get_h3_list(row, resolution):
            for j in [*i]:
                roads_h3id.append({'osm_id': row.id, 'h3_index': j})
        return(roads_h3id)

    def polygon_get_inner_h3_id(self, roads, resultion):
        return(roads.apply(lambda row: (self._polygon_row_get_inner_h3_id(row, resultion)), axis=1))