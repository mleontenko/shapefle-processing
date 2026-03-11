import sys
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox
import pyqtgraph as pg

from shapefile_processing.shapefile_manager import ShapefileManager

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

        self.shapefile_manager = ShapefileManager(self.plot_widget)
        
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
            has_features = self.shapefile_manager.load_and_render(file_name)
        except Exception as error:
            QMessageBox.critical(self, 'Load Error', f'Failed to load shapefile:\n{error}')
            return

        if not has_features:
            QMessageBox.information(self, 'Empty Layer', 'The selected shapefile contains no features.')
            return

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())