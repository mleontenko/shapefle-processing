"""Spatial metric calculations for geometry-based feature enrichment."""

import geopandas as gpd


class SpatialMetricsService:
    """Provides methods for calculating spatial metrics such as area, perimeter, nearest neighbor distance, and vertex counts."""

    def calculate_area(
        self,
        gdf: gpd.GeoDataFrame,
        column_name: str = "area",
    ) -> gpd.GeoDataFrame:
        """Calculates the area of each geometry in the GeoDataFrame and adds it as a new column.

        Args:
            gdf (gpd.GeoDataFrame): GeoDataFrame containing the geometries to analyze
            column_name (str): Name of the column to store the area values

        Returns:
            gpd.GeoDataFrame: GeoDataFrame with the new column containing area values
        """
        gdf[column_name] = gdf.geometry.area
        return gdf

    def calculate_perimeter(
        self,
        gdf: gpd.GeoDataFrame,
        column_name: str = "perimeter",
    ) -> gpd.GeoDataFrame:
        """Calculates the perimeter of each geometry in the GeoDataFrame and adds it as a new column.

        Args:
            gdf (gpd.GeoDataFrame): GeoDataFrame containing the geometries to analyze
            column_name (str): Name of the column to store the perimeter values

        Returns:
            gpd.GeoDataFrame: GeoDataFrame with the new column containing perimeter values
        """
        gdf[column_name] = gdf.geometry.length
        return gdf

    def calculate_distance_to_nearest_neighbor(
        self,
        gdf: gpd.GeoDataFrame,
        column_name: str = "dist_near",
        nearest_column_name: str = "nearest",
        id_column_name: str = "id",
    ) -> gpd.GeoDataFrame:
        """Calculates the distance to the nearest neighbor for each geometry and adds it as a new column.

        Also adds a column with the identifier of the nearest neighbor.

        Args:
            gdf (gpd.GeoDataFrame): GeoDataFrame containing the geometries to analyze
            column_name (str): Name of the column to store the nearest neighbor distances
            nearest_column_name (str): Name of the column to store the nearest neighbor identifiers
            id_column_name (str): Name of the identifier column in the input GeoDataFrame

        Returns:
            gpd.GeoDataFrame: GeoDataFrame with the new columns containing nearest neighbor distances and identifiers
        """
        left = gdf.reset_index(drop=True)
        right = left.copy()

        try:
            nearest = gpd.sjoin_nearest(
                left,
                right,
                how="left",
                distance_col=column_name,
                lsuffix="left",
                rsuffix="right",
                max_distance=None,
                exclusive=True,
            )
        except TypeError:
            nearest = gpd.sjoin_nearest(
                left,
                right,
                how="left",
                distance_col=column_name,
                lsuffix="left",
                rsuffix="right",
                max_distance=None,
            )
            nearest = nearest[nearest.index != nearest["index_right"]]

        if nearest.empty:
            gdf[column_name] = None
            gdf[nearest_column_name] = None
            return gdf

        # If multiple candidates exist (ties), keep the first one with minimum distance
        nearest_per_feature = (
            nearest.sort_values(column_name).groupby(level=0, sort=False).first()
        )

        # After sjoin_nearest, right-side columns are suffixed (e.g. id_right)
        # Build expected column name dynamically from 'id_column_name'
        right_id_column_name = f"{id_column_name}_right"
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

    def calculate_number_of_neighbors(
        self,
        gdf: gpd.GeoDataFrame,
        radius: float = 1.0,
        column_name: str = "num_neighb",
    ) -> gpd.GeoDataFrame:
        """Calculates the number of neighbors within a specified radius for each geometry and adds it as a new column.

        Args:
            gdf (gpd.GeoDataFrame): GeoDataFrame containing the geometries to analyze
            radius (float): Radius within which to count neighbors
            column_name (str): Name of the column to store the neighbor counts

        Returns:
            gpd.GeoDataFrame: GeoDataFrame with the new column containing neighbor counts
        """
        left = gdf.reset_index(drop=True)
        right = left.copy()

        # Create buffered geometries for spatial join
        left_buffered = left.copy()
        left_buffered.geometry = left_buffered.geometry.buffer(radius)

        # Spatial join to find all geometries within radius
        neighbors = gpd.sjoin(
            left_buffered,
            right,
            how="left",
            predicate="intersects",
            lsuffix="left",
            rsuffix="right",
        )

        # Count neighbors per feature, excluding self
        neighbor_count = (
            neighbors[neighbors.index != neighbors["index_right"]]
            .groupby(level=0)
            .size()
        )

        # Assign counts, filling missing indices with 0
        row_index = gdf.reset_index(drop=True).index
        gdf[column_name] = neighbor_count.reindex(row_index, fill_value=0).values

        return gdf

    def calculate_centroid_coordinates(
        self,
        gdf: gpd.GeoDataFrame,
        x_column: str = "centroid_x",
        y_column: str = "centroid_y",
    ) -> gpd.GeoDataFrame:
        """Calculates the centroid coordinates of each geometry and adds them as new columns.

        Args:
            gdf (gpd.GeoDataFrame): GeoDataFrame containing the geometries to analyze
            x_column (str): Name of the column to store the centroid X coordinates
            y_column (str): Name of the column to store the centroid Y coordinates

        Returns:
            gpd.GeoDataFrame: GeoDataFrame with the new columns containing centroid coordinates
        """
        gdf[x_column] = gdf.geometry.centroid.x
        gdf[y_column] = gdf.geometry.centroid.y
        return gdf

    def calculate_number_of_vertices(
        self,
        gdf: gpd.GeoDataFrame,
        column_name: str = "num_vertices",
    ) -> gpd.GeoDataFrame:
        """Counts the number of vertices for each geometry, excluding the closing point for polygons.

        Args:
            gdf (gpd.GeoDataFrame): GeoDataFrame containing the geometries to analyze
            column_name (str): Name of the column to store the vertex counts

        Returns:
            gpd.GeoDataFrame: GeoDataFrame with the new column containing vertex counts
        """
        gdf[column_name] = gdf.geometry.apply(self._count_polygon_vertices)
        return gdf

    def _count_polygon_vertices(self, geom) -> int | None:
        """Counts the number of vertices for a geometry, excluding the closing point for polygons."""
        if geom is None or geom.is_empty:
            return None

        if geom.geom_type == "Polygon":
            count = len(geom.exterior.coords)
            if count > 1 and geom.exterior.coords[0] == geom.exterior.coords[-1]:
                return count - 1
            return count

        if geom.geom_type == "MultiPolygon":
            return sum(
                len(part.exterior.coords) - 1
                if len(part.exterior.coords) > 1
                and part.exterior.coords[0] == part.exterior.coords[-1]
                else len(part.exterior.coords)
                for part in geom.geoms
                if not part.is_empty
            )

        return None
