"""Dialog widget for displaying shapefile attribute data in a table."""

import pandas as pd
from PyQt6.QtWidgets import (
    QDialog,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class AttributeTableDialog(QDialog):
    """Modal dialog that renders a pandas DataFrame in a Qt table widget."""

    def __init__(self, attributes: pd.DataFrame, parent: QWidget | None = None) -> None:
        """Initialize dialog content from attribute data.

        Args:
            attributes (pd.DataFrame): Table data to display.
            parent (QWidget | None): Optional parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Attribute Table")
        self.resize(900, 500)

        layout = QVBoxLayout(self)
        table_widget = QTableWidget(self)
        layout.addWidget(table_widget)

        table_widget.setRowCount(len(attributes))
        table_widget.setColumnCount(len(attributes.columns))
        table_widget.setHorizontalHeaderLabels([str(col) for col in attributes.columns])

        for row_index, (_, row_data) in enumerate(attributes.iterrows()):
            for col_index, value in enumerate(row_data):
                display_value = "" if value is None else str(value)
                table_widget.setItem(
                    row_index,
                    col_index,
                    QTableWidgetItem(display_value),
                )

        table_widget.resizeColumnsToContents()
