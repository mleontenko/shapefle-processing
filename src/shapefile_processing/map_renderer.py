"""Rendering helpers for drawing geometries and labels on the map plot widget."""

import geopandas as gpd
import pyqtgraph as pg
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QBrush, QColor, QPolygonF
from PyQt6.QtWidgets import QGraphicsPolygonItem


class MapRenderer:
    """Render spatial layers and labels into a PyQtGraph plot."""

    def __init__(self, plot_widget: pg.PlotWidget) -> None:
        """Initialize renderer with the target plot widget.
        
        Args:
            plot_widget (pg.PlotWidget): The PyQtGraph plot widget to render on
        """
        self.plot_widget = plot_widget

    def render_polygons(self, gdf: gpd.GeoDataFrame) -> None:
        """Draw polygon and multipolygon geometries from a GeoDataFrame.
        
        Args:
            gdf (gpd.GeoDataFrame): GeoDataFrame containing the geometries to render
        """
        for geometry in gdf.geometry:
            if geometry is None or geometry.is_empty:
                continue

            if geometry.geom_type == "Polygon":
                polygons = [geometry]
            elif geometry.geom_type == "MultiPolygon":
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

    def render_labels(self, gdf: gpd.GeoDataFrame, column_name: str = "id") -> None:
        """Draw text labels at feature centroids using the selected attribute.
        
        Args:
            gdf (gpd.GeoDataFrame): GeoDataFrame containing the geometries to label
            column_name (str): Name of the column to use for label text
        """
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
        """Set the plot view to fit the bounds of the GeoDataFrame geometries.
        
        Fit the view to layer bounds, with fallback to auto-range for degenerate 
        extents.

        Args:
            gdf (gpd.GeoDataFrame): GeoDataFrame containing the geometries to fit
        """
        bounds = gdf.total_bounds
        min_x, min_y, max_x, max_y = bounds
        if min_x != max_x and min_y != max_y:
            rect = QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
            self.plot_widget.getPlotItem().getViewBox().setRange(
                rect=rect, padding=0.05
            )
        else:
            self.plot_widget.enableAutoRange()
