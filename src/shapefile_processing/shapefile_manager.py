import geopandas as gpd

from shapefile_processing.map_renderer import MapRenderer
from shapefile_processing.spatial_metrics_service import SpatialMetricsService


class ShapefileManager:
    def __init__(self, plot_widget, map_renderer=None, spatial_metrics_service=None):
        self.plot_widget = plot_widget
        self.map_renderer = map_renderer or MapRenderer(plot_widget)
        self.spatial_metrics_service = spatial_metrics_service or SpatialMetricsService()
        self.loaded_gdf = None

    def load_and_render(self, file_name):
        gdf = gpd.read_file(file_name)
        self.loaded_gdf = gdf

        self.plot_widget.clear()

        if gdf.empty:
            return False

        self.map_renderer.render_polygons(gdf)
        self.map_renderer.set_plot_range(gdf)
        return True

    def get_attributes(self):
        if self.loaded_gdf is None:
            return None

        return self.loaded_gdf.drop(columns='geometry', errors='ignore')

    def assign_ids(self):
        if self.loaded_gdf is None:
            return None

        feature_count = len(self.loaded_gdf)
        self.loaded_gdf['id'] = [f'BLD_{index}' for index in range(1, feature_count + 1)]
        # convert 'id' column to object type to ensure compatibility with shapefile export
        self.loaded_gdf['id'] = self.loaded_gdf['id'].astype('object')
        return feature_count

    def calculate_area(self):
        if self.loaded_gdf is None:
            return None

        self.loaded_gdf = self.spatial_metrics_service.calculate_area(self.loaded_gdf)
        return len(self.loaded_gdf)

    def calculate_perimeter(self):
        if self.loaded_gdf is None:
            return None

        self.loaded_gdf = self.spatial_metrics_service.calculate_perimeter(self.loaded_gdf)
        return len(self.loaded_gdf)

    def calculate_distance_to_nearest_neighbor(self):
        if self.loaded_gdf is None:
            return None

        self.loaded_gdf = self.spatial_metrics_service.calculate_distance_to_nearest_neighbor(
            self.loaded_gdf,
        )
        return len(self.loaded_gdf)

    def calculate_number_of_neighbors(self, radius=1.0):
        if self.loaded_gdf is None:
            return None

        self.loaded_gdf = self.spatial_metrics_service.calculate_number_of_neighbors(
            self.loaded_gdf,
            radius=radius,
        )
        return len(self.loaded_gdf)

    def export_shapefile(self, output_path):
        if self.loaded_gdf is None:
            return False

        export_gdf = self.loaded_gdf.copy()

        for column_name in export_gdf.columns:
            if column_name == 'geometry':
                continue

            column_series = export_gdf[column_name]
            dtype_module = type(column_series.dtype).__module__
            if dtype_module.startswith('pandas'):
                column_series = column_series.astype('object')

            export_gdf[column_name] = column_series.where(
                column_series.notna(),
                None,
            )

        export_gdf.to_file(output_path, driver='ESRI Shapefile')
        return True
