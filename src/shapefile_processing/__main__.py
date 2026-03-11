import sys
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QAction, QPolygonF, QBrush, QColor
from PyQt6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox, QGraphicsPolygonItem
import pyqtgraph as pg
import geopandas as gpd

pg.setConfigOptions(antialias=True)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Shapefile Loader')
        self.setGeometry(100, 100, 800, 600)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.08)
        self.plot_widget.setAspectLocked(True)
        
        # Format axes to show full decimal notation instead of scientific
        ax_x = self.plot_widget.getAxis('bottom')
        ax_y = self.plot_widget.getAxis('left')
        ax_x.tickStrings = lambda values, scale, spacing: [f'{int(v)}' for v in values]
        ax_y.tickStrings = lambda values, scale, spacing: [f'{int(v)}' for v in values]
        
        self.setCentralWidget(self.plot_widget)

        self.create_menu()

    def create_menu(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('File')

        load_action = QAction('Load Shapefile', self)
        load_action.triggered.connect(self.load_shapefile)
        file_menu.addAction(load_action)

    def load_shapefile(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            'Load Shapefile',
            '',
            'Shapefiles (*.shp);;All Files (*)',
        )
        if file_name:
            self.render_shapefile(file_name)

    def render_shapefile(self, file_name):
        try:
            gdf = gpd.read_file(file_name)
        except Exception as error:
            QMessageBox.critical(self, 'Load Error', f'Failed to load shapefile:\n{error}')
            return

        self.plot_widget.clear()

        if gdf.empty:
            QMessageBox.information(self, 'Empty Layer', 'The selected shapefile contains no features.')
            return

        self.render_polygons(gdf)

        bounds = gdf.total_bounds
        min_x, min_y, max_x, max_y = bounds
        if min_x != max_x and min_y != max_y:
            self.plot_widget.setXRange(min_x, max_x, padding=0.05)
            self.plot_widget.setYRange(min_y, max_y, padding=0.05)
        else:
            self.plot_widget.enableAutoRange()

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
                
                # Create filled polygon
                polygon_item = QPolygonF()
                for x, y in zip(x_values, y_values):
                    polygon_item.append(QPointF(x, y))
                
                graphics_polygon = QGraphicsPolygonItem(polygon_item)
                graphics_polygon.setPen(pg.mkPen((70, 95, 130, 220), width=0.8))
                graphics_polygon.setBrush(QBrush(QColor(70, 95, 130, 150)))  # Transparent fill
                self.plot_widget.addItem(graphics_polygon)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())