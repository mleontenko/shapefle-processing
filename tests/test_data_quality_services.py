import unittest

import geopandas as gpd
from shapely.geometry import Polygon

from shapefile_processing.services.data_quality_services import DataQualityServices


class DataQualityServicesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = DataQualityServices()

    def test_detect_invalid_geometry_marks_invalid_features(self) -> None:
        valid_polygon = Polygon([(0, 0), (2, 0), (1, 1), (0, 0)])
        # self-intersection polygon (invalid)
        invalid_polygon = Polygon([(0, 0), (2, 2), (0, 2), (2, 0), (0, 0)])

        gdf = gpd.GeoDataFrame(
            {"name": ["valid", "invalid"]},
            geometry=[valid_polygon, invalid_polygon],
            crs="EPSG:25884",
        )

        result = self.service.detect_invalid_geometry(gdf)

        self.assertIn("invalid_geom", result.columns)
        self.assertEqual([False, True], result["invalid_geom"].tolist())
        self.assertNotIn("invalid_geom", gdf.columns)

    def test_detect_overlapping_polygons_marks_true_for_area_overlap(self) -> None:
        # a and b overlap, c does not
        polygon_a = Polygon([(0, 0), (2, 0), (2, 2), (0, 0)])
        polygon_b = Polygon([(1, 1), (3, 1), (3, 3), (1, 1)])
        polygon_c = Polygon([(5, 5), (7, 5), (7, 7), (5, 5)])

        gdf = gpd.GeoDataFrame(
            {"id": [1, 2, 3]},
            geometry=[polygon_a, polygon_b, polygon_c],
            crs="EPSG:25884",
        )

        result = self.service.detect_overlapping_polygons(gdf)

        self.assertIn("overlap", result.columns)
        self.assertEqual([True, True, False], result["overlap"].tolist())
        self.assertNotIn("overlap", gdf.columns)

    def test_detect_overlapping_polygons_excludes_boundary_touch(self) -> None:
        # polygons share an edge at x=2 but have no area overlap
        polygon_left = Polygon([(0, 0), (2, 0), (2, 2), (0, 0)])
        polygon_right = Polygon([(2, 0), (4, 0), (4, 2), (2, 0)])

        gdf = gpd.GeoDataFrame(
            {"id": [1, 2]},
            geometry=[polygon_left, polygon_right],
            crs="EPSG:25884",
        )

        result = self.service.detect_overlapping_polygons(gdf)

        self.assertEqual([False, False], result["overlap"].tolist())

    def test_detect_overlapping_polygons_detects_containment(self) -> None:
        # inner polygon is completely within outer polygon
        outer_polygon = Polygon([(0, 0), (6, 0), (6, 6), (0, 0)])
        inner_polygon = Polygon([(2, 2), (3, 2), (3, 3), (2, 2)])

        gdf = gpd.GeoDataFrame(
            {"id": [1, 2]},
            geometry=[outer_polygon, inner_polygon],
            crs="EPSG:25884",
        )

        result = self.service.detect_overlapping_polygons(gdf)

        self.assertEqual([True, True], result["overlap"].tolist())

    def test_detect_spatial_outliers_uses_edge_to_edge_distance(self) -> None:
        # nearest edge distances: a<->b = 1, c<->b = 7
        polygon_a = Polygon([(0, 0), (1, 0), (1, 1), (0, 0)])
        polygon_b = Polygon([(2, 0), (3, 0), (3, 1), (2, 0)])
        polygon_c = Polygon([(10, 0), (11, 0), (11, 1), (10, 0)])

        gdf = gpd.GeoDataFrame(
            {"id": [1, 2, 3]},
            geometry=[polygon_a, polygon_b, polygon_c],
            crs="EPSG:25884",
        )

        result = self.service.detect_spatial_outliers(gdf, distance_threshold=1.5)

        self.assertIn("spatial_outlier", result.columns)
        self.assertEqual([False, False, True], result["spatial_outlier"].tolist())
        self.assertNotIn("spatial_outlier", gdf.columns)

    def test_detect_spatial_outliers_single_feature_is_outlier(self) -> None:
        polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 0)])
        gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[polygon], crs="EPSG:25884")

        result = self.service.detect_spatial_outliers(gdf, distance_threshold=1.0)

        self.assertEqual([True], result["spatial_outlier"].tolist())


if __name__ == "__main__":
    unittest.main()
