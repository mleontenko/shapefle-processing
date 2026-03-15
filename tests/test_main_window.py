import os
import unittest

from PyQt6.QtWidgets import QApplication

from shapefile_processing.ui.main_window import MainWindow


class MainWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.app = QApplication.instance() or QApplication([])

    def test_main_window_renders(self):
        window = MainWindow()
        window.show()
        self.app.processEvents()

        self.assertTrue(window.isVisible())
        self.assertEqual(window.windowTitle(), "Shapefile Processing")
        self.assertIsNotNone(window.centralWidget())

        window.close()


if __name__ == "__main__":
    unittest.main()
