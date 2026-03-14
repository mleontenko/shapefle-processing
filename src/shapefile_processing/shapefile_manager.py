"""High-level manager for loading, enriching, validating, and exporting shapefiles."""

from os import PathLike

import geopandas as gpd
import pandas as pd
import pyqtgraph as pg

from shapefile_processing.map_renderer import MapRenderer
from shapefile_processing.services.data_quality_services import DataQualityServices
from shapefile_processing.services.spatial_metrics_service import SpatialMetricsService


class ShapefileManager:
    """Coordinates map rendering and geospatial service operations for the UI."""

    def __init__(
        self,
        plot_widget: pg.PlotWidget,
        map_renderer: MapRenderer | None = None,
        spatial_metrics_service: SpatialMetricsService | None = None,
        data_quality_services: DataQualityServices | None = None,
    ) -> None:
        """Initialize manager dependencies and set empty loaded layer state."""
        self.plot_widget = plot_widget
        self.map_renderer = map_renderer or MapRenderer(plot_widget)
        self.spatial_metrics_service = (
            spatial_metrics_service or SpatialMetricsService()
        )
        self.data_quality_services = data_quality_services or DataQualityServices()
        self.loaded_gdf: gpd.GeoDataFrame | None = None

    def load_and_render(self, file_name: str | PathLike[str]) -> bool:
        """Load a shapefile and render features on the plot widget."""
        gdf = gpd.read_file(file_name)
        self.loaded_gdf = gdf

        self.plot_widget.clear()

        if gdf.empty:
            return False

        self.map_renderer.render_polygons(gdf)
        self.map_renderer.set_plot_range(gdf)
        return True

    def get_attributes(self) -> pd.DataFrame | None:
        """Return non-geometry attributes for the loaded layer, if available."""
        if self.loaded_gdf is None:
            return None

        return self.loaded_gdf.drop(columns="geometry", errors="ignore")

    def assign_ids(self) -> int | None:
        """Assign sequential BLD-style IDs and render labels for loaded features."""
        if self.loaded_gdf is None:
            return None

        feature_count = len(self.loaded_gdf)
        self.loaded_gdf["id"] = [
            f"BLD_{index}" for index in range(1, feature_count + 1)
        ]
        # convert 'id' column to object type to ensure compatibility 
        #with shapefile export
        self.loaded_gdf["id"] = self.loaded_gdf["id"].astype("object")
        self.map_renderer.render_labels(self.loaded_gdf, column_name="id")
        return feature_count

    def calculate_area(self) -> int | None:
        """Calculate and store feature area for the loaded layer."""
        if self.loaded_gdf is None:
            return None

        self.loaded_gdf = self.spatial_metrics_service.calculate_area(self.loaded_gdf)
        return len(self.loaded_gdf)

    def calculate_perimeter(self) -> int | None:
        """Calculate and store feature perimeter for the loaded layer."""
        if self.loaded_gdf is None:
            return None

        self.loaded_gdf = self.spatial_metrics_service.calculate_perimeter(
            self.loaded_gdf
        )
        return len(self.loaded_gdf)

    def calculate_distance_to_nearest_neighbor(self) -> int | None:
        """Calculate nearest-neighbor distance and nearest ID for each feature."""
        if self.loaded_gdf is None:
            return None

        self.loaded_gdf = (
            self.spatial_metrics_service.calculate_distance_to_nearest_neighbor(
                self.loaded_gdf,
            )
        )
        return len(self.loaded_gdf)

    def calculate_number_of_neighbors(self, radius: float = 1.0) -> int | None:
        """Count neighbors within the provided radius for each feature."""
        if self.loaded_gdf is None:
            return None

        self.loaded_gdf = self.spatial_metrics_service.calculate_number_of_neighbors(
            self.loaded_gdf,
            radius=radius,
        )
        return len(self.loaded_gdf)

    def calculate_centroid_coordinates(self) -> int | None:
        """Calculate and store centroid X/Y coordinates for each feature."""
        if self.loaded_gdf is None:
            return None

        self.loaded_gdf = self.spatial_metrics_service.calculate_centroid_coordinates(
            self.loaded_gdf,
        )
        return len(self.loaded_gdf)

    def calculate_number_of_vertices(self) -> int | None:
        """Calculate and store polygon vertex counts for each feature."""
        if self.loaded_gdf is None:
            return None

        self.loaded_gdf = self.spatial_metrics_service.calculate_number_of_vertices(
            self.loaded_gdf,
        )
        return len(self.loaded_gdf)

    def detect_invalid_geometry(self) -> tuple[int, int] | None:
        """Mark invalid geometries and return invalid and total feature counts."""
        if self.loaded_gdf is None:
            return None

        self.loaded_gdf = self.data_quality_services.detect_invalid_geometry(
            self.loaded_gdf
        )
        invalid_count = int(self.loaded_gdf["invalid_geom"].sum())
        total_count = len(self.loaded_gdf)
        return invalid_count, total_count

    def detect_overlapping_polygons(self) -> tuple[int, int] | None:
        """Mark overlapping polygons and return overlap and total feature counts."""
        if self.loaded_gdf is None:
            return None

        self.loaded_gdf = self.data_quality_services.detect_overlapping_polygons(
            self.loaded_gdf
        )
        overlap_count = int(self.loaded_gdf["overlap"].sum())
        total_count = len(self.loaded_gdf)
        return overlap_count, total_count

    def detect_spatial_outliers(
        self, distance_threshold: float = 1.0
    ) -> tuple[int, int] | None:
        """Mark spatial outliers and return outlier and total feature counts."""
        if self.loaded_gdf is None:
            return None

        self.loaded_gdf = self.data_quality_services.detect_spatial_outliers(
            self.loaded_gdf,
            distance_threshold=distance_threshold,
        )
        outlier_count = int(self.loaded_gdf["spatial_outlier"].sum())
        total_count = len(self.loaded_gdf)
        return outlier_count, total_count

    def export_shapefile(self, output_path: str | PathLike[str]) -> bool:
        """Export the current layer to an ESRI Shapefile."""
        if self.loaded_gdf is None:
            return False

        export_gdf = self.loaded_gdf.copy()

        for column_name in export_gdf.columns:
            if column_name == "geometry":
                continue

            column_series = export_gdf[column_name]
            dtype_module = type(column_series.dtype).__module__
            if dtype_module.startswith("pandas"):
                column_series = column_series.astype("object")

            export_gdf[column_name] = column_series.where(
                column_series.notna(),
                None,
            )

        export_gdf.to_file(output_path, driver="ESRI Shapefile")
        return True
