import geopandas as gpd


class SpatialMetricsService:
    def calculate_area(self, gdf, column_name='area'):
        gdf[column_name] = gdf.geometry.area
        return gdf

    def calculate_perimeter(self, gdf, column_name='perimeter'):
        gdf[column_name] = gdf.geometry.length
        return gdf

    def calculate_distance_to_nearest_neighbor(
        self,
        gdf,
        column_name='dist_near',
        nearest_column_name='nearest',
        id_column_name='id',
    ):
        left = gdf.reset_index(drop=True)
        right = left.copy()

        try:
            nearest = gpd.sjoin_nearest(
                left,
                right,
                how='left',
                distance_col=column_name,
                lsuffix='left',
                rsuffix='right',
                max_distance=None,
                exclusive=True,
            )
        except TypeError:
            nearest = gpd.sjoin_nearest(
                left,
                right,
                how='left',
                distance_col=column_name,
                lsuffix='left',
                rsuffix='right',
                max_distance=None,
            )
            nearest = nearest[nearest.index != nearest['index_right']]

        if nearest.empty:
            gdf[column_name] = None
            gdf[nearest_column_name] = None
            return gdf

        # If multiple candidates exist (ties), keep the first one with minimum distance
        nearest_per_feature = nearest.sort_values(column_name).groupby(level=0, sort=False).first()

        # After sjoin_nearest, right-side columns are suffixed (e.g. id_right)
        # Build expected column name dynamically from 'id_column_name'
        right_id_column_name = f'{id_column_name}_right'
        # nearest neighbor's explicit ID value from the right layer
        nearest_id_series = nearest_per_feature[right_id_column_name]
    

        # Align computed values back to the original row order in `gdf`.
        # 'nearest_per_feature' is indexed by left feature index; reindex fills by matching index.
        row_index = gdf.reset_index(drop=True).index        
        # Write nearest neighbor identifier (ID or fallback index).
        gdf[nearest_column_name] = nearest_id_series.reindex(row_index).values
        # Write nearest distance (distance_nearest).
        gdf[column_name] = nearest_per_feature[column_name].reindex(row_index).values
        return gdf
