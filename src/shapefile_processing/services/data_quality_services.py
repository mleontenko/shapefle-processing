import geopandas as gpd


class DataQualityServices:
    def detect_invalid_geometry(self, gdf, column_name='invalid_geom'):
        gdf = gdf.copy()
        gdf[column_name] = ~gdf.geometry.is_valid
        gdf[column_name] = gdf[column_name].astype(bool)
        return gdf

    def detect_overlapping_polygons(self, gdf, column_name='overlap'):
        # avoid mutating original dataframe, force clean index for reliable joining
        gdf = gdf.copy().reset_index(drop=True)

        # Self-join: keep rows where geometries intersect in area
        # add suffix because of duplicate column names from join
        # predicate='overlaps' does not include cases where one polygon is completely within another
        joined = gpd.sjoin(gdf, gdf, how='left', predicate='intersects', lsuffix='left', rsuffix='right')

        # Remove self-matches
        joined = joined[joined.index != joined['index_right']]

        # Filter out boundary touches
        def _has_interior_overlap(row):
            left_geom = gdf.geometry.iloc[row.name]
            right_geom = gdf.geometry.iloc[row['index_right']]
            intersection = left_geom.intersection(right_geom)
            return not intersection.is_empty and intersection.area > 0

        if not joined.empty:
            mask = joined.apply(_has_interior_overlap, axis=1)
            overlapping_indices = set(joined[mask].index.tolist())
        else:
            overlapping_indices = set()

        gdf[column_name] = gdf.index.isin(overlapping_indices)
        gdf[column_name] = gdf[column_name].astype(bool)
        return gdf
