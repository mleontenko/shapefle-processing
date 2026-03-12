import geopandas as gpd

class DataQualityServices:
    def detect_invalid_geometry(self, gdf, column_name='invalid_geom'):
        gdf = gdf.copy()
        gdf[column_name] = ~gdf.geometry.is_valid
        gdf[column_name] = gdf[column_name].astype(bool)
        return gdf
