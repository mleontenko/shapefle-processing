"""Main application window for loading, analyzing, and exporting shapefiles."""

from os import PathLike

import pyqtgraph as pg
from PyQt6.QtCore import QEvent
from PyQt6.QtGui import QAction, QShowEvent
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QMainWindow,
    QMessageBox,
)

from shapefile_processing.shapefile_manager import ShapefileManager
from shapefile_processing.ui.attribute_table_dialog import AttributeTableDialog
from shapefile_processing.ui.map_renderer import MapRenderer
from shapefile_processing.ui.parameters_dialog import ParametersDialog
from shapefile_processing.ui.zoom_to_data_button import ZoomToDataButton

pg.setConfigOptions(antialias=True)


class MainWindow(QMainWindow):
    """Top-level GUI window coordinating map display and user actions."""

    def __init__(self) -> None:
        """Initialize widgets, services, and menu/toolbar actions."""
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
        """Create File and View menus with their actions."""
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
        """Create toolbar actions for IDs, spatial attributes, and quality checks."""
        toolbar = self.addToolBar("Tools")
        assert toolbar is not None
        self.parameters_action = QAction("Parameters", self)
        self.parameters_action.triggered.connect(self.open_parameters_dialog)
        toolbar.addAction(self.parameters_action)

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
        """Enable or disable actions based on whether a non-empty layer is loaded."""
        has_loaded_features = (
            self.shapefile_manager.loaded_gdf is not None
            and not self.shapefile_manager.loaded_gdf.empty
        )
        self.parameters_action.setEnabled(has_loaded_features)
        self.assign_ids_action.setEnabled(has_loaded_features)
        self.calculate_spatial_attributes_action.setEnabled(has_loaded_features)
        self.data_quality_action.setEnabled(has_loaded_features)
        self.zoom_to_data_button.setEnabled(has_loaded_features)

    # button is repositioned when the app first appears
    # showEvent is triggered after window is shown
    def showEvent(self, event: QShowEvent | None) -> None:
        """Reposition the zoom button after the window is shown.

        Args:
            event (QShowEvent | None): Qt show event for the window.
        """
        super().showEvent(event)
        self.zoom_to_data_overlay.schedule_reposition()

    # catches fullscreen/maximize transitions
    # changeEvent is triggered when state/property changes
    def changeEvent(self, event: QEvent | None) -> None:
        """Reposition the zoom button when window state changes.

        Args:
            event (QEvent | None): Qt state-change event for the window.
        """
        super().changeEvent(event)
        if event is not None and event.type() == QEvent.Type.WindowStateChange:
            self.zoom_to_data_overlay.schedule_reposition()

    def load_shapefile(self) -> None:
        """Open a file picker and load a selected shapefile.

        Returns:
            None
        """
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Load Shapefile",
            "",
            "Shapefiles (*.shp);;All Files (*)",
        )
        if file_name:
            self.render_shapefile(file_name)

    def open_parameters_dialog(self) -> None:
        """Open dialog to configure the ID prefix used by assign_ids()."""
        dialog = ParametersDialog(
            id_prefix=self.shapefile_manager.id_prefix,
            neighbor_radius=self.shapefile_manager.neighbor_radius,
            outlier_distance_threshold=self.shapefile_manager.outlier_distance_threshold,
            parent=self,
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        prefix, radius, threshold = dialog.get_values()

        self.shapefile_manager.set_id_prefix(prefix)
        self.shapefile_manager.set_neighbor_radius(radius)
        self.shapefile_manager.set_outlier_distance_threshold(threshold)

    def render_shapefile(self, file_name: str | PathLike[str]) -> None:
        """Load and render a shapefile path, showing user feedback on outcomes.

        Args:
            file_name (str | PathLike[str]): Path to the shapefile to render.
        """
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
        """Display loaded attributes in a modal table dialog."""
        attributes = self.shapefile_manager.get_attributes()
        if attributes is None:
            QMessageBox.information(
                self, "No Layer Loaded", "Please load a shapefile first."
            )
            return

        table_dialog = AttributeTableDialog(attributes, parent=self)
        table_dialog.exec()

    def assign_ids(self) -> None:
        """Assign IDs to loaded features and notify the user."""
        assigned_count = self.shapefile_manager.assign_ids()
        if assigned_count is None:
            QMessageBox.information(
                self, "No Layer Loaded", "Please load a shapefile first."
            )
            return

        QMessageBox.information(
            self,
            "IDs Assigned",
            (
                f'Assigned IDs with prefix "{self.shapefile_manager.id_prefix}" '
                f"to {assigned_count} features."
            ),
        )

    def calculate_spatial_attributes(self) -> None:
        """Run spatial metric calculations for the loaded layer and show summary."""
        updated_count = self.shapefile_manager.calculate_area()
        if updated_count is None:
            QMessageBox.information(
                self, "No Layer Loaded", "Please load a shapefile first."
            )
            return

        self.shapefile_manager.calculate_perimeter()
        self.shapefile_manager.calculate_distance_to_nearest_neighbor()
        self.shapefile_manager.calculate_number_of_neighbors(
            radius=self.shapefile_manager.neighbor_radius
        )
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
        """Run data quality checks and show counts for each check."""
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

        outlier_result = self.shapefile_manager.detect_spatial_outliers(
            distance_threshold=self.shapefile_manager.outlier_distance_threshold
        )
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
        """Adjust map view bounds to the extent of loaded features."""
        gdf = self.shapefile_manager.loaded_gdf
        if gdf is None or gdf.empty:
            QMessageBox.information(
                self, "No Layer Loaded", "Please load a shapefile first."
            )
            return

        self.map_renderer.set_plot_range(gdf)

    def export_shapefile(self) -> None:
        """Export the current layer to a user-selected shapefile path."""
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
