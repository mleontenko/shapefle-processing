import tempfile
import unittest
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Polygon

from shapefile_processing.shapefile_manager import ShapefileManager


class FakePlotWidget:
    def __init__(self):
        self.clear_called = False

    def clear(self):
        self.clear_called = True


class FakeMapRenderer:
    def __init__(self):
        self.render_called = False
        self.range_called = False

    def render_polygons(self, gdf):
        self.render_called = True

    def set_plot_range(self, gdf):
        self.range_called = True


class ShapefileManagerTests(unittest.TestCase):
    def test_load_and_render_polygon_shapefile_success(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            shp_path = Path(temp_dir) / "polygons.shp"

            gdf = gpd.GeoDataFrame(
                {"name": ["A", "B"]},
                geometry=[
                    Polygon([(0, 0), (1, 0), (1, 1), (0, 0)]),
                    Polygon([(2, 2), (3, 2), (3, 3), (2, 2)]),
                ],
                crs="EPSG:4326",
            )
            gdf["name"] = gdf["name"].astype("object")
            gdf.to_file(shp_path)

            fake_plot = FakePlotWidget()
            fake_renderer = FakeMapRenderer()
            manager = ShapefileManager(fake_plot, fake_renderer)

            result = manager.load_and_render(str(shp_path))

            self.assertTrue(result)
            self.assertTrue(fake_plot.clear_called)
            self.assertTrue(fake_renderer.render_called)
            self.assertTrue(fake_renderer.range_called)
            self.assertIsNotNone(manager.loaded_gdf)
            self.assertEqual(len(manager.loaded_gdf), 2)


if __name__ == "__main__":
    unittest.main()
