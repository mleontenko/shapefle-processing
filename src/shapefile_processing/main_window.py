from os import PathLike

import pyqtgraph as pg
from PyQt6.QtCore import QEvent
from PyQt6.QtGui import QAction, QShowEvent
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from shapefile_processing.map_renderer import MapRenderer
from shapefile_processing.shapefile_manager import ShapefileManager
from shapefile_processing.zoom_to_data_button import ZoomToDataButton

pg.setConfigOptions(antialias=True)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Shapefile Loader")
        self.setGeometry(100, 100, 800, 600)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("w")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.08)
        self.plot_widget.setAspectLocked(True)

        # Format axes to show full decimal notation instead of scientific
        ax_x = self.plot_widget.getAxis("bottom")
        ax_y = self.plot_widget.getAxis("left")
        ax_x.tickStrings = lambda values, scale, spacing: [f"{int(v)}" for v in values]
        ax_y.tickStrings = lambda values, scale, spacing: [f"{int(v)}" for v in values]

        self.map_renderer = MapRenderer(self.plot_widget)
        self.shapefile_manager = ShapefileManager(self.plot_widget, self.map_renderer)

        self.setCentralWidget(self.plot_widget)

        self.zoom_to_data_overlay = ZoomToDataButton(
            self.plot_widget, self.zoom_to_data
        )
        self.zoom_to_data_button = self.zoom_to_data_overlay.button

        self.create_menu()
        self.create_toolbar()

    def create_menu(self) -> None:
        menu_bar = self.menuBar()
        # satisfy type checker that menu_bar is not None, since QMainWindow.menuBar()
        # should always return a valid QMenuBar instance
        assert menu_bar is not None
        file_menu = menu_bar.addMenu("File")
        view_menu = menu_bar.addMenu("View")
        assert file_menu is not None
        assert view_menu is not None

        load_action = QAction("Load Shapefile", self)
        load_action.triggered.connect(self.load_shapefile)
        file_menu.addAction(load_action)

        export_action = QAction("Export Shapefile", self)
        export_action.triggered.connect(self.export_shapefile)
        file_menu.addAction(export_action)

        attribute_table_action = QAction("Attribute Table", self)
        attribute_table_action.triggered.connect(self.show_attribute_table)
        view_menu.addAction(attribute_table_action)

    def create_toolbar(self) -> None:
        toolbar = self.addToolBar("Tools")
        assert toolbar is not None
        self.assign_ids_action = QAction("1. Assign IDs", self)
        self.assign_ids_action.triggered.connect(self.assign_ids)
        toolbar.addAction(self.assign_ids_action)

        self.calculate_spatial_attributes_action = QAction(
            "2. Calculate Spatial Attributes", self
        )
        self.calculate_spatial_attributes_action.triggered.connect(
            self.calculate_spatial_attributes
        )
        toolbar.addAction(self.calculate_spatial_attributes_action)

        self.data_quality_action = QAction("3. Data Quality Checks", self)
        self.data_quality_action.triggered.connect(self.data_quality_checks)
        toolbar.addAction(self.data_quality_action)

        self.update_layer_actions()

    def update_layer_actions(self) -> None:
        has_loaded_features = (
            self.shapefile_manager.loaded_gdf is not None
            and not self.shapefile_manager.loaded_gdf.empty
        )
        self.assign_ids_action.setEnabled(has_loaded_features)
        self.calculate_spatial_attributes_action.setEnabled(has_loaded_features)
        self.data_quality_action.setEnabled(has_loaded_features)
        self.zoom_to_data_button.setEnabled(has_loaded_features)

    # button is repositioned when the app first appears
    # showEvent is triggered after window is shown
    def showEvent(self, event: QShowEvent | None) -> None:
        super().showEvent(event)
        self.zoom_to_data_overlay.schedule_reposition()

    # catches fullscreen/maximize transitions
    # changeEvent is triggered when state/property changes
    def changeEvent(self, event: QEvent | None) -> None:
        super().changeEvent(event)
        if event is not None and event.type() == QEvent.Type.WindowStateChange:
            self.zoom_to_data_overlay.schedule_reposition()

    def load_shapefile(self) -> None:
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Load Shapefile",
            "",
            "Shapefiles (*.shp);;All Files (*)",
        )
        if file_name:
            self.render_shapefile(file_name)

    def render_shapefile(self, file_name: str | PathLike[str]) -> None:
        try:
            has_features = self.shapefile_manager.load_and_render(file_name)
        except Exception as error:
            self.update_layer_actions()
            QMessageBox.critical(
                self, "Load Error", f"Failed to load shapefile:\n{error}"
            )
            return

        if not has_features:
            self.update_layer_actions()
            QMessageBox.information(
                self, "Empty Layer", "The selected shapefile contains no features."
            )
            return

        self.update_layer_actions()

    def show_attribute_table(self) -> None:
        attributes = self.shapefile_manager.get_attributes()
        if attributes is None:
            QMessageBox.information(
                self, "No Layer Loaded", "Please load a shapefile first."
            )
            return

        table_dialog = QDialog(self)
        table_dialog.setWindowTitle("Attribute Table")
        table_dialog.resize(900, 500)

        layout = QVBoxLayout(table_dialog)
        table_widget = QTableWidget(table_dialog)
        layout.addWidget(table_widget)

        table_widget.setRowCount(len(attributes))
        table_widget.setColumnCount(len(attributes.columns))
        table_widget.setHorizontalHeaderLabels([str(col) for col in attributes.columns])

        for row_index, (_, row_data) in enumerate(attributes.iterrows()):
            for col_index, value in enumerate(row_data):
                display_value = "" if value is None else str(value)
                table_widget.setItem(
                    row_index, col_index, QTableWidgetItem(display_value)
                )

        table_widget.resizeColumnsToContents()
        table_dialog.exec()

    def assign_ids(self) -> None:
        assigned_count = self.shapefile_manager.assign_ids()
        if assigned_count is None:
            QMessageBox.information(
                self, "No Layer Loaded", "Please load a shapefile first."
            )
            return

        QMessageBox.information(
            self, "IDs Assigned", f"Assigned BLD IDs to {assigned_count} features."
        )

    def calculate_spatial_attributes(self) -> None:
        updated_count = self.shapefile_manager.calculate_area()
        if updated_count is None:
            QMessageBox.information(
                self, "No Layer Loaded", "Please load a shapefile first."
            )
            return

        self.shapefile_manager.calculate_perimeter()
        self.shapefile_manager.calculate_distance_to_nearest_neighbor()
        self.shapefile_manager.calculate_number_of_neighbors()
        self.shapefile_manager.calculate_centroid_coordinates()
        self.shapefile_manager.calculate_number_of_vertices()

        QMessageBox.information(
            self,
            "Spatial Attributes Calculated",
            (
                "Calculated area, perimeter, nearest neighbour distance, number of "
                "neighbors, centroid coordinates, and number of vertices for "
                f"{updated_count} features."
            ),
        )

    def data_quality_checks(self) -> None:
        if self.shapefile_manager.loaded_gdf is None:
            QMessageBox.information(
                self, "No Layer Loaded", "Please load a shapefile first."
            )
            return

        invalid_result = self.shapefile_manager.detect_invalid_geometry()
        if invalid_result is None:
            QMessageBox.information(
                self, "No Layer Loaded", "Please load a shapefile first."
            )
            return
        invalid_count, total_count = invalid_result

        overlap_result = self.shapefile_manager.detect_overlapping_polygons()
        if overlap_result is None:
            QMessageBox.information(
                self, "No Layer Loaded", "Please load a shapefile first."
            )
            return
        overlap_count, _ = overlap_result

        outlier_result = self.shapefile_manager.detect_spatial_outliers()
        if outlier_result is None:
            QMessageBox.information(
                self, "No Layer Loaded", "Please load a shapefile first."
            )
            return
        outlier_count, _ = outlier_result

        QMessageBox.information(
            self,
            "Data Quality Checks",
            f"Data quality checks complete.\n\n"
            f"  \u2022 Features checked   : {total_count}\n"
            f"  \u2022 Invalid geometries  : {invalid_count}\n"
            f"  \u2022 Overlapping polygons: {overlap_count}\n"
            f"  \u2022 Spatial outliers    : {outlier_count}\n\n"
            f"Columns added to layer:\n"
            f'  - "invalid_geom" (True = invalid geometry)\n'
            f'  - "overlap"      (True = overlaps another polygon)\n'
            f'  - "outlier" (True = no neighbour within threshold distance)',
        )

    def zoom_to_data(self) -> None:
        gdf = self.shapefile_manager.loaded_gdf
        if gdf is None or gdf.empty:
            QMessageBox.information(
                self, "No Layer Loaded", "Please load a shapefile first."
            )
            return

        self.map_renderer.set_plot_range(gdf)

    def export_shapefile(self) -> None:
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Shapefile",
            "",
            "Shapefiles (*.shp);;All Files (*)",
        )

        if not output_path:
            return

        if not output_path.lower().endswith(".shp"):
            output_path = f"{output_path}.shp"

        try:
            exported = self.shapefile_manager.export_shapefile(output_path)
        except Exception as error:
            QMessageBox.critical(
                self, "Export Error", f"Failed to export shapefile:\n{error}"
            )
            return

        if not exported:
            QMessageBox.information(
                self, "No Layer Loaded", "Please load a shapefile first."
            )
            return

        QMessageBox.information(
            self, "Export Complete", f"Shapefile exported to:\n{output_path}"
        )
