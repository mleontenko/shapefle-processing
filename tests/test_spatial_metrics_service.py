import unittest

import geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon

from shapefile_processing.services.spatial_metrics_service import SpatialMetricsService


class SpatialMetricsServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = SpatialMetricsService()

    def test_calculate_area_adds_area_column(self) -> None:
        poly_a = Polygon([(0, 0), (2, 0), (2, 2), (0, 0)])
        poly_b = Polygon([(0, 0), (3, 0), (3, 1), (0, 0)])
        gdf = gpd.GeoDataFrame(
            {"id": [1, 2]}, geometry=[poly_a, poly_b], crs="EPSG:25884"
        )

        result = self.service.calculate_area(gdf.copy())

        self.assertIn("area", result.columns)
        self.assertAlmostEqual(2.0, float(result.loc[0, "area"]), places=6)
        self.assertAlmostEqual(1.5, float(result.loc[1, "area"]), places=6)

    def test_calculate_perimeter_adds_perimeter_column(self) -> None:
        polygon = Polygon([(0, 0), (2, 0), (2, 2), (0, 0)])
        gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[polygon], crs="EPSG:25884")

        result = self.service.calculate_perimeter(gdf.copy())

        self.assertIn("perimeter", result.columns)
        self.assertAlmostEqual(6.828427, float(result.loc[0, "perimeter"]), places=5)

    def test_calculate_distance_to_nearest_neighbor_adds_distance_and_id(self) -> None:
        gdf = gpd.GeoDataFrame(
            {"id": [1, 2, 3]},
            geometry=[
                Polygon([(0, 0), (1, 0), (1, 1), (0, 0)]),
                Polygon([(3, 0), (4, 0), (4, 1), (3, 0)]),
                Polygon([(10, 0), (11, 0), (11, 1), (10, 0)]),
            ],
            crs="EPSG:25884",
        )

        result = self.service.calculate_distance_to_nearest_neighbor(gdf.copy())

        self.assertIn("dist_near", result.columns)
        self.assertIn("nearest", result.columns)
        self.assertEqual([2, 1, 2], result["nearest"].tolist())
        distances = [float(v) for v in result["dist_near"].tolist()]
        self.assertAlmostEqual(2.0, distances[0], places=6)
        self.assertAlmostEqual(2.0, distances[1], places=6)
        self.assertAlmostEqual(6.0, distances[2], places=6)

    def test_calculate_number_of_neighbors_counts_within_radius(self) -> None:
        gdf = gpd.GeoDataFrame(
            {"id": [1, 2, 3]},
            geometry=[
                Polygon([(0, 0), (1, 0), (1, 1), (0, 0)]),
                Polygon([(3, 0), (4, 0), (4, 1), (3, 0)]),
                Polygon([(10, 0), (11, 0), (11, 1), (10, 0)]),
            ],
            crs="EPSG:25884",
        )

        result = self.service.calculate_number_of_neighbors(gdf.copy(), radius=3.5)

        self.assertIn("num_neighb", result.columns)
        self.assertEqual([1, 1, 0], result["num_neighb"].tolist())

    def test_calculate_centroid_coordinates_adds_xy_columns(self) -> None:
        polygon = Polygon([(0, 0), (2, 0), (2, 2), (0, 0)])
        gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[polygon], crs="EPSG:25884")

        result = self.service.calculate_centroid_coordinates(gdf.copy())

        self.assertIn("centroid_x", result.columns)
        self.assertIn("centroid_y", result.columns)
        self.assertAlmostEqual(1.333333, float(result.loc[0, "centroid_x"]), places=5)
        self.assertAlmostEqual(0.666667, float(result.loc[0, "centroid_y"]), places=5)

    def test_calculate_number_of_vertices_excludes_closing_point(self) -> None:
        polygon = Polygon([(0, 0), (2, 0), (2, 2), (0, 0)])
        gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[polygon], crs="EPSG:25884")

        result = self.service.calculate_number_of_vertices(gdf.copy())

        self.assertIn("num_vertices", result.columns)
        self.assertEqual([3], result["num_vertices"].tolist())

    def test_calculate_number_of_vertices_supports_multipolygon(self) -> None:
        polygon_a = Polygon([(0, 0), (2, 0), (2, 2), (0, 0)])
        polygon_b = Polygon([(3, 0), (4, 0), (4, 1), (3, 0)])
        multipolygon = MultiPolygon([polygon_a, polygon_b])
        gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[multipolygon], crs="EPSG:25884")

        result = self.service.calculate_number_of_vertices(gdf.copy())

        self.assertIn("num_vertices", result.columns)
        self.assertEqual([6], result["num_vertices"].tolist())

    def test_calculate_number_of_vertices_counts_invalid_polygon(self) -> None:
        invalid_polygon = Polygon([(0, 0), (2, 2), (0, 2), (2, 0), (0, 0)])
        self.assertFalse(invalid_polygon.is_valid)
        gdf = gpd.GeoDataFrame(
            {"id": [1]}, geometry=[invalid_polygon], crs="EPSG:25884"
        )

        result = self.service.calculate_number_of_vertices(gdf.copy())

        self.assertIn("num_vertices", result.columns)
        self.assertEqual([4], result["num_vertices"].tolist())


if __name__ == "__main__":
    unittest.main()
