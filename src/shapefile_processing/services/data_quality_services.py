"""Data quality checks for geometry validity, overlaps, and spatial outliers."""

import geopandas as gpd
import pandas as pd


class DataQualityServices:
    """Provides methods for assessing the quality of spatial data, such as detecting invalid geometries, overlaps, and spatial outliers."""

    def detect_invalid_geometry(
        self,
        gdf: gpd.GeoDataFrame,
        column_name: str = "invalid_geom",
    ) -> gpd.GeoDataFrame:
        """Detects invalid geometries in the GeoDataFrame and adds a boolean column indicating validity.

        Args:
            gdf (gpd.GeoDataFrame): GeoDataFrame containing the geometries to analyze
            column_name (str): Name of the column to store the validity flags

        Returns:
            gpd.GeoDataFrame: GeoDataFrame with the new column containing validity flags
        """
        gdf = gdf.copy()

        # check for valid geometries and flip with ~ to mark invalid ones as True
        gdf[column_name] = ~gdf.geometry.is_valid
        gdf[column_name] = gdf[column_name].astype(bool)
        return gdf

    def detect_overlapping_polygons(
        self,
        gdf: gpd.GeoDataFrame,
        column_name: str = "overlap",
    ) -> gpd.GeoDataFrame:
        """Detects overlapping polygons in the GeoDataFrame and adds a boolean column indicating overlaps.

        Args:
            gdf (gpd.GeoDataFrame): GeoDataFrame containing the geometries to analyze
            column_name (str): Name of the column to store the overlap flags

        Returns:
            gpd.GeoDataFrame: GeoDataFrame with the new column containing overlap flags
        """
        # avoid mutating original dataframe, force clean index for reliable joining
        gdf = gdf.copy().reset_index(drop=True)

        # Self-join: keep rows where geometries intersect in area
        # add suffix because of duplicate column names from join
        # predicate='overlaps' does not include cases where one polygon is completely within another
        joined = gpd.sjoin(
            gdf,
            gdf,
            how="left",
            predicate="intersects",
            lsuffix="left",
            rsuffix="right",
        )

        # Remove self-matches
        joined = joined[joined.index != joined["index_right"]]

        # Filter out boundary touches
        def _has_interior_overlap(row: pd.Series) -> bool:
            left_geom = gdf.geometry.iloc[row.name]
            right_geom = gdf.geometry.iloc[row["index_right"]]
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

    def detect_spatial_outliers(
        self,
        gdf: gpd.GeoDataFrame,
        distance_threshold: float = 1.0,
        column_name: str = "spatial_outlier",
    ) -> gpd.GeoDataFrame:
        """Identifies spatial outliers based on distance to nearest neighbor.

        Args:
            gdf (gpd.GeoDataFrame): GeoDataFrame containing the geometries to analyze
            distance_threshold (float): Distance threshold to classify outliers
            column_name (str): Name of the column to store the outlier flags

        Returns:
            gpd.GeoDataFrame: GeoDataFrame with the new column containing outlier flags
        """
        gdf = gdf.copy().reset_index(drop=True)
        gdf[column_name] = False

        if gdf.empty:
            return gdf

        if len(gdf) == 1:
            gdf[column_name] = True
            return gdf

        distance_col = "_nearest_edge_distance"

        # sjoin_nearest() calculates distance to nearest neighbour
        # if polygons are separeate - distance is from nearest edge to nearest edge
        # if polygons touch or overlap, distance is 0
        # exclusive = True avoids matching feature to iteslf
        nearest = gpd.sjoin_nearest(
            gdf,
            gdf,
            how="left",
            distance_col=distance_col,
            lsuffix="left",
            rsuffix="right",
            max_distance=None,
            exclusive=True,
        )

        if nearest.empty:
            gdf[column_name] = True
            return gdf

        # If multiple candidates exist (ties), keep the first one with minimum distance
        nearest_per_feature = (
            nearest.sort_values(distance_col).groupby(level=0, sort=False).first()
        )
        # reindex to original gdf order and assign distances
        nearest_distances = nearest_per_feature[distance_col].reindex(gdf.index)

        # classify as outlier if nearest neighbor is farther than threshold or if no neighbors exist (NaN distance)
        gdf[column_name] = nearest_distances.isna() | (
            nearest_distances > distance_threshold
        )
        gdf[column_name] = gdf[column_name].astype(bool)
        return gdf
