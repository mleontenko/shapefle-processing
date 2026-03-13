from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QBrush, QColor, QPolygonF
from PyQt6.QtWidgets import QGraphicsPolygonItem
import geopandas as gpd
import pyqtgraph as pg


class MapRenderer:
    def __init__(self, plot_widget: pg.PlotWidget) -> None:
        self.plot_widget = plot_widget

    def render_polygons(self, gdf: gpd.GeoDataFrame) -> None:
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

    def render_labels(self, gdf: gpd.GeoDataFrame, column_name: str = 'id') -> None:
        for _, row in gdf.iterrows():
            if row.geometry is None or row.geometry.is_empty:
                continue
            centroid = row.geometry.centroid
            label = pg.TextItem(
                text=str(row[column_name]),
                color=(0, 0, 0),
                anchor=(0.5, 0.5),
            )
            label.setPos(centroid.x, centroid.y)
            self.plot_widget.addItem(label)

    def set_plot_range(self, gdf: gpd.GeoDataFrame) -> None:
        bounds = gdf.total_bounds
        min_x, min_y, max_x, max_y = bounds
        if min_x != max_x and min_y != max_y:
            self.plot_widget.setXRange(min_x, max_x, padding=0.05)
            self.plot_widget.setYRange(min_y, max_y, padding=0.05)
        else:
            self.plot_widget.enableAutoRange()
