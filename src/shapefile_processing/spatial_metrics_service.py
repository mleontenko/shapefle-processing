class SpatialMetricsService:
    def calculate_area(self, gdf, column_name='area'):
        gdf[column_name] = gdf.geometry.area
        return gdf

    def calculate_perimeter(self, gdf, column_name='perimeter'):
        gdf[column_name] = gdf.geometry.length
        return gdf
