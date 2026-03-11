from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QBrush, QColor, QPolygonF
from PyQt6.QtWidgets import QGraphicsPolygonItem
import geopandas as gpd
import pyqtgraph as pg


class ShapefileManager:
    def __init__(self, plot_widget):
        self.plot_widget = plot_widget

    def load_and_render(self, file_name):
        gdf = gpd.read_file(file_name)

        self.plot_widget.clear()

        if gdf.empty:
            return False

        self.render_polygons(gdf)
        self.set_plot_range(gdf)
        return True

    def render_polygons(self, gdf):
        for geometry in gdf.geometry:
            if geometry is None or geometry.is_empty:
                continue

            if geometry.geom_type == 'Polygon':
                polygons = [geometry]
            elif geometry.geom_type == 'MultiPolygon':
                polygons = list(geometry.geoms)
            else:
                continue

            for polygon in polygons:
                x_values, y_values = polygon.exterior.xy

                polygon_item = QPolygonF()
                for x, y in zip(x_values, y_values):
                    polygon_item.append(QPointF(x, y))

                graphics_polygon = QGraphicsPolygonItem(polygon_item)
                graphics_polygon.setPen(pg.mkPen((70, 95, 130, 220), width=0.8))
                graphics_polygon.setBrush(QBrush(QColor(70, 95, 130, 150)))
                self.plot_widget.addItem(graphics_polygon)

    def set_plot_range(self, gdf):
        bounds = gdf.total_bounds
        min_x, min_y, max_x, max_y = bounds
        if min_x != max_x and min_y != max_y:
            self.plot_widget.setXRange(min_x, max_x, padding=0.05)
            self.plot_widget.setYRange(min_y, max_y, padding=0.05)
        else:
            self.plot_widget.enableAutoRange()
